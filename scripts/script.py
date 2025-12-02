import pandas as pd
import polars as pl
import numpy as np
from typing import Dict, List

import json
import sqlite3


# import fastavro

import sqlalchemy

# Assume df is a Polars DataFrame loaded using ingest_data


def clean_dataframe(df: pl.DataFrame):
    """Cleans the DataFrame with minimal processing."""

    schema = get_schema(df)
    description = describe_schema(df)

    # Conversion for string columns that represent numbers, to avoid error
    for col_name in description:
        if col_name["dtype"] == "str" and (
            "int" in col_name["name"] or "float" in col_name["name"]
        ):
            try:
                df[col_name["name"]] = pd.to_numeric(
                    df[col_name["name"]], errors="coerce"
                )
            except:
                pass

    # String cleaning - remove leading/trailing whitespace
    for col in df.columns:
        if str(df[col].dtype).startswith("str"):
            df[col] = df[col].str.strip()

    # Imputation example (selective) - only if >20% missing
    for col in df.columns:
        if df[col].is_null().sum() / len(df) > 0.2:
            # Only numeric columns
            if str(df[col].dtype).startswith("numeric"):
                df[col].fillna(df[col].mean(), inplace=True)
                df[col] = df[col].astype(pl.Float64)  # Explicit type
                df[col + "_was_missing"] = (
                    pl.when(pl.col(col).is_null()).then(1).otherwise(0)
                )

    return df  # Or return updated dataframe


def compact_sample_for_prompt(
    df: pl.DataFrame, n_rows: int = 5, max_chars: int = 2000, max_value_chars: int = 200
) -> List[Dict]:
    """Return a compact list-of-dicts safe to include in LLM prompts.

    - Takes the first `n_rows` from `df` (or fewer if needed).
    - Truncates long string values to `max_value_chars`.
    - If the resulting JSON still exceeds `max_chars`, reduces the number of rows until it fits.
    - Falls back to returning a list with a single dict of column->dtype pairs if nothing else fits.
    """
    # start with top n_rows
    rows = df.head(n_rows).to_dicts()

    def _truncate_value(v):
        if v is None:
            return None
        if isinstance(v, str):
            if len(v) > max_value_chars:
                return v[: max_value_chars - 3] + "..."
            return v
        # basic stringify for complex types
        if isinstance(v, (list, dict)):
            s = json.dumps(v, ensure_ascii=False)
            if len(s) > max_value_chars:
                return s[: max_value_chars - 3] + "..."
            return s
        return v

    def _rows_to_compact(rlist):
        out = []
        for r in rlist:
            nr = {k: _truncate_value(v) for k, v in r.items()}
            out.append(nr)
        return out

    compact = _rows_to_compact(rows)
    j = json.dumps(compact, ensure_ascii=False)
    cur_rows = len(compact)
    # reduce rows until fits max_chars
    while len(j) > max_chars and cur_rows > 0:
        cur_rows = max(0, cur_rows - 1)
        compact = _rows_to_compact(rows[:cur_rows])
        j = json.dumps(compact, ensure_ascii=False)

    if len(j) <= max_chars and cur_rows > 0:
        return compact

    # fallback: return schema-like small sample
    schema_sample = [{"column": name, "dtype": str(t)} for name, t in df.schema.items()]
    return schema_sample


def get_schema(df: pl.DataFrame) -> Dict[str, str]:
    """Return column -> dtype for a Polars DataFrame."""
    return {name: str(dtype) for name, dtype in df.schema.items()}


def describe_schema(df: pl.DataFrame) -> List[Dict]:
    """Describe each column with dtype, null_count, nullable, and unique_count."""
    out = []
    for col in df.columns:
        s = df[col]
        out.append(
            {
                "name": col,
                "dtype": str(s.dtype),
                "null_count": int(s.is_null().sum()),
                "nullable": bool(s.is_null().sum() > 0),
                "unique_count": int(s.n_unique()),
            }
        )
    return out


def load_data(
    source: str, table: str = None, query: str = None, **kwargs
) -> pl.DataFrame:
    """
    Load data from a wide range of file formats or database connections into a Polars DataFrame.

    Supported:
    - .csv, .parquet, .delta, .xlsx, .xls, .avro
    - SQLite (.db), SQL files (.sql), database URIs (Postgres, MySQL, etc.)
    """

    src = source.lower()

    if src.endswith(".csv"):
        return pl.read_csv(source, ignore_errors=True, **kwargs)
    elif src.endswith(".parquet"):
        return pl.read_parquet(source)
    elif src.endswith(".xlsx") or src.endswith(".xls"):
        return pl.from_pandas(pd.read_excel(source, **kwargs))

    elif src.endswith(".db"):
        conn = sqlite3.connect(source)
        if query:
            df = pd.read_sql_query(query, conn)
        elif table:
            df = pd.read_sql(f"SELECT * FROM {table}", conn)
        else:
            raise ValueError("Specify table or query for .db source.")
        conn.close()
        return pl.from_pandas(df)
    elif src.endswith(".sql"):
        with open(source) as f:
            sql = f.read()
        # You’ll need to pass a DB connection string via kwargs["conn_str"]
        engine = sqlalchemy.create_engine(kwargs["conn_str"])
        df = pd.read_sql(sql, engine)
        return pl.from_pandas(df)

    elif (
        src.startswith("postgresql://")
        or src.startswith("mysql://")
        or src.startswith("sqlite://")
        or src.startswith("mssql+pyodbc://")
    ):
        engine = sqlalchemy.create_engine(source)
        if query:
            df = pd.read_sql(query, engine)
        elif table:
            df = pd.read_sql(f"SELECT * FROM {table}", engine)
        else:
            raise ValueError("Specify table or query when connecting to a database.")
        return pl.from_pandas(df)

    else:
        raise ValueError(f"Unsupported source type: {source}")


def smart_sample(
    df: pl.DataFrame, target_col: str = None, max_rows: int = 5000
) -> pl.DataFrame:
    n = df.height
    if n <= max_rows:
        return df

    if target_col and target_col in df.columns:
        sampled = (
            df.groupby(target_col, maintain_order=True)
            .apply(
                lambda g: g.sample(min(len(g), max_rows // df[target_col].n_unique()))
            )
            .collect()
        )
        return sampled

    numeric_cols = [
        c for c, t in df.schema.items() if "Float" in str(t) or "Int" in str(t)
    ]
    if numeric_cols:
        key = numeric_cols[0]
        quantile_bins = np.linspace(0, 1, 10)
        q_values = [df[key].quantile(q) for q in quantile_bins]
        indices = []
        for i in range(len(q_values) - 1):
            subset = df.filter((df[key] >= q_values[i]) & (df[key] < q_values[i + 1]))
            if subset.height:
                indices.append(
                    subset.sample(min(len(subset), max_rows // 10)).to_pandas()
                )
        return pl.from_pandas(pd.concat(indices))

    return df.sample(max_rows)
