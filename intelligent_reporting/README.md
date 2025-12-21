# 📁 Connectors Module

The connectors module provides a unified and extensible system for loading data from multiple file formats and database engines.  
It powers the data ingestion layer of `intelligent_reporting` and ensures each data source follows a consistent, predictable interface.

---

## 💡 What Connectors Do

- They take a file or database connection.  
- They read the data.  
- They return it in a clean, usable form for the rest of the system.  

Each connector focuses on one format only (CSV, JSON, Excel, Parquet, XML, databases, etc.), which keeps things simple and organized.

---

## 🧩 Available Connectors

| Connector            | Supported Types            | Description                                           |
|----------------------|----------------------------|-------------------------------------------------------|
| **CSVConnector**     | `.csv`, `.tsv`, `.txt`     | Reads delimited text files.                           |
| **JSONConnector**    | `.json`                    | Reads JSON documents or arrays of records.            |
| **ParquetConnector** | `.parquet`                 | Loads Parquet files via pandas/pyarrow.               |
| **SpreadsheetConnector** | `.xlsx`, `.xls`, `.ods`| Loads Excel and spreadsheet-like formats.             |
| **XMLConnector**     | `.xml`                     | Parses XML and converts tree structures into rows.    |
| **SQLAlchemyConnector** | Databases & Cloud              | Connects to SQL databases using SQLAlchemy.           |

## 📌 Summary — All databases and warehouses you can ingest  
❗ *Relational / SQL databases supported through SQLAlchemy:*

✔ PostgreSQL  
✔ MySQL & MariaDB  
✔ SQLite  
✔ Oracle  
✔ Microsoft SQL Server  
✔ Amazon Redshift  
✔ Snowflake  
✔ CockroachDB  
✔ BigQuery (via SQLAlchemy wrapper)  
✔ Hive / Presto  
✔ ClickHouse  
✔ IBM DB2 / Informix  
✔ SAP ASE  
…and many others available through community SQLAlchemy dialects.
---✔ PostgreSQL  
✔ MySQL & MariaDB  
✔ SQLite  
✔ Oracle  
✔ Microsoft SQL Server  
✔ Amazon Redshift  
✔ Snowflake  
✔ CockroachDB  
✔ BigQuery (via SQLAlchemy wrapper)  
✔ Hive / Presto  
✔ ClickHouse  
✔ IBM DB2 / Informix  
✔ SAP ASE  

Below is the definitive list of which Python package you must install for each database, using the most widely supported and SQLAlchemy-compatible drivers.
| Database                 | Python Driver (DBAPI)                | Install Command                              |
|--------------------------|--------------------------------------|-----------------------------------------------|
| **PostgreSQL**           | `psycopg2` / `psycopg2-binary`       | `pip install psycopg2-binary`                 |
| **MySQL**                | `pymysql` / `mysqlclient`            | `pip install pymysql`                         |
| **MariaDB**              | `mariadb`                            | `pip install mariadb`                         |
| **SQLite**               | built-in (`sqlite3`)                 | *(no install needed)*                         |
| **Oracle**               | `cx_Oracle`                          | `pip install cx_Oracle`                       |
| **Microsoft SQL Server** | `pyodbc`                             | `pip install pyodbc`                          |
| **Amazon Redshift**      | `redshift-connector` / `psycopg2`    | `pip install redshift-connector`              |
| **Snowflake**            | `snowflake-connector-python`         | `pip install snowflake-connector-python`      |
| **CockroachDB**          | PostgreSQL drivers (`psycopg2`)      | `pip install psycopg2-binary`                 |
| **Google BigQuery**      | `pybigquery`                         | `pip install pybigquery`                      |
| **Presto / Trino**       | `trino`                              | `pip install trino`                           |
| **Hive**                 | `pyhive[hive]`                       | `pip install pyhive[hive]`                    |
| **ClickHouse**           | `clickhouse-connect`                 | `pip install clickhouse-connect`              |
| **IBM DB2 / Informix**   | `ibm_db`                             | `pip install ibm_db`                          |
| **SAP ASE (Sybase)**     | `pyodbc` / `python-sybase` (legacy)  | `pip install pyodbc`                          |


## 🧠 How It Works

- The project automatically selects the correct connector based on the file extension.  
  Example: `.csv` → CSV connector, `.json` → JSON connector.  

- For databases, the system uses a dedicated database connector.

This means you don’t need to think about how the data is loaded — it just works.

## 🧠 How to Use the Pipeline

### Example: Loading a Flat File, infering its schema and downcasting it
#### 📥 Loading Data

In this case, the `Pipeline` constructor accepts a single parameter named **`file`**.  
This parameter represents the data source path and is intentionally named `file`
(not `file_path` or `name_file`) to keep the API simple and consistent.

All configuration is done at initialization time.  
Therefore, the `load()` method **does not require positional arguments**.

---

#### 🧬 Inferring Schema

The infer() method requires a dataframe and optionally accepts a schema directory.

**Accepted parameters:**
- `data` *(required)*: Polars DataFrame
- `schema_dir` *(optional)*: directory where schemas are stored or generated

---

#### 🪶 Downcasting Data

The `downcast()` method **only requires** the dataframe.

**Accepted parameters:**
- `data` *(required)*: Polars DataFrame

---
example:
```python
from intelligent_reporting.pipeline import Pipeline

def main():
    file = "data/samples.csv"
    pipeline = Pipeline(file=file)
    raw = pipeline.load()  # returns a polars.DataFrame

    # do anything with the DataFrame
    # print(data)

    typed, schema = pipeline.infer(data=raw) # also supports schema_dir
    # print(typed)

    downcasted = pipeline.downcast(data=typed) # only supports data
    # print(downcasted)

if __name__ == "__main__":
    main()
```

