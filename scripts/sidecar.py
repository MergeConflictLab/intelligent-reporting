import sys
import os

# Add the project root to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import logging
import json
import requests
import httpx  # Async HTTP client
import uvicorn
import polars as pl
from fastapi import FastAPI, HTTPException, Body, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
import shutil

from intelligent_reporting.profiling import DataSampler, DataSummarizer, DataVisualizer
from scripts.utils import json_fix, strip_code_fence
from intelligent_reporting.orchestrator.selector import Selector
from intelligent_reporting.custom_typing.schemaInfererFlatFiles import (
    SchemaInfererFlatFiles,
)
import intelligent_reporting.connectors

# Load environment variables
load_dotenv()
BASE_URL = os.getenv("BASE_URL")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="Intelligent Reporting Sidecar")

# CORS Configuration
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Constants
RESULTS_DIR = "results"
FIGURES_DIR = "figures"
DATA_DIR = "data"
# Ensure directories exist
os.makedirs(RESULTS_DIR, exist_ok=True)
os.makedirs(FIGURES_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)


# Pydantic Models
class UploadResponse(BaseModel):
    file_path: str
    message: str


class ProfileRequest(BaseModel):
    file_path: str
    max_rows: int = 250


class ProfileResponse(BaseModel):
    sample_data: Any
    description: Any
    schema_info: Dict[str, Any]


class ExecuteTaskRequest(BaseModel):
    task: Dict[str, Any]
    sandbox_data_path: str
    offline_mode: bool = False
    sample_data: Optional[Any] = None
    description: Optional[Any] = None
    schema_info: Optional[Dict[str, str]] = None


class ExecuteTaskResponse(BaseModel):
    task_name: str
    code: str
    stdout: str
    stderr: str
    artifacts: List[Dict[str, str]]  # List of {filename, content_base64}
    insights: Optional[Dict[str, Any]] = None


