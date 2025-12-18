import polars as pl
import numpy as np
from .base_connector import BaseConnector
from .registry import register_file
from ..expection import *
import os

@register_file([".parquet", ".pq"])
class ParquetConnector(BaseConnector):
    def __init__(self, path: str):
        self.nulls = {}
        self.path = path

    def _standerdize_null_likes(self, *, df: pl.DataFrame):
        NULL_LIKES = {
            " ", "", "null", "none", "nan", "n/a", "na",
            "#n/a", "#na", "--", "?", "unknown", "missing",
            "undefined", ".", "blank", "empty"
        }

        return df.with_columns([
            pl.when(
                pl.col(col).is_null() |
                pl.col(col).cast(str).is_in(NULL_LIKES)
            )
            .then(None)
            .otherwise(pl.col(col))
            .alias(col)
            for col in df.columns
        ])

    def load(self):
        """
        Turn a Parquet file as pl.DataFrame
        Does not support chunk processing yet
        """
        if not os.path.exists(self.path):
            raise DataLoadingError(
                f"File not found: {self.path}"
            )

        # sanity check
        try:
            df = pl.read_parquet(
                self.path,
                n_rows=1
            )
        except Exception as e:
            raise DataLoadingError(
                f"Invalid or corrupted Parquet file: {self.path}"
            ) from e

        if df.width == 0:
            raise EmptyDatasetError(
                f"Parquet file has no columns: {self.path}"
            )

        if df.height == 0:
            raise EmptyDatasetError(
                f"Parquet file contains no rows: {self.path}"
            )
        try:
            df = pl.read_parquet(source=self.path)
            df = self._standerdize_null_likes(df=df)

            return df
        except Exception as e:
            raise DataLoadingError(
                f"Failed to fully load Parquet file: {self.path}"
            ) from e