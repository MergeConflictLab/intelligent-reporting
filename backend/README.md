# Agents

This folder contains the core agent modules for the Intelligent Reporting system. Each agent is a focused, testable component used to analyze data or orchestrate analysis workflows. Typical responsibilities include metadata extraction, plan generation, code generation, and insight summarization.

## Run

```bash
docker build -t llm-fastapi .
docker run -d --network=host \
  --memory=15g \
  --shm-size=16g \
  -e HOST_WORKDIR=$(pwd) \
  -e OLLAMA_HOST=http://localhost:11434 \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v /usr/bin/docker:/usr/bin/docker:ro \
  -v $(pwd)/models:/app/models \
  -v $(pwd)/sandbox/code:/app/sandbox/code \
  -v $(pwd)/sandbox/output:/app/sandbox/output \
  -v $(pwd)/sandbox/data:/app/sandbox/data \
  llm-fastapi
```

The API will be available at `http://0.0.0.0:8000`.

## Files in this folder

- `metadata_agent.py` — Extracts structural metadata from datasets.
- `supervisor_agent.py` — Creates an analysis plan from metadata and samples.
- `assistant_agent.py` — Generates executable code for a specific analysis task.
- `insights_agent.py` — Produces textual insights from charts and summaries.

## Brief agent summaries

## Metadata Agent (`metadata_agent.py`)

**Role**: Analyze dataset structure and produce a machine-readable description.

**Key function**: `metadata_query(model, sample_data, schema, description)`

**Inputs**:

- `model`: LLM identifier used for any text-generation steps.
- `sample_data`: `List[dict]`, a small sample of rows.
- `schema`: `dict` mapping column names to inferred types.
- `description`: Optional human-provided column descriptions.

**Outputs**:

- `dict` containing:
  - `table_description`: short natural-language summary.
  - `columns`: list of `{name, description}` entries.

## Supervisor Agent (`supervisor_agent.py`)

**Role**: Produce a prioritized analysis plan from metadata and data samples.

**Key function**: `supervisor_query(model, sample_data, description)`

**Inputs**:

- `model`: LLM name.
- `sample_data`: small list of rows.
- `description`: metadata output from the Metadata Agent.

**Outputs**:

- `dict` describing the plan, typically including:
  - `libraries`: list of Python libraries to use (e.g., `pandas`, `polars`).
  - `tasks`: list of task objects; each task commonly contains:
    - `name`: short task title.
    - `description`: intent or hypothesis to evaluate.
    - `columns`: columns involved.
    - `plot_type`: suggested visualization type.
    - `preprocessing`: brief cleaning steps required.
    - `code_template`: pseudo-code or template the Assistant can expand.

## Assistant Agent (`assistant_agent.py`)

**Role**: Turn a single Supervisor task into executable Python code.

**Key function**: `assistant_query(supervisor_response, path, model="mistral")`

**Inputs**:

- `supervisor_response`: one task object from the Supervisor plan.
- `path`: path to dataset file to run against.
- `model`: LLM identifier (default: `mistral`).

**Outputs**:

- `dict` with keys such as:
  - `name`: task name.
  - `code`: executable Python code (string) that performs the analysis and
    writes any plot files or outputs.

## Insights Agent (`insights_agent.py`)

**Role**: Produce human-readable insights from generated plots and summaries.

**Key function**: `insights_query(img, summary_data, sample_data, description)`

**Inputs**:

- `img`: base64 or path to plot image.
- `summary_data`: statistical summaries (e.g., result of `df.describe()`).
- `sample_data`: small sample rows used for context.
- `description`: high-level description of the analysis performed.

**Outputs**:

- `list` of insight objects with fields like:
  - `insight`: brief finding.
  - `reasoning`: explanation why the finding matters.
  - `evidence`: supporting data points or visual cues.

## Notes & development

Agent responsibilities differ depending on the reporting mode. Automated EDA uses only the Metadata Agent and Insights Agent to generate a fully automated exploratory report. The Fully AI Reporting mode uses the entire agent stack — Metadata, Supervisor, Assistant, and Insights Agents — to produce an end-to-end analysis with planning, code generation, execution, visualization, and insight generation.