@app.post("/api/upload", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...)):
    try:
        file_location = os.path.join(DATA_DIR, file.filename)
        with open(file_location, "wb+") as buffer:
            shutil.copyfileobj(file.file, buffer)
        logger.info(f"File saved to {file_location}")
        return UploadResponse(
            file_path=file_location, message="File uploaded successfully"
        )
    except Exception as e:
        logger.error(f"Upload failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


class MetadataRequest(BaseModel):
    sample_data: Any
    description: Any
    schema_info: Dict[str, str]
    offline_mode: bool = False


class MetadataResponse(BaseModel):
    metadata_json: Any
    supervisor_description: Any
    usage: Optional[Dict[str, int]] = None


class SupervisorRequest(BaseModel):
    sample_data: Any
    supervisor_description: Any
    offline_mode: bool = False


class SupervisorResponse(BaseModel):
    tasks: List[Dict[str, Any]]
    usage: Optional[Dict[str, int]] = None


class ExecuteTaskRequest(BaseModel):
    task: Dict[str, Any]
    sandbox_data_path: str
    offline_mode: bool = False
    sample_data: Optional[Any] = None
    description: Optional[Any] = None
    schema_info: Optional[Dict[str, str]] = None


class ExecuteTaskResponse(BaseModel):
    task_name: str
    code: str
    stdout: str
    stderr: str
    artifacts: List[Dict[str, str]]  # List of {filename, content_base64}
    insights: Optional[Dict[str, Any]] = None
    usage: Optional[Dict[str, int]] = None


@app.post("/api/profile", response_model=ProfileResponse)
async def profile_data(request: ProfileRequest):
    try:
        logger.info(f"Profiling data from: {request.file_path}")
        if not os.path.exists(request.file_path):
            raise HTTPException(
                status_code=404, detail=f"File not found: {request.file_path}"
            )

        # Use Selector for format-agnostic loading
        try:
            selector = Selector(file=request.file_path)
            df = selector.get_data()
        except Exception as e:
            raise HTTPException(
                status_code=400, detail=f"Failed to load file: {str(e)}"
            )

        # Infer schema and clean data
        try:
            inferer = SchemaInfererFlatFiles()
            df, rich_schema = inferer.infer_schema(df, schema_dir=RESULTS_DIR)
            logger.info("Schema inference and data cleaning completed.")
        except Exception as e:
            logger.error(f"Schema inference failed: {e}")
            # Fallback to original df if inference fails, though ideal is to fail hard or warn
            rich_schema = {col: str(df.schema[col]) for col in df.columns}

        # Consistent setup with entry_script.py
        effective_max_rows = request.max_rows
        if df.height < request.max_rows:
            logger.info(
                f"Dataset has fewer rows ({df.height}) than requested max_rows ({request.max_rows}). Using {df.height} rows."
            )
            effective_max_rows = df.height

        sampler = DataSampler(
            df=df, max_rows=effective_max_rows, sample_dir=RESULTS_DIR
        )

        # summarizer = DataSummarizer(df=df, summary_dir=RESULTS_DIR, figures_dir=FIGURES_DIR)
        summarizer = DataSummarizer(
            df=df, summary_dir=RESULTS_DIR, figures_dir=FIGURES_DIR
        )

        # visualizer = DataVisualizer(
        #    df=df, summary_dir=RESULTS_DIR, figures_dir=FIGURES_DIR, top_k_categories=5
        # )
        visualizer = DataVisualizer(
            df=df, summary_dir=RESULTS_DIR, figures_dir=FIGURES_DIR, top_k_categories=5
        )

        sample_data = sampler.run_sample()
        description = summarizer.summary()
        # schema = {col: str(df.schema[col]) for col in df.columns} # Replaced by rich_schema

        # Flatten rich schema for frontend compatibility while keeping accuracy
        # rich_schema['columns'] is {col: {inferred_type: ..., ...}}
        schema_info = {
            col: details["inferred_type"]
            for col, details in rich_schema["columns"].items()
        }

        logger.info(
            f"Profiling completed. Schema Info: {json.dumps(schema_info, indent=2)}"
        )
        return ProfileResponse(
            sample_data=sample_data, description=description, schema_info=schema_info
        )
    except Exception as e:
        logger.error(f"Profiling failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# Agent Imports Removed - Sidecar is now a strict proxy
# from intelligent_reporting.agents.metadata_agent import MetadataAgent
# from intelligent_reporting.agents.supervisor_agent import SupervisorAgent
# from intelligent_reporting.agents.assistant_agent import AssistantAgent
# from intelligent_reporting.agents.insights_agent import InsightsAgent

# Initialize Agents Removed
# metadata_agent = MetadataAgent()
# supervisor_agent = SupervisorAgent()
# assistant_agent = AssistantAgent()
# insights_agent = InsightsAgent()

# Determine Backend URL
# User requested "through base_url". We prefer BASE_URL, then REMOTE_BACKEND_URL, then localhost default.
effective_backend_url = os.getenv("BASE_URL")
if not effective_backend_url:
    effective_backend_url = os.getenv("REMOTE_BACKEND_URL")
if not effective_backend_url:
    effective_backend_url = "http://localhost:8000"

logger.info(f"Sidecar configured to proxy to Backend at: {effective_backend_url}")


# Helper for proxying
async def proxy_request(url: str, json_body: dict):
    # Use httpx for async requests
    async with httpx.AsyncClient(
        timeout=120.0
    ) as client:  # Generous timeout for agents
        try:
            resp = await client.post(url, json=json_body)
            # Forward status code and content
            if resp.status_code >= 400:
                raise HTTPException(status_code=resp.status_code, detail=resp.text)
            return resp.json()
        except httpx.RequestError as e:
            logger.error(f"Proxy request failed to {url}: {e}")
            raise HTTPException(status_code=502, detail=f"Proxy Error: {str(e)}")


REMOTE_BACKEND_URL = os.getenv("REMOTE_BACKEND_URL")


@app.post("/api/metadata", response_model=MetadataResponse)
async def run_metadata(request: MetadataRequest):
    logger.info(f"Proxying Metadata request to {effective_backend_url}")
    # Map Sidecar MetadataRequest to Backend MetadataInput
    payload = request.dict()
    url = f"{effective_backend_url}/agents/metadata/run"
    raw_response = await proxy_request(url, payload)

    # ADAPTER: Transform raw backend response to Sidecar's MetadataResponse
    # Backend returns plain dict/json. Sidecar needs MetadataResponse.
    metadata_response = raw_response

    # Handle supervisor_description extraction logic (from legacy local agent)
    if (
        isinstance(metadata_response, dict)
        and "columns" in metadata_response
        and isinstance(metadata_response["columns"], list)
    ):
        supervisor_description = metadata_response["columns"]
    elif isinstance(metadata_response, list):
        supervisor_description = metadata_response
    else:
        supervisor_description = [metadata_response]

    usage = None
    if isinstance(metadata_response, dict):
        usage = metadata_response.pop("_usage", None)

    return MetadataResponse(
        metadata_json=metadata_response,
        supervisor_description=supervisor_description,
        usage=usage,
    )


@app.post("/api/supervisor", response_model=SupervisorResponse)
async def run_supervisor(request: SupervisorRequest):
    logger.info(f"Proxying Supervisor request to {effective_backend_url}")
    # Map Sidecar SupervisorRequest to Backend SupervisorInput
    # Sidecar: sample_data, supervisor_description, offline_mode
    # Backend: sample_data, description, offline_mode.
    payload = {
        "sample_data": request.sample_data,
        "description": request.supervisor_description,
        "offline_mode": request.offline_mode,
    }
    url = f"{effective_backend_url}/agents/supervisor/run"
    parsed_output = await proxy_request(url, payload)

    # ADAPTER: Transform raw backend response to Sidecar's SupervisorResponse
    tasks_wrapper = {}
    if isinstance(parsed_output, (list, dict)):
        tasks_wrapper = (
            parsed_output
            if isinstance(parsed_output, dict)
            else {"tasks": parsed_output}
        )
        if isinstance(tasks_wrapper, list):
            tasks_wrapper = {"tasks": tasks_wrapper}
        elif isinstance(tasks_wrapper, dict) and "tasks" not in tasks_wrapper:
            tasks_wrapper = {"tasks": [tasks_wrapper]}
    else:
        tasks_wrapper = {"tasks": []}

    tasks = tasks_wrapper.get("tasks", [])
    logger.info(f"Supervisor planned {len(tasks)} tasks.")

    usage = None
    if isinstance(parsed_output, dict):
        usage = parsed_output.get("_usage")

    return SupervisorResponse(tasks=tasks, usage=usage)


@app.post("/api/execute_task", response_model=ExecuteTaskResponse)
async def execute_task(request: ExecuteTaskRequest):
    try:
        task = request.task

        # 1. Generate Code (Assistant)
        logger.info(f"Generating code for task: {task.get('name', 'Unnamed')}")

        if True:  # Force block for proxy
            logger.info(f"Proxying Assistant request to {effective_backend_url}")
            asst_payload = {
                "supervisor_response": task,
                "path": request.sandbox_data_path,
                "offline_mode": request.offline_mode,
            }
            assistant_out = await proxy_request(
                f"{effective_backend_url}/agents/assistant/run", asst_payload
            )

        raw_code = assistant_out.get("code", "")
        task_name = assistant_out.get("name", task.get("name", "unnamed_task"))

        code = strip_code_fence(raw_code)

        # 2. Execute Code (Sandbox)
        logger.info("Executing code in sandbox...")

        # 2. Execute Code (Sandbox) - Strictly Remote
        logger.info("Executing code in sandbox...")

        # Extract filename logic
        data_filename = os.path.basename(request.sandbox_data_path)

        sandbox_payload = {
            "code": code,
            "data_dir": "data",
            "image": "llm-sandbox",
            "name": task_name,
            "sample_data": request.sample_data,  # Data transfer
            "filename": data_filename,
        }

        # Use httpx for async consistency (previously used blocking requests)
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{effective_backend_url}/sandbox/run", json=sandbox_payload
            )

        if resp.status_code >= 400:
            # Manually raise for status since httpx doesn't have quite the same API as requests in all versions,
            # but raise_for_status() exists on response object in recent versions
            resp.raise_for_status()

        result = resp.json()

        stderr = result.get("stderr", "")
        stdout = result.get("stdout", "")
        media_items = result.get("media", [])

        logger.info(f"Sandbox STDOUT: {stdout}")
        logger.info(f"Sandbox STDERR: {stderr}")

        artifacts = []
        insights_data = None

        # 3. Process Artifacts & Get Insights
        logger.info(f"Sandbox returned {len(media_items)} media items.")

        for item in media_items:
            fname = item["filename"]
            content_b64 = item["content"]
            artifacts.append({"filename": fname, "content_base64": content_b64})

            # If we have context data, try to get insights for the first artifact
            if request.sample_data and request.description and not insights_data:
                logger.info("Conditions met. Proxying Insights request...")

                ins_payload = {
                    "img": content_b64,
                    "summary_data": {"note": "Summary data not fully populated"},
                    "sample_data": request.sample_data,
                    "description": request.description,
                    "offline_mode": request.offline_mode,
                }
                try:
                    insights_data = await proxy_request(
                        f"{effective_backend_url}/agents/insights/run", ins_payload
                    )
                    logger.info("Remote Insight received.")
                except Exception as e:
                    logger.warning(f"Remote Insights Agent failed: {e}")

        # Extract usage
        usage = assistant_out.get("_usage", {})

        return ExecuteTaskResponse(
            task_name=task_name,
            code=code,
            stdout=stdout,
            stderr=stderr,
            artifacts=artifacts,
            insights=insights_data,
            usage=usage,
        )

    except Exception as e:
        logger.error(f"Task execution failed: {str(e)}", exc_info=True)
        detail = str(e)
        if hasattr(e, "response") and e.response:
            detail += f" | Remote Response: {e.response.text}"
        raise HTTPException(status_code=500, detail=detail)


# Validations for PDF generation
from fpdf import FPDF
import base64
import tempfile


class PDFReport(FPDF):
    def header(self):
        self.set_font("Arial", "B", 15)
        self.cell(0, 10, "Intelligent Reporting Pipeline", 0, 1, "C")
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.cell(0, 10, f"Page {self.page_no()}", 0, 0, "C")


class GeneratePDFRequest(BaseModel):
    profile_summary: Dict[str, Any]
    schema_info: Dict[str, str]
    tasks: List[Dict[str, Any]]


@app.post("/api/generate_pdf")
async def generate_pdf(request: GeneratePDFRequest):
    pdf = PDFReport()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    # 1. Profile Summary
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "1. Data Profile Summary", 0, 1)
    pdf.set_font("Arial", size=10)

    # Check if profile_summary is flat or nested
    # The frontend sends 'description' which is the summary dict
    if isinstance(request.profile_summary, dict):
        for k, v in request.profile_summary.items():
            pdf.cell(0, 8, f"{k}: {v}", 0, 1)
    else:
        pdf.multi_cell(0, 8, str(request.profile_summary))
    pdf.ln(5)

    # 2. Schema Info
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "2. Schema Information", 0, 1)
    pdf.set_font("Arial", size=10)

    for col, dtype in request.schema_info.items():
        pdf.cell(0, 8, f"- {col}: {dtype}", 0, 1)
    pdf.ln(5)

    # 3. Tasks & Insights
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "3. Analysis Tasks & Insights", 0, 1)
    pdf.ln(2)

    for i, task in enumerate(request.tasks):
        task_name = task.get("task_name", f"Task {i+1}")
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, f"Task {i+1}: {task_name}", 0, 1)

        # Insights
        if task.get("insights"):
            pdf.set_font("Arial", "I", 10)
            pdf.multi_cell(0, 8, f"Insight: {task.get('insights')}")
            pdf.ln(2)

        # Artifacts (Images)
        if task.get("artifacts"):
            for artifact in task["artifacts"]:
                try:
                    # decode base64
                    img_data = base64.b64decode(artifact["content_base64"])
                    with tempfile.NamedTemporaryFile(
                        suffix=".png", delete=False
                    ) as tmp:
                        tmp.write(img_data)
                        tmp_path = tmp.name

                    # Add image to PDF
                    # Ensure it fits on page; max width approx 190
                    pdf.image(tmp_path, w=150)
                    pdf.ln(5)
                    os.unlink(tmp_path)
                except Exception as e:
                    logger.error(f"Failed to add image for task {task_name}: {e}")
                    pdf.cell(0, 8, "[Error loading image]", 0, 1)

        pdf.ln(5)

    # Save to temp file and return
    import uuid

    out_filename = f"report_{uuid.uuid4()}.pdf"
    out_path = os.path.join(RESULTS_DIR, out_filename)
    pdf.output(out_path)

    from fastapi.responses import FileResponse

    return FileResponse(
        out_path, filename="analysis_report.pdf", media_type="application/pdf"
    )


@app.get("/health")
async def health_check():
    return {"status": "ok", "routes": [r.path for r in app.routes]}


if __name__ == "__main__":
    # Print all registered routes for debugging
    for route in app.routes:
        print(f"Registered route: {route.path} [{route.methods}]")

    # Use app object directly to avoid import issues
    uvicorn.run(app, host="0.0.0.0", port=8001)
