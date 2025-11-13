import pandas as pd
import polars as pl

from scripts.ingest import get_schema
from scripts.ingest import describe_schema

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


# BACK
