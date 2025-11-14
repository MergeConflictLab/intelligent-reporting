import sqlite3
import polars as pl
import pandas as pd
import fastavro

import sqlalchemy


def load_data(
    source: str, table: str = None, query: str = None, **kwargs
) -> pl.DataFrame:
    """
    Load data from a wide range of file formats or database connections into a Polars DataFrame.

    Supported:
    - .csv, .parquet, .delta, .xlsx, .xls, .avro
    - SQLite (.db), SQL files (.sql), database URIs (Postgres, MySQL, etc.)
    """
    # TODO: Port over Naouar's improvements for datasets
    # TODO: Support JSON through Amine's Changes
    src = source.lower()

    if src.endswith(".csv"):
        return pl.read_csv(source, ignore_errors=True, **kwargs)
    elif src.endswith(".parquet"):
        return pl.read_parquet(source)
    elif src.endswith(".xlsx") or src.endswith(".xls"):
        return pl.from_pandas(pd.read_excel(source, **kwargs))
    elif src.endswith(".avro"):

        with open(source, "rb") as f:
            records = list(fastavro.reader(f))
        return pl.DataFrame(records)
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

    # TODO: Anissa to add support for more databases as needed
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
