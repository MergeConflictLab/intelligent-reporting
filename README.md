# AI-Driven Automated Report Generation System

## Overview

This system uses Large Language Models (LLMs) and multi-agent orchestration to automatically transform raw datasets into structured, interpretable reports. It combines metadata analysis, visualization generation, and natural-language summarization to deliver daily or weekly data insights with minimal human intervention.

## System Architecture
### Data Layer
- Handles all data ingestion, validation, and profiling.
- Inputs: CSV, Parquet, SQL, or API-based sources.
- Processes: Cleansing, sampling, and profiling (via tools like pandas-profiling or ydata-profiling).
- Outputs: A structured dataset and its metadata (schema, types, null counts, distributions).
- Storage: Metadata and profiling results stored in SQLite or a lightweight local database.

### Agent Layer

- A collaborative AI layer composed of specialized agents that sequentially process and interpret data.
- Metadata Agent
  - Generates a dataset overview and column-level metadata.
  - Outputs structured JSON or Markdown describing data structure, types, and notable features.
  - Enables downstream agents to “understand” the dataset before analysis.

- Supervisor Agent (Reader)
  - Reads metadata and dataset samples to identify patterns, anomalies, and analytical opportunities.
  - Defines analysis goals and visualization ideas.
  - Creates a task plan for the Assistant Agent, specifying what plots or analyses to perform.

- Assistant Agent (Plot Generator)
  - Takes the Supervisor’s plan and poduces executable Python code for plots or tables (using matplotlib, seaborn, or plotly).
  - Executes the code within a secure sandbox (e.g., Docker, Jupyter kernel).
  - Returns visual outputs and summaries to the Supervisor.

Feedback Loop
  - The Supervisor reviews generated plots and summaries, refining prompts or parameters to improve relevance and clarity.
  - Ensures report coherence and visual quality before final integration.

### Report Generation Layer

Combines all outputs—metadata, plots, insights—into a cohesive, publication-ready report.
Pipeline: Markdown → HTML/PDF (via Jinja2, WeasyPrint, or ReportLab).
#### Structure:
```text
.
├── README.md                   # Main project documentation
├── requirements.txt            # Python dependencies
│
└── intelligent_reporting/
    ├── agents/
    ├── exporting/
    ├── loading/
    └── profiling/
```

### Execution & Integration Layer
- Isolates and executes code safely (Python sandbox, Docker, or notebook kernel).
- Connects seamlessly to existing data pipelines (NiFi, Airflow, etc.) for automatic scheduling and dataset refresh.
- Supports APIs for external system integration.

## Technical Stack Summary
| Layer	| Tools / Frameworks|
|-------|--------------------|
| LLM & Agent Framework	| OpenAI GPT / Local LLMs (Llama 3, Mistral) via LangChain, LangGraph, or CrewAI|
| Data Handling	| Pandas, Polars|
| Visualization	| Matplotlib, Seaborn, Plotly|
| Execution Sandbox	| exec, Docker, or jupyter_client|
| Reporting	| Jinja2, Markdown, WeasyPrint, ReportLab|
| Storage	| SQLite, local FS for logs & results|

## Prerequisites for Success
- High-Quality Data: Clean, consistent, and well-documented input.
- Robust Models: Use capable LLMs for reasoning, coding, and summarization.
- Clear Objectives: Define analytical goals (KPIs, anomalies, trends).
- Scalable Infrastructure: Cloud-based or containerized compute for resource-intensive workloads.
- Multidisciplinary Expertise: Collaboration among data engineers, ML experts, and analysts.
- TTesting & Validation: Unit, integration, and benchmark testing across agents.
- Ethical & Privacy Compliance: Conform to GDPR, HIPAA, and general AI ethics standards.
- Continuous Feedback Loop: Incorporate user feedback to refine analysis and improve usability.
- Iterative Development: Start small—automate core insights first, then expand into complex report generation.

## Outcome

A dynamic AI platform capable of:
- Automatically interpreting datasets,
- Generating intelligent visualizations,
- Synthesizing insights into narrative reports, and
- Delivering consistent, interpretable analytics with minimal manual effort.

## Setup
This project uses Python tooling, Docker-based sandboxing, and cloud LLM models. Follow these steps to prepare the environment.
### 1. Install Python Dependencies
```bash
python3 -m venv .venv
source .venv/bin/activate    # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```
### 2.Initialize LLM providers 
The system uses cloud-hosted LLMs that must be “activated” by sending a first message:

- qwen3-vl:235b-cloud

- deepseek-v3.1:671b-cloud

Log into your LLM platform (Ollama Cloud, Foundry, etc.) and send a short message (e.g., “hello”) to each model to ensure they respond.

### 3. Build and Run the Execution Sandbox
The sandbox is where plot generating code runs safely. Ensure Docker is running.

From the project root:
```bash
cd sandbox
docker build -t intelligent-reporting-sandbox -f dockerfile.sandbox .
docker run -d --name reporting-sandbox intelligent-reporting-sandbox
```
Generated files appear in: 
sandbox/output/   # visualizations, tables, PDFs
sandbox/code/     # agent-generated Python code