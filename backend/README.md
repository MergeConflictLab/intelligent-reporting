# Intelligent Reporting Backend

This directory contains the FastAPI-based backend for the Intelligent Reporting system. It serves as the bridge between the frontend UI and the core agentic logic.

## Key Components

- **API Layer**: `app/` contains the FastAPI application and route definitions.
- **Agent Orchestration**: Uses the `intelligent_reporting` core library to manage Metadata, Supervisor, Assistant, and Insights agents.
- **Sandbox**: Manages Docker containers for safe code execution.

## Getting Started

### Prerequisites

- Python 3.10+
- Docker (must be running)

### Installation

1. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   Copy `.env.example` to `.env` and fill in the necessary values (e.g., OpenAI API key if running in online mode).

### Running the Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`.
API Documentation is available at `http://localhost:8000/docs`.

### Docker Deployment

You can also build and run the backend as a Docker container:

```bash
docker build -t intelligent-reporting-backend .
docker run -d \
  -p 8000:8000 \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v $(pwd)/sandbox/data:/app/sandbox/data \
  -v $(pwd)/sandbox/output:/app/sandbox/output \
  -v $(pwd)/models:/app/models \
  intelligent-reporting-backend
```

## API Documentation

Detailed API documentation can be found in [API_DOCUMENTATION.md](API_DOCUMENTATION.md).

## Agents

The backend exposes several agent capabilities:

- **Metadata Agent**: Extracts structural and semantic metadata from datasets.
- **Supervisor Agent**: Generates analysis plans.
- **Assistant Agent**: Generates and executes Python code.
- **Insights Agent**: Interprets results and visualizations.

## Offline Mode

The backend supports an `offline_mode` which utilizes local GGUF models instead of external LLM APIs. Ensure you have the necessary models downloaded in the `models/` directory if you intend to use this feature.

## Roadmap

- [ ] **Async Task Queue**: Implement Celery + Redis for handling long-running analysis tasks.
- [ ] **Database Integration**: Replace in-memory caching with PostgreSQL for persistent agent state.
- [ ] **Streaming Responses**: Support server-sent events (SSE) for real-time agent thought streaming.
- [ ] **Security Hardening**: Enhanced sandbox isolation and API rate limiting.

