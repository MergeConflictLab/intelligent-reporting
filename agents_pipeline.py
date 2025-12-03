import json
import os
import glob
import time
import subprocess
from dotenv_vault import load_dotenv

import nbformat as nbf
from intelligent_reporting.agents.metadata_agent import metadata_query
from intelligent_reporting.agents.supervisor_agent import supervisor_query
from intelligent_reporting.agents.assistant_agent import assistant_query
from sandbox.sandbox import run_in_docker_sandbox
from intelligent_reporting.loading.CSVLoader import CSVLoader
from intelligent_reporting.custom_typing.schemaInfererFlatFiles import (
    SchemaInfererFlatFiles,
)
from intelligent_reporting.profiling.DataSampler import DataSampler
from intelligent_reporting.agents.insights_agent import insights_query
from scripts.utils import json_fix, strip_code_fence
from scripts.utils import encode_image


def agents_pipeline(file_path: str) -> list:

    # load_dotenv()

    loader = CSVLoader()
    df = loader.load(file_path=file_path)

    schema_inferer = SchemaInfererFlatFiles()
    df, schema = schema_inferer.infer_schema(df)

    description = schema.get("columns", {})

    # Sample data using DataSampler
    sampler = DataSampler(df=df, max_rows=100, output_path="sample_data.json")
    sample_data = sampler.run_sample()

    raw_response = metadata_query(
        model="deepseek-v3.1:671b-cloud",
        sample_data=sample_data,
        schema=schema,
        description=description,
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

    output = supervisor_query(
        description=supervisor_description,
        model="deepseek-v3.1:671b-cloud",
        sample_data=sample_data,
    )

    parsed_output = json_fix(output)
    with open("output.json", "w", encoding="utf-8") as f:
        if isinstance(parsed_output, (list, dict)):
            json.dump(parsed_output, f, ensure_ascii=False, indent=2)
        else:
            f.write(strip_code_fence(str(output)))

    print("Parsing supervisor output...")
    print(parsed_output)
    if isinstance(parsed_output, (list, dict)):
        tasks = (
            parsed_output
            if isinstance(parsed_output, dict)
            else {"tasks": parsed_output}
        )
        if isinstance(tasks, list):
            tasks = {"tasks": tasks}
        elif isinstance(tasks, dict) and "tasks" not in tasks:
            tasks = {"tasks": [tasks]}
    else:
        try:
            with open("output.json", "r", encoding="utf-8") as f:
                tasks = json.load(f)
        except Exception:
            tasks = {"tasks": []}

    nb = nbf.v4.new_notebook()
    cells = []
    insights = []
    print(f"Found {len(tasks.get('tasks', []))} tasks to execute.")
    for task in tasks.get("tasks", []):
        task_name = task.get("name", "unnamed_task")

        assistant_out = assistant_query(
            model="deepseek-v3.1:671b-cloud",
            supervisor_response=task,
            path=file_path,
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
        task_name = assistant_json.get("name", [])

        print(f"--- RUNNING TASK: {task_name} ---")
        print(code)

        result = run_in_docker_sandbox(name=task_name, code=code)
        print(result)

        cells.append(nbf.v4.new_markdown_cell(f"## Task: {task_name}"))
        cells.append(nbf.v4.new_code_cell(code))

        if result["stdout"].strip():
            cells.append(
                nbf.v4.new_markdown_cell(
                    "### Output\n⁠\n\n" + result["stdout"] + "\n\n\n"
                )
            )
        if result["stderr"].strip():
            cells.append(
                nbf.v4.new_markdown_cell(
                    "### Errors\n⁠\n\n" + result["stderr"] + "\n\n\n"
                )
            )

        for artifact in result["artifacts"]:
            fname = os.path.basename(artifact)
            if fname.lower().endswith((".png", ".jpg")):
                cells.append(nbf.v4.new_markdown_cell(f"### Plot\n![]({artifact})"))
            else:
                with open(artifact, encoding="utf-8") as f:
                    cells.append(
                        nbf.v4.new_markdown_cell(
                            f"### Artifact: {fname}\n⁠\n\n{f.read()}\n\n\n"
                        )
                    )

            print("Generating insight for ", task["name"])
            file_name = os.path.basename(artifact)
            img_path = os.path.join("sandbox/output", file_name)
            encoded_image = encode_image(img_path)

            insight = insights_query(
                img=encoded_image,
                summary_data=response,
                sample_data=sample_data,
                description=task,
                # api_key=os.getenv("API_KEY"),
                # azure_endpoint=os.getenv("AZURE_ENDPOINT"),
            )
            insights.append(insight)

            try:
                ins_text = json.dumps(insight, ensure_ascii=False, indent=2)
            except TypeError:
                ins_text = str(insight)

            cells.append(
                nbf.v4.new_markdown_cell(
                    f"### Insight for {task['name']}\n⁠\n\n{ins_text}\n\n\n"
                )
            )
            time.sleep(5)

    nb["cells"] = cells

    with open("generated_tasks.ipynb", "w", encoding="utf-8") as f:
        nbf.write(nb, f)
    with open("insights.json", "w", encoding="utf-8") as f:
        json.dump(insights, f)

    print("Notebook 'generated_tasks.ipynb' created successfully.")
    return insights


if __name__ == "__main__":
    agents_pipeline(file_path="data/cleaned_salad_data.csv")
