# Intelligent Reporting

**Intelligent Reporting** is a powerful, agentic AI data analysis platform that autonomously extracts metadata, plans analysis tasks, executes code in a sandboxed environment, and generates insights with visual evidence.

The system is built with a modular architecture comprising a React/Next.js frontend, a FastAPI backend, and a core Python library for agent orchestration.

## Features

- **Automated Metadata Extraction**: Understands your data schema and semantic meaning automatically.
- **Agentic Planning**: The Supervisor Agent creates a tailored analysis plan based on your data.
- **Sandboxed Execution**: Code is generated and executed in a secure Docker container.
- **Visual Insights**: Generates charts and provides text-based insights and recommendations.
- **Offline Mode**: Supports local execution using GGUF models for airgapped environments.

## Project Structure

- **[`frontend/`](frontend/README.md)**: Next.js + Tailwind CSS dashboard.
- **[`backend/`](backend/README.md)**: FastAPI server handling API requests and agent orchestration.
- **[`intelligent_reporting/`](intelligent_reporting/README.md)**: Core Python package containing the agent logic and pipeline definitions.

## Quick Start

### Prerequisites

- **Docker**: Required for the sandbox environment.
- **Python 3.10+**: For backend and core logic.
- **Node.js 18+**: For the frontend.

### 1. Start the Backend

 Navigate to the `backend` directory and follow the instructions in [backend/README.md](backend/README.md).

```bash
cd backend
# Install dependencies, setup environment, and run
uvicorn app.main:app --reload --port 8000
```

### 2. Start the Frontend

Navigate to the `frontend` directory and follow the instructions in [frontend/README.md](frontend/README.md).

```bash
cd frontend
npm install
npm run dev
```

Visit `http://localhost:3000` to start analyzing your data.

## License

[MIT](LICENSE)

## Roadmap & Future Improvements

We are actively working on making Intelligent Reporting more robust and versatile. Here are some key areas for future development:

- **Authentication & Multi-Tenancy**: Adding user accounts and project isolation.
- **Cloud Deployment**: First-class support for deploying to AWS/Azure/GCP with Terraform.
- **Advanced Visualizations**: Interactive React-based charts (Recharts/Visx) replacing static images.
- **Workflow Persistence**: Saving analysis state to a database (PostgreSQL) to resume sessions.
- **CI/CD Integration**: Automated pipelines for testing agents and sandbox security.

