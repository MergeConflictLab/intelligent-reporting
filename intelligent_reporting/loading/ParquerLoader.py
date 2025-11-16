import polars as pl
import numpy as np

class ParquetLoader:
    def __init__(self):
        self.nulls = {}

    def _standerdize_null_likes(self, df: pl.DataFrame):
        NULL_LIKES = {
                    None, np.nan, pl.Null," ", "", "null", "none", "nan", "n/a", "na", "#n/a", "#na", "--", "?", 
                    "unknown", "missing", "nil", "undefined", ".", "blank", "empty"
                }
        return df.with_columns([
            pl.when(pl.col(col).isin(NULL_LIKES)).then(None).otherwise(pl.col(col)) for col in df.columns
        ])

    def load(self, file_path: str, chunksize: int):
        """Yield chunks of a Parquet file as pl.DataFrame"""
        df = pl.read_parquet(file_path)
        total_rows = df.height

        for offset in range(0, total_rows, chunksize):
            yield df.slice(offset, chunksize)
