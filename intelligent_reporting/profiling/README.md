# Profiling

This module is responsible for **analyzing data, generating statistics, and inferring schema**.  
It contains the following key classes:

- **SchemaInferer** – Handles the **structure** of the data:
  - Detects column types (numeric, datetime, boolean, string/categorical).
  - Identifies null values, unique ratios, min/max/mean/std for numeric columns.
  - Flags identifiers and constants.
  - Produces structured JSON schema representations suitable for pipelines.

- **DataProfiler** / profiling logic – Handles **distribution, statistics, and correlations**:
  - Computes summary statistics per column.
  - Detects correlations and basic patterns.
  - Optionally produces more advanced descriptive metrics for exploratory analysis.

- **QualityChecker** – Handles **data health and validation**:
  - Detects missing or inconsistent data.
  - Flags potential issues (constant columns, high null ratios, duplicates).
  - Provides alerts and warnings for downstream processing.

---

### Example JSON schema output (from SchemaInferer)

```json
{
  "num_rows": 15000,
  "num_cols": 15,
  "memory_usage_mb": 10.05,
  "columns": {
    "index": {
      "name": "index",
      "null_values": 0,
      "inferred_type": "numeric",
      "confidence": "100%",
      "unique_ratio": "100%",
      "missing_ratio": "0.0%",
      "distinct_count": 15000,
      "sample_values": [0.0, 1.0, 2.0, 3.0, 4.0],
      "is_constant": false,
      "is_identifier": true,
      "notes": "Most values are numeric."
    },
    "Order_ID": {
      "name": "Order_ID",
      "null_values": 0,
      "inferred_type": "string",
      "confidence": "100%",
      "unique_ratio": "100%",
      "missing_ratio": "0.0%",
      "distinct_count": 15000,
      "sample_values": ["ORD100000", "ORD100001", "ORD100002", "ORD100003", "ORD100004"],
      "is_constant": false,
      "is_identifier": true,
      "notes": "Mostly unique free-text strings."
    },
    "Date": {
      "name": "Date",
      "null_values": 0,
      "inferred_type": "datetime",
      "confidence": "100%",
      "unique_ratio": "2.4%",
      "missing_ratio": "0.0%",
      "distinct_count": 365,
      "sample_values": ["2025-01-25", "2025-08-28", "2025-02-27", "2025-02-24", "2025-06-15"],
      "is_constant": false,
      "is_identifier": false,
      "notes": "Contains daily timestamps."
    }
    ...
  }
}