#### 📌 Supported File Types & Accepted Parameters

**CSV**
> The file path must be provided at pipeline initialization.

Accepted parameters for `load()`:
- `has_header`: bool  
- `quote_char`: string  
- `encoding`: string  

---

**Excel**
> Choose **either** `sheet_id` or `sheet_name`.

Accepted parameters for `load()`:
- `sheet_id`: 0, 1, 2, ... (int)  
- `sheet_name`: string  
- `table_name`: string  
- `has_header`: bool  

---

**JSON**
No additional parameters.

---

**Parquet**
No additional parameters.

---

**XML**
No additional parameters.


**Sources (for Python structure and exception handling syntax):**  
- Python Software Foundation — *Defining Main Functions & Script Execution*: https://docs.python.org/3/library/__main__.html  
- Python Software Foundation — *Errors and Exceptions*: https://docs.python.org/3/tutorial/errors.html

### Example: Loading Data from a Database
#### 📥 Loading Data
In this case, the `Pipeline` constructor accepts a single parameter named **`db_url`**.  
This parameter represents the SQLAlchemy database connection string and is intentionally
named `db_url` (not `db_conn` or `connection_string`) to keep the API simple and consistent.

When working with databases, the configuration is handled at initialization time.  
However, the `load()` method takes a single parameter named **`table`**.

This parameter represents the name of the table from which the data should be ingested
and is intentionally named `table` (not `db_table` or `table_name`) to keep the API simple
and consistent.

> **Note:** All parameters are passed as **keyword arguments**.

#### 🧬 Inferring Schema

The infer() method requires a dataframe and optionally accepts a schema directory.

**Accepted parameters:**
- `data` *(required)*: Polars DataFrame
- `schema_dir` *(optional)*: directory where schemas are stored or generated

---

#### 🪶 Downcasting Data

The `downcast()` method **only requires** the dataframe.

**Accepted parameters:**
- `data` *(required)*: Polars DataFrame

---
example:
```python
from intelligent_reporting.pipeline import Pipeline

def main():
    db_url = "driver://user:passwd@host:port/db"
    table = "table_name" 

    pipeline = Pipeline(db_url=db_url)
    raw = pipeline.run(table=table) # returns a polars.DataFrame

    # do anything with the DataFrame
    # print(data)

    typed, schema = pipeline.infer(data=raw) # also supports schema_dir
    # print(typed)

    downcasted = pipeline.downcast(data=typed) # only supports data
    # print(downcasted)

if __name__ == "__main__":
    main()
```
----------------------------------
# 📊 Automated Data Profiling & Exploratory Analysis Module

Once data is ingested, typed, and optimized, it flows into an automated EDA layer designed to deliver fast, consistent, and decision-ready insights with minimal human intervention.

---

##  Business Value

This EDA system helps teams:

- Reduce time spent on repetitive analysis
- Standardize insights across datasets and projects
- Quickly assess data quality and risks
- Surface key relationships early (before modeling or reporting)
- Produce artifacts that can be shared directly with stakeholders

It enables faster data understanding without requiring deep domain expertise upfront.

---
## 🧱 EDA Modules Overview

The EDA pipeline is composed of **independent modules** that can be run together or separately, depending on the use case.

---

### 🔹 Sampling

Creates a **representative subset** of large datasets to:
- Speed up analysis
- Enable quick exploration
- Preserve global data structure

📤 **Output:** sampled dataset saved to disk

---

### 🔹 Data Summary & Quality Profiling

Provides a **high-level understanding** of the dataset:
- Dataset size and structure
- Missing values and duplicates
- Basic statistics and distributions
- Detection of constant or low-information columns

📤 **Output:** structured JSON summary

---

### 🔹 Automated Visual Analysis

Automatically generates **clear, presentation-ready charts**:
- Numeric and categorical distributions
- Time trends (when applicable)
- Outlier and imbalance detection

Visuals are generated using **safe defaults**, avoiding noise and over-plotting.

📤 **Output:** PNG figures ready for reports or dashboards

---

### 🔹 Correlation & Relationship Analysis

Identifies **meaningful relationships** between variables:
- Highlights strong correlations
- Filters out invalid or misleading signals
- Helps guide feature selection and business hypotheses

📤 **Output:** correlation heatmaps and relationship plots


- Internal logging using Python’s `logging` module
- `NullHandler` by default (safe for libraries)
- Caller can enable logging centrally
- Informative lifecycle messages per module

---

## 🚀 Example Usage

```python
from intelligent_reporting.pipeline import Pipeline
from intelligent_reporting.profiling import *
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logging.getLogger(__name__).info("Profiling pipeline started")

file = "data/samples.csv"
pipeline = Pipeline(file=file)
raw = pipeline.load()  # returns a polars.DataFrame

typed, schema = pipeline.infer(data=raw) # also supports schema_dir

downcasted = pipeline.downcast(data=typed) # only supports data

RESULTS_DIR = "results"
FIGURES_DIR = "figures"
MAX_ROWS = 5

sampler = DataSampler(df=downcasted, max_rows=MAX_ROWS, sample_dir = RESULTS_DIR)
summarizer = DataSummarizer(df=downcasted, summary_dir= RESULTS_DIR, figures_dir= FIGURES_DIR)
visualizer = DataVisualizer(df=downcasted, summary_dir= RESULTS_DIR, figures_dir= FIGURES_DIR, top_k_categories=5)
correlater = DataCorrelater(df=downcasted)

sample = sampler.run_sample()
summary = summarizer.summary()
visualizer.run_viz()
correlater.run()