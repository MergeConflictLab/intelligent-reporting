# Agents

This folder contains the core agent modules for the Intelligent Reporting system. Each agent has a specific responsibility, from metadata extraction to high-level orchestration. They are designed to be modular, testable, and composable.

## 1. Metadata Agent (`metadata_agent.py`)

**Role:** Analyzes the structure of the dataset.

**Key Function:** `metadata_query(model, sample_data, schema, description)`

**Inputs:**
- `model`: Name of the LLM to use.
- `sample_data`: A list of dictionaries representing sample rows.
- `schema`: Dictionary mapping column names to data types.
- `description`: A list of column descriptions/details.

**Outputs:**
- A JSON string containing:
    - `table_description`: A summary of the table.
    - `columns`: A list of objects with `name` and `description` for each column.

## 2. Supervisor Agent (`supervisor_agent.py`)

**Role:** The strategist. It analyzes the metadata and data samples to formulate an analysis plan.

**Key Function:** `supervisor_query(model, sample_data, description)`

**Inputs:**
- `model`: Name of the LLM.
- `sample_data`: Sample rows from the dataset.
- `description`: Metadata description of the dataset (output from Metadata Agent).

**Outputs:**
- A JSON string defining the plan:
    - `libraries`: List of Python libraries to use.
    - `tasks`: A list of analysis tasks, where each task has:
        - `name`: Short title.
        - `description`: Goal of the analysis.
        - `columns`: Columns involved.
        - `plot_type`: Recommended visualization type.
        - `preprocessing`: Necessary data cleaning steps.
        - `code_template`: Pseudo-code guide for the Assistant Agent.

## 3. Assistant Agent (`assistant_agent.py`)

**Role:** The coder. It takes a specific task from the Supervisor's plan and generates executable Python code.

**Key Function:** `assistant_query(supervisor_response, path, model="mistral")`

**Inputs:**
- `supervisor_response`: The specific task object from the Supervisor's plan.
- `path`: Path to the dataset file.
- `model`: Name of the LLM (default: "mistral").

**Outputs:**
- A dictionary:
    - `name`: The task name.
    - `code`: The executable Python code to perform the analysis and save the plot.

## 4. Insights Agent (`insights_agent.py`)

**Role:** The analyst. It looks at the generated charts and data summaries to produce textual insights.

**Key Function:** `insights_query(img, summary_data, sample_data, description)`

**Inputs:**
- `img`: Base64 encoded string of the generated plot image.
- `summary_data`: Statistical summary of the data (e.g., `df.describe()`).
- `sample_data`: Sample rows.
- `description`: High-level description of the analysis task.

**Outputs:**
- A JSON array of insight objects:
    - `insight`: The key finding.
    - `reasoning`: Why this is important.
    - `evidence`: Data points or visual features supporting the finding.
