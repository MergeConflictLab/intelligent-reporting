# Agents

This folder contains the core agent modules that will be integrated with the automated EDA

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


## 2. Insights Agent (`insights_agent.py`)

**Role:** The analyst. It looks at the generated charts and data summaries to produce textual insights.

**Key Function:** `insights_query(img, summary_data, sample_data, description)`

**Inputs:**
- `img`: Base64 encoded string of the generated plot image.
- `summary_data`: statistical mesures that came from the manual EDA.
- `sample_data`: Sample rows using sampling techniques.
- `description`: High-level description table and columns.

**Outputs:**
- A JSON array of insight objects:
    - `insight`: The key finding.
    - `reasoning`: Why this is important.
    - `evidence`: Data points or visual features supporting the finding.