import json
import os
import time

import nbformat as nbf
from dotenv_vault import load_dotenv

from intelligent_reporting.agents.agent_factory import AgentFactory, AgentType
from intelligent_reporting.custom_typing.schemaInfererFlatFiles import (
    SchemaInfererFlatFiles,
)
from intelligent_reporting.orchestrator.data_pipeline_selector import (
    DataPipelineSelector,
)
from intelligent_reporting.profiling.DataSampler import DataSampler
from sandbox.sandbox import run_in_docker_sandbox
from scripts.utils import encode_image, json_fix, strip_code_fence


def process_task(task, file_path, data_dir, response, sample_data, offline_mode):
    """
    Process a single task: Generate code, run in sandbox, generate insights.
    Returns a dictionary with 'cells' (notebook cells) and 'insight' (insight dict).
    """
    task_name = task.get("name", "unnamed_task")
    sandbox_path = "/sandbox/data/" + os.path.basename(file_path)

    local_cells = []
    local_insight = None

    # 1. Generate Code (Assistant Agent)
    assistant_agent = AgentFactory.get_agent(AgentType.ASSISTANT)
    assistant_out = assistant_agent.run(
        supervisor_response=task,
        path=sandbox_path,
        offline_mode=offline_mode,
    )

    try:
        assistant_json = json_fix(assistant_out)
    except Exception:
        assistant_json = assistant_out

    if isinstance(assistant_json, dict) and "code" in assistant_json:
        raw_code = assistant_json["code"]
    else:
        raw_code = assistant_out  # fallback

    code = strip_code_fence(raw_code)
    # Update task name if assistant provided a better one
    task_name = (
        assistant_json.get("name", task_name)
        if isinstance(assistant_json, dict)
        else task_name
    )

    local_cells.append(nbf.v4.new_markdown_cell(f"## Task: {task_name}"))
    local_cells.append(nbf.v4.new_code_cell(code))

    result = run_in_docker_sandbox(code=code, data_dir=data_dir, name=task_name)

    if result["stdout"].strip():
        local_cells.append(
            nbf.v4.new_markdown_cell("### Output\n\n" + result["stdout"] + "\n\n")
        )
    if result["stderr"].strip():
        local_cells.append(
            nbf.v4.new_markdown_cell("### Errors\n\n" + result["stderr"] + "\n\n")
        )

    # 3. Generate Insights (Insights Agent)
    for artifact in result["artifacts"]:
        fname = os.path.basename(artifact)
        if fname.lower().endswith((".png", ".jpg")):
            rel_path = os.path.relpath(artifact, os.getcwd())
            local_cells.append(nbf.v4.new_markdown_cell(f"### Plot\n![]({rel_path})"))
        else:
            with open(artifact, encoding="utf-8") as f:
                local_cells.append(
                    nbf.v4.new_markdown_cell(f"### Artifact: {fname}\n\n{f.read()}\n\n")
                )

        img_path = os.path.join("sandbox/output", fname)
        encoded_image = encode_image(img_path)

        try:
            insights_agent = AgentFactory.get_agent(AgentType.INSIGHTS)
            insight = insights_agent.run(
                img=encoded_image,
                summary_data=response,
                sample_data=sample_data,
                description=task,
                offline_mode=offline_mode,
            )
            local_insight = insight

            try:
                ins_text = json.dumps(insight, ensure_ascii=False, indent=2)
            except TypeError:
                ins_text = str(insight)

            local_cells.append(
                nbf.v4.new_markdown_cell(
                    f"### Insight for {task_name}\n\n{ins_text}\n\n"
                )
            )
        except Exception as e:
            print(f"Failed to generate insight for {task_name}: {e}")
            local_cells.append(
                nbf.v4.new_markdown_cell(
                    f"### Insight for {task_name} (FAILED)\n\nError: {e}\n\n"
                )
            )
            local_insight = {"error": str(e)}

    return {"cells": local_cells, "insight": local_insight}


def agents_pipeline(file_path: str, offline_mode: bool = False) -> list:
    load_dotenv()
    # Extract data directory for sandbox mounting
    data_dir = os.path.dirname(file_path) if os.path.dirname(file_path) else "data"

    loader = DataPipelineSelector(file=file_path).select_loader_inferer()[0]()
    df = loader.load(file_path)

    schema_inferer = SchemaInfererFlatFiles()
    df, schema = schema_inferer.infer_schema(df)

    description = schema.get("columns", {})

    # Sample data using DataSampler
    sampler = DataSampler(df=df, max_rows=200, output_path="sample_data.json")
    sample_data = sampler.run_sample()

    metadata_agent = AgentFactory.get_agent(AgentType.METADATA)
    raw_response = metadata_agent.run(
        sample_data=sample_data,
        schema=schema,
        description=description,
        offline_mode=offline_mode,
    )

    response = json_fix(raw_response)
    if isinstance(response, str):
        try:
            response = json.loads(response)
        except Exception:
            response = {"table_description": response, "columns": []}

    if (
        isinstance(response, dict)
        and "columns" in response
        and isinstance(response["columns"], list)
    ):
        supervisor_description = response["columns"]
    elif isinstance(response, list):
        supervisor_description = response
    else:
        supervisor_description = [response]

    supervisor_agent = AgentFactory.get_agent(AgentType.SUPERVISOR)
    output = supervisor_agent.run(
        description=supervisor_description,
        sample_data=sample_data,
        offline_mode=offline_mode,
    )

    parsed_output = output

    with open("output.json", "w", encoding="utf-8") as f:
        if isinstance(parsed_output, (list, dict)):
            json.dump(parsed_output, f, ensure_ascii=False, indent=2)
        else:
            f.write(strip_code_fence(str(output)))

    if isinstance(parsed_output, dict):
        tasks_list = parsed_output.get("tasks", [])
    elif isinstance(parsed_output, list):
        tasks_list = parsed_output
    else:
        tasks_list = []

    print(f"Found {len(tasks_list)} tasks to execute.")

    nb = nbf.v4.new_notebook()
    all_cells = []
    all_insights = []

    # Sequential Execution
    print("Starting sequential execution of tasks...")

    for task in tasks_list:
        try:
            result = process_task(
                task,
                file_path,
                data_dir,
                response,
                sample_data,
                offline_mode,
            )
            all_cells.extend(result["cells"])
            if result["insight"]:
                all_insights.append(result["insight"])
            print(f"Task '{task.get('name')}' completed successfully.")
        except Exception as exc:
            task_name = task.get("name", "unknown")
            print(f"Task '{task_name}' generated an exception: {exc}")
            all_cells.append(
                nbf.v4.new_markdown_cell(
                    f"## Task: {task_name} (FAILED)\n\nError: {exc}"
                )
            )

    nb["cells"] = all_cells

    with open("generated_tasks.ipynb", "w", encoding="utf-8") as f:
        nbf.write(nb, f)
    with open("insights.json", "w", encoding="utf-8") as f:
        json.dump(all_insights, f)

    print("Notebook 'generated_tasks.ipynb' created successfully.")
    return all_insights


if __name__ == "__main__":
    # Time the pipeline
    start_time = time.time()
    insights = agents_pipeline(
        file_path="data/cleaned_salad_data.csv", offline_mode=True
    )
    end_time = time.time()
    print(f"Pipeline execution time: {end_time - start_time:.2f} seconds")
    print(insights)
