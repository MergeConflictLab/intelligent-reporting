# Agentic Backend API Documentation

> **Base URL:** `http://intelrepo.duckdns.org:8000/` 
>
> All endpoints accept `application/json` and return `application/json`.

---

## Quick Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Root - Check if API is running |
| GET | `/health` | Health check with cached agents info |
| POST | `/agents/metadata/run` | Analyze dataset and generate column metadata |
| POST | `/agents/supervisor/run` | Plan analysis tasks from metadata |
| POST | `/agents/assistant/run` | Generate Python code for a task |
| POST | `/agents/insights/run` | Generate insights from a chart image |
| POST | `/agents/generic/run` | Run any agent with dynamic payload |
| POST | `/sandbox/run` | Execute Python code in Docker sandbox |

---

## Endpoints

### 1. Health Check

Check if the API is running and view cached agents.

```
GET /health
```

**Response:**
```json
{
  "status": "ok",
  "cached_agents": ["metadata", "supervisor"]
}
```

---

### 2. Metadata Agent

Analyzes sample data and schema to generate enriched column descriptions.

```
POST /agents/metadata/run
```

**Request Body:**
```json
{
  "sample_data": [
    {"column1": "value1", "column2": 123},
    {"column1": "value2", "column2": 456}
  ],
  "schema_info": {
    "columns": {
      "column1": {"type": "string", "name": "column1"},
      "column2": {"type": "number", "name": "column2"}
    }
  },
  "description": {
    "column1": {"type": "string", "name": "column1"},
    "column2": {"type": "number", "name": "column2"}
  },
  "offline_mode": true
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `sample_data` | `Array<Object>` | ✅ | Sample rows from the dataset |
| `schema_info` | `Object` | ✅ | Schema with column definitions |
| `description` | `Object` | ✅ | Column descriptions/metadata |
| `offline_mode` | `boolean` | ❌ | Use local models (default: `false`) |

**Response:**
```json
{
  "table_description": "Sales data containing transaction records...",
  "columns": [
    {
      "name": "column1",
      "type": "string",
      "description": "Product category identifier",
      "semantic_type": "categorical"
    }
  ]
}
```

---

### 3. Supervisor Agent

Plans analysis tasks based on the metadata output.

```
POST /agents/supervisor/run
```

**Request Body:**
```json
{
  "sample_data": [
    {"column1": "value1", "column2": 123}
  ],
  "description": [
    {
      "name": "column1",
      "type": "string",
      "description": "Product category"
    },
    {
      "name": "column2",
      "type": "number",
      "description": "Sales amount"
    }
  ],
  "offline_mode": true
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `sample_data` | `Array<Object>` | ✅ | Sample rows from the dataset |
| `description` | `Array<Object>` | ✅ | Column descriptions (from metadata agent) |
| `offline_mode` | `boolean` | ❌ | Use local models (default: `false`) |

**Response:**
```json
{
  "libraries": ["pandas", "matplotlib", "seaborn"],
  "tasks": [
    {
      "name": "sales_by_category",
      "description": "Create a bar chart showing total sales by product category",
      "chart_type": "bar",
      "columns": ["column1", "column2"]
    },
    {
      "name": "sales_distribution",
      "description": "Create a histogram showing distribution of sales amounts",
      "chart_type": "histogram",
      "columns": ["column2"]
    }
  ]
}
```

---

### 4. Assistant Agent

Generates Python code for a specific task.

```
POST /agents/assistant/run
```

**Request Body:**
```json
{
  "supervisor_response": {
    "name": "sales_by_category",
    "description": "Create a bar chart showing total sales by product category",
    "chart_type": "bar",
    "columns": ["column1", "column2"]
  },
  "path": "/sandbox/data/sales_data.csv",
  "offline_mode": true
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `supervisor_response` | `Object` | ✅ | Single task object from supervisor |
| `path` | `string` | ✅ | Path to data file (inside sandbox) |
| `offline_mode` | `boolean` | ❌ | Use local models (default: `false`) |

**Response:**
```json
{
  "name": "sales_by_category",
  "code": "import pandas as pd\nimport matplotlib.pyplot as plt\n\ndf = pd.read_csv('/sandbox/data/sales_data.csv')\n\nplt.figure(figsize=(10, 6))\ndf.groupby('column1')['column2'].sum().plot(kind='bar')\nplt.title('Sales by Category')\nplt.savefig('/sandbox/output/sales_by_category.png')\nplt.close()"
}
```

---

### 5. Insights Agent

Generates insights from a chart image.

```
POST /agents/insights/run
```

**Request Body:**
```json
{
  "img": "<base64-encoded-image-string>",
  "summary_data": {
    "table_description": "Sales data...",
    "columns": [...]
  },
  "sample_data": [
    {"column1": "value1", "column2": 123}
  ],
  "description": {
    "name": "sales_by_category",
    "description": "Bar chart of sales by category"
  },
  "offline_mode": true
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `img` | `string` | ✅ | Base64-encoded image (PNG/JPG) |
| `summary_data` | `Object` | ✅ | Metadata response or summary |
| `sample_data` | `Array<Object>` | ✅ | Sample rows from dataset |
| `description` | `Object` | ✅ | Task description that generated the chart |
| `offline_mode` | `boolean` | ❌ | Use local models (default: `false`) |

**Response:**
```json
{
  "title": "Sales Distribution by Category",
  "key_findings": [
    "Electronics category has the highest sales at $45,000",
    "Clothing shows a 23% increase compared to last period"
  ],
  "recommendations": [
    "Focus marketing efforts on the Electronics category",
    "Investigate low performance in Home & Garden"
  ]
}
```

---

### 6. Generic Agent Runner

Run any agent type with a dynamic payload. Useful for testing.

```
POST /agents/generic/run
```

**Request Body:**
```json
{
  "agent_type": "supervisor",
  "payload": {
    "sample_data": [...],
    "description": [...],
    "offline_mode": true
  }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `agent_type` | `string` | ✅ | One of: `metadata`, `supervisor`, `assistant`, `insights` |
| `payload` | `Object` | ✅ | Arguments matching the agent's `run()` method |

---

### 7. Sandbox Execution

Execute Python code in an isolated Docker container.

```
POST /sandbox/run
```

**Request Body:**
```json
{
  "code": "import pandas as pd\ndf = pd.read_csv('/sandbox/data/data.csv')\nprint(df.head())\n\nimport matplotlib.pyplot as plt\nplt.figure()\ndf.plot()\nplt.savefig('/sandbox/output/chart.png')",
  "data_dir": "data",
  "image": "llm-sandbox",
  "name": "my_analysis",
  "sample_data": [
    {"col1": "a", "col2": 1},
    {"col1": "b", "col2": 2}
  ],
  "filename": "data.csv"
}
```

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `code` | `string` | ✅ | - | Python code to execute |
| `data_dir` | `string` | ❌ | `"data"` | Host directory to mount |
| `image` | `string` | ❌ | `"llm-sandbox"` | Docker image name |
| `name` | `string` | ❌ | `null` | Container/task name |
| `sample_data` | `Array<Object>` | ❌ | `[]` | Data to write as CSV |
| `filename` | `string` | ❌ | `"data.csv"` | Filename for sample_data |

**Response:**
```json
{
  "stdout": "   col1  col2\n0    a     1\n1    b     2",
  "stderr": "",
  "exit_code": 0,
  "artifacts": ["/path/to/sandbox/output/chart.png"],
  "media": [
    {
      "filename": "chart.png",
      "content": "<base64-encoded-png>"
    }
  ]
}
```

> [!IMPORTANT]
> **Sandbox File Paths:**
> - Data files are mounted at `/sandbox/data/`
> - Save outputs to `/sandbox/output/` for artifact collection

---

## Error Handling

All endpoints return HTTP 500 on failure with a JSON body:

```json
{
  "detail": "Error message describing what went wrong"
}
```

**Common Errors:**
- `400 Bad Request` - Invalid agent type or malformed request
- `500 Internal Server Error` - Agent execution failed

---

## Complete Workflow Example

Here's how to use all endpoints together for a full analysis pipeline:

### Step 1: Check Health
```bash
curl https://your-url.trycloudflare.com/health
```

### Step 2: Run Metadata Agent
```bash
curl -X POST https://your-url.trycloudflare.com/agents/metadata/run \
  -H "Content-Type: application/json" \
  -d '{
    "sample_data": [{"product": "Widget", "sales": 100}],
    "schema_info": {"columns": {"product": {"type": "string"}, "sales": {"type": "number"}}},
    "description": {"product": {"type": "string"}, "sales": {"type": "number"}},
    "offline_mode": true
  }'
```

### Step 3: Run Supervisor Agent
```bash
curl -X POST https://your-url.trycloudflare.com/agents/supervisor/run \
  -H "Content-Type: application/json" \
  -d '{
    "sample_data": [{"product": "Widget", "sales": 100}],
    "description": [{"name": "product", "type": "string"}, {"name": "sales", "type": "number"}],
    "offline_mode": true
  }'
