import sys
import os

# Add the project root to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import logging
import json
import requests
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
    schema_info: Dict[str, str]


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


class SupervisorRequest(BaseModel):
    sample_data: Any
    supervisor_description: Any
    offline_mode: bool = False


class SupervisorResponse(BaseModel):
    tasks: List[Dict[str, Any]]


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
            logger.error(f"Data loading failed: {e}")
            raise HTTPException(
                status_code=400, detail=f"Failed to load file: {str(e)}"
            )

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
        schema = {col: str(df.schema[col]) for col in df.columns}

        logger.info("Profiling completed.")
        return ProfileResponse(
            sample_data=sample_data, description=description, schema_info=schema
        )
    except Exception as e:
        logger.error(f"Profiling failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# Agent Imports
from intelligent_reporting.agents.metadata_agent import MetadataAgent
from intelligent_reporting.agents.supervisor_agent import SupervisorAgent
from intelligent_reporting.agents.assistant_agent import AssistantAgent
from intelligent_reporting.agents.insights_agent import InsightsAgent

# Initialize Agents
metadata_agent = MetadataAgent()
supervisor_agent = SupervisorAgent()
assistant_agent = AssistantAgent()
insights_agent = InsightsAgent()


@app.post("/api/metadata", response_model=MetadataResponse)
async def run_metadata(request: MetadataRequest):
    try:
        logger.info("Running Metadata Agent locally...")
        metadata_response = metadata_agent.run(
            sample_data=request.sample_data,
            schema=request.schema_info,
            description=request.description,
            offline_mode=request.offline_mode,
        )

        if isinstance(metadata_response, str):
            try:
                metadata_response = json.loads(metadata_response)
            except:
                metadata_response = {
                    "table_description": metadata_response,
                    "columns": [],
                }

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

        return MetadataResponse(
            metadata_json=metadata_response,
            supervisor_description=supervisor_description,
        )
    except Exception as e:
        logger.error(f"Metadata step failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/supervisor", response_model=SupervisorResponse)
async def run_supervisor(request: SupervisorRequest):
    try:
        logger.info("Running Supervisor Agent locally...")
        parsed_output = supervisor_agent.run(
            sample_data=request.sample_data,
            description=request.supervisor_description,
            offline_mode=request.offline_mode,
        )

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

        return SupervisorResponse(tasks=tasks)

    except Exception as e:
        logger.error(f"Supervisor step failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/execute_task", response_model=ExecuteTaskResponse)
async def execute_task(request: ExecuteTaskRequest):
    try:
        task = request.task

        # 1. Generate Code (Assistant)
        logger.info(f"Generating code for task: {task.get('name', 'Unnamed')}")

        assistant_out = assistant_agent.run(
            supervisor_response=task,
            path=request.sandbox_data_path,
            offline_mode=request.offline_mode,
        )

        raw_code = assistant_out.get("code", "")
        task_name = assistant_out.get("name", task.get("name", "unnamed_task"))

        code = strip_code_fence(raw_code)

        # 2. Execute Code (Sandbox)
        logger.info("Executing code in sandbox...")

        # NOTE: Sandbox remains HTTP for now as per likely Docker architecture
        if not BASE_URL:
            logger.warning("BASE_URL not set for Sandbox, trying http://localhost:8000")

        sandbox_base = BASE_URL if BASE_URL else "http://localhost:8000"
        sandbox_payload = {
            "code": code,
            "data_dir": "data",
            "image": "llm-sandbox",
            "name": task_name,
        }

        resp = requests.post(f"{sandbox_base}/sandbox/run", json=sandbox_payload)
        resp.raise_for_status()
        result = resp.json()

        stderr = result.get("stderr", "")
        stdout = result.get("stdout", "")
        media_items = result.get("media", [])

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
                logger.info("Conditions met. Calling Insights Agent locally...")

                try:
                    insights_data = insights_agent.run(
                        img=content_b64,
                        summary_data={"note": "Summary data not fully populated"},
                        sample_data=request.sample_data,
                        description=request.description,
                        offline_mode=request.offline_mode,
                    )
                    logger.info("Insight received.")
                except Exception as e:
                    logger.warning(f"Insights Agent failed: {e}")

        return ExecuteTaskResponse(
            task_name=task_name,
            code=code,
            stdout=stdout,
            stderr=stderr,
            artifacts=artifacts,
            insights=insights_data,
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
    uvicorn.run(app, host="0.0.0.0", port=8000)
