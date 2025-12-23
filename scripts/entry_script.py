import sys
import os

# Add the project root to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import polars as pl
from intelligent_reporting.profiling import *
from scripts.utils import json_fix, strip_code_fence
import logging
import os
import json
import requests
import nbformat as nbf
from dotenv import load_dotenv


load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logging.getLogger(__name__).info("Profiling pipeline started")


df = pl.read_csv("data/BMW-sales-data.csv")
BASE_URL = os.getenv("BASE_URL", "http://178.62.95.124:8000")
RESULTS_DIR = "results"
FIGURES_DIR = "figures"
MAX_ROWS = 100

sampler = DataSampler(df=df, max_rows=MAX_ROWS, sample_dir=RESULTS_DIR)
summarizer = DataSummarizer(df=df, summary_dir=RESULTS_DIR, figures_dir=FIGURES_DIR)
visualizer = DataVisualizer(
    df=df, summary_dir=RESULTS_DIR, figures_dir=FIGURES_DIR, top_k_categories=5
)

file_path = "data/BMW-sales-data.csv"
offline_mode = False

print("[1/5] Sampling & Summarizing data...")
sample_data = sampler.run_sample()
description = summarizer.summary()
schema = {col: str(df.schema[col]) for col in df.columns}

print("Data processed and sampled.")

print("\n[2/5] Calling Metadata Agent...")
metadata_payload = {
    "sample_data": sample_data,
    "schema_info": schema,
    "description": description,
    "offline_mode": offline_mode,
}

try:
    resp = requests.post(f"{BASE_URL}/agents/metadata/run", json=metadata_payload)
    resp.raise_for_status()
    raw_metadata = resp.json()
except Exception as e:
    print(f"Metadata Agent failed: {e}")
    if hasattr(e, "response") and e.response:
        print(e.response.text)
    raise e

metadata_response = json_fix(raw_metadata)
print(metadata_response)
if isinstance(metadata_response, str):
    try:
        metadata_response = json.loads(metadata_response)
    except:
        metadata_response = {"table_description": metadata_response, "columns": []}

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

print("Metadata received.")

print("\n[3/5] Calling Supervisor Agent...")
supervisor_payload = {
    "sample_data": sample_data,
    "description": supervisor_description,
    "offline_mode": offline_mode,
}

try:
    resp = requests.post(f"{BASE_URL}/agents/supervisor/run", json=supervisor_payload)
    resp.raise_for_status()
    raw_supervisor = resp.json()
except Exception as e:
    print(f"Supervisor Agent failed: {e}")
    raise e

parsed_output = json_fix(raw_supervisor)

if isinstance(parsed_output, (list, dict)):
    tasks = (
        parsed_output if isinstance(parsed_output, dict) else {"tasks": parsed_output}
    )
    if isinstance(tasks, list):
        tasks = {"tasks": tasks}
    elif isinstance(tasks, dict) and "tasks" not in tasks:
        tasks = {"tasks": [tasks]}
else:
    tasks = {"tasks": []}

print(parsed_output)
print(f"Supervisor planned {len(tasks.get('tasks', []))} tasks.")

nb = nbf.v4.new_notebook()
cells = []
insights_list = []

sandbox_data_path = "/sandbox/data/" + os.path.basename(file_path)

for i, task in enumerate(tasks.get("tasks", [])):
    print(f"\n[Task {i+1}] {task.get('name', 'Unnamed')}")

    print(" -> Generating code...")
    assistant_payload = {
        "supervisor_response": task,
        "path": sandbox_data_path,
        "offline_mode": offline_mode,
    }
    try:
        resp = requests.post(f"{BASE_URL}/agents/assistant/run", json=assistant_payload)
        resp.raise_for_status()
        assistant_out = resp.json()
    except Exception as e:
        print(f"Assistant failed: {e}")
        continue

    try:
        assistant_json = json_fix(assistant_out)
    except:
        assistant_json = assistant_out

    if isinstance(assistant_json, dict) and "code" in assistant_json:
        raw_code = assistant_json["code"]
    else:
        raw_code = str(assistant_out)

    code = strip_code_fence(raw_code)
    task_name = assistant_json.get("name", f"task_{i}")

    cells.append(nbf.v4.new_markdown_cell(f"## Task: {task_name}"))
    cells.append(nbf.v4.new_code_cell(code))

    print(" -> Executing code in sandbox...")
    sandbox_payload = {
        "code": code,
        "data_dir": "data",
        "image": "llm-sandbox",
        "name": task_name,
    }
    try:
        resp = requests.post(f"{BASE_URL}/sandbox/run", json=sandbox_payload)
        resp.raise_for_status()
        result = resp.json()
    except Exception as e:
        print(f"Sandbox execution failed: {e}")
        if hasattr(e, "response") and e.response:
            print(e.response.text)
        continue

    if result["stdout"].strip():
        cells.append(nbf.v4.new_markdown_cell(f"### Output\n\n{result['stdout']}"))
    if result["stderr"].strip():
        cells.append(nbf.v4.new_markdown_cell(f"### Errors\n\n{result['stderr']}"))

    media_items = result.get("media", [])

    for item in media_items:
        fname = item["filename"]
        content_b64 = item["content"]
        print(f" -> Artifact received: {fname}")

        cells.append(nbf.v4.new_markdown_cell(f"### Artifact: {fname}"))
        img_html = f'<img src="data:image/png;base64,{content_b64}" />'
        cells.append(
            nbf.v4.new_code_cell(
                f"from IPython.display import HTML\nHTML('{img_html}')"
            )
        )

        print(" -> Calling Insights Agent...")
        insights_payload = {
            "img": content_b64,
            "summary_data": {
                "note": "Summary data not fully populated in this flow yet"
            },
            "sample_data": sample_data,
            "description": description,
            "offline_mode": offline_mode,
        }

        try:
            resp = requests.post(
                f"{BASE_URL}/agents/insights/run", json=insights_payload
            )
            resp.raise_for_status()
            insight = resp.json()
            print(" -> Insight received.")

            cells.append(nbf.v4.new_markdown_cell("### Insights"))
            cells.append(nbf.v4.new_markdown_cell(json.dumps(insight, indent=2)))

        except Exception as e:
            print(f"Insights Agent failed: {e}")

nb["cells"] = cells
with open("generated_tasks_remote.ipynb", "w", encoding="utf-8") as f:
    nbf.write(nb, f)
print("\nRemote pipeline completed. Notebook saved to 'generated_tasks_remote.ipynb'.")