```

### Step 4: Run Assistant Agent (for each task)
```bash
curl -X POST https://your-url.trycloudflare.com/agents/assistant/run \
  -H "Content-Type: application/json" \
  -d '{
    "supervisor_response": {"name": "sales_chart", "description": "Create sales chart"},
    "path": "/sandbox/data/data.csv",
    "offline_mode": true
  }'
```

### Step 5: Execute Code in Sandbox
```bash
curl -X POST https://your-url.trycloudflare.com/sandbox/run \
  -H "Content-Type: application/json" \
  -d '{
    "code": "import pandas as pd\nprint(\"Hello from sandbox!\")",
    "sample_data": [{"product": "Widget", "sales": 100}],
    "filename": "data.csv"
  }'
```

### Step 6: Generate Insights (for each chart)
```bash
curl -X POST https://your-url.trycloudflare.com/agents/insights/run \
  -H "Content-Type: application/json" \
  -d '{
    "img": "<base64-image-from-sandbox-response>",
    "summary_data": {"table_description": "Sales data"},
    "sample_data": [{"product": "Widget", "sales": 100}],
    "description": {"name": "sales_chart"},
    "offline_mode": true
  }'
```

---

## JavaScript/TypeScript Example

```typescript
const BASE_URL = "https://your-url.trycloudflare.com";

