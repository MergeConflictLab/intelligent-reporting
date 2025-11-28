import json
import os
import time
import nbformat as nbf

from intelligent_reporting.agents.metadata_agent import metadata_query
from scripts.script import load_data, get_schema, describe_schema, clean_dataframe
from intelligent_reporting.agents.insight_agent import insights_query
from scripts.utils import strip_code_fence, encode_image


def main():
    # --- LOAD DATA ---
    df = load_data(source="data/cleaned_salad_data.csv")
    df = clean_dataframe(df)
    schema = get_schema(df)
    description = describe_schema(df)

    print("--------------")

    # --- METADATA AGENT ---
    raw_response = metadata_query(
        model="deepseek-v3.1:671b-cloud",
        sample_data=df.head(5).to_dicts(),
        schema=schema,
        description=description,
    )

    response = strip_code_fence(raw_response)
    print(response)
    try:
        metadata = json.loads(response)
    except:
        metadata = {"table_description": response, "columns": []}

    print("==============")

    # --- LOAD SUMMARY.JSON (IMPORTANT FIX) ---
    with open("EDA_output/data_summary.json", "r") as f:
        summary_data = json.load(f)

    figures_dir = "EDA_output/figures"
    insights = []

    # Loop over all plots
    for file_name in os.listdir(figures_dir):

        if not file_name.lower().endswith((".png", ".jpg", ".jpeg")):
            continue

        img_path = os.path.join(figures_dir, file_name)
        encoded_image = encode_image(img_path)

        # --- INSIGHT AGENT ---
        insight = insights_query(
            img=encoded_image,
            summary_data=response,
            sample_data=df.head(5).to_dicts(),
            description=metadata,
        )

        insights.append({
            "figure": file_name,
            "insight": insight
        })

        print("\nInsight generated for:", file_name)
        print(json.dumps(insight, indent=2, ensure_ascii=False))

        time.sleep(3)

    # optional: save final insight json
    with open("EDA_output/insights.json", "w") as f:
        json.dump(insights, f, indent=2, ensure_ascii=False)

    print("\nAll insights generated and saved to EDA/insights.json")


    '''
        raw_response = metadata_query(
        model="deepseek-v3.1:671b-cloud",
        sample_data=df.head(5).to_dicts(),
        schema=schema,
        description=description,
    )
    response = strip_code_fence(raw_response)
    print(response)
    if isinstance(response, str):
        try:
            response = json.loads(response)
        except Exception:
            response = {"table_description": response, "columns": []}'''

    '''# --- SUPERVISOR AGENT ---
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
        sample_data=df.head(5).to_dicts(),
    )

    parsed_output = json_fix(output)
    with open("output.json", "w", encoding="utf-8") as f:
        if isinstance(parsed_output, (list, dict)):
            json.dump(parsed_output, f, ensure_ascii=False, indent=2)
        else:
            f.write(strip_code_fence(str(output)))

    # Load tasks
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

    # --- BUILD NOTEBOOK ---
    nb = nbf.v4.new_notebook()
    cells = []
    insights = []
    print(f"Found {len(tasks.get('tasks', []))} tasks to execute.")
    for task in tasks.get("tasks", []):
        task_name = task.get("name", "unnamed_task")

        # --- ASSISTANT AGENT (returns {"name":..., "code":...}) ---
        assistant_out = assistant_query(
            model="deepseek-v3.1:671b-cloud",
            supervisor_response=task,
            path="data/cleaned_salad_data.csv",
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

        # --- RUN IN SANDBOX ---
        result = run_in_docker_sandbox(name=task_name, code=code)
        print(result)

        # Insert code cell (with title)
        cells.append(nbf.v4.new_markdown_cell(f"## Task: {task_name}"))
        cells.append(nbf.v4.new_code_cell(code))

        # Stdout
        if result["stdout"].strip():
            cells.append(
                nbf.v4.new_markdown_cell("### Output\n⁠  \n" + result["stdout"] + "\n  ⁠")
            )

        # Stderr
        if result["stderr"].strip():
            cells.append(
                nbf.v4.new_markdown_cell("### Errors\n⁠  \n" + result["stderr"] + "\n  ⁠")
            )

        # Artifacts
        for artifact in result["artifacts"]:
            fname = os.path.basename(artifact)
            if fname.lower().endswith((".png", ".jpg")):
                cells.append(nbf.v4.new_markdown_cell(f"### Plot\n![]({artifact})"))
            else:
                with open(artifact, encoding="utf-8") as f:
                    cells.append(
                        nbf.v4.new_markdown_cell(
                            f"### Artifact: {fname}\n⁠  \n{f.read()}\n  ⁠"
                        )
                    )

            # --- SUPERVISOR INSIGHTS ---
            print("Generating insight for ", task["name"])
            file_name = os.path.basename(artifact)
            img_path = os.path.join("sandbox/output", file_name)
            encoded_image = encode_image(img_path)

            insight = insights_query(
                img=encoded_image,
                summary_data=response,
                sample_data=df.head(5).to_dicts(),
                description=task,
            )
            insights.append(insight)
            # Render insight as pretty JSON in the notebook cell
            try:
                ins_text = json.dumps(insight, ensure_ascii=False, indent=2)
            except TypeError:
                ins_text = str(insight)

            cells.append(
                nbf.v4.new_markdown_cell(
                    f"### Insight for {task['name']}\n⁠  \n{ins_text}\n  ⁠"
                )
            )
            time.sleep(5)

    # Finalize notebook
    nb["cells"] = cells

    with open("generated_tasks.ipynb", "w", encoding="utf-8") as f:
        nbf.write(nb, f)
    with open("insights.json", "w", encoding="utf-8") as f:
        json.dump(insights, f)

    print("Notebook 'generated_tasks.ipynb' created successfully.")
'''

if __name__ == "__main__":
    main()
