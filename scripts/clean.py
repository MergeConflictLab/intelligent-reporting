import pandas as pd
import polars as pl

from scripts.ingest import describe_schema


def clean_dataframe(df: pl.DataFrame):
    """Cleans the DataFrame with minimal processing."""

    description = describe_schema(df)

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

    for col in df.columns:
        if str(df[col].dtype).startswith("str"):
            df[col] = df[col].str.strip()

    for col in df.columns:
        if df[col].is_null().sum() / len(df) > 0.2:
            if str(df[col].dtype).startswith("numeric"):
                df[col].fillna(df[col].mean(), inplace=True)
                df[col] = df[col].astype(pl.Float64)  # Explicit type
                df[col + "_was_missing"] = (
                    pl.when(pl.col(col).is_null()).then(1).otherwise(0)
                )

    return df