// Health check
async function checkHealth() {
  const res = await fetch(`${BASE_URL}/health`);
  return res.json();
}

// Run Metadata Agent
async function runMetadata(sampleData: object[], schema: object, description: object) {
  const res = await fetch(`${BASE_URL}/agents/metadata/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      sample_data: sampleData,
      schema_info: schema,
      description: description,
      offline_mode: true
    })
  });
  return res.json();
}

// Run Supervisor Agent
async function runSupervisor(sampleData: object[], description: object[]) {
  const res = await fetch(`${BASE_URL}/agents/supervisor/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      sample_data: sampleData,
      description: description,
      offline_mode: true
    })
  });
  return res.json();
}

// Run code in sandbox
async function runSandbox(code: string, sampleData: object[] = []) {
  const res = await fetch(`${BASE_URL}/sandbox/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      code: code,
      sample_data: sampleData,
      filename: "data.csv"
    })
  });
  return res.json();
}
```

---

## Notes

- **Timeout:** LLM operations can take 30-120 seconds. Set appropriate client timeouts.
- **offline_mode:** When `true`, uses local/cached models. When `false`, may use external APIs.
- **Base64 Images:** The `img` field for insights should be raw base64 without data URL prefix.
- **Sandbox Paths:** Always use `/sandbox/data/` for input and `/sandbox/output/` for artifacts.
