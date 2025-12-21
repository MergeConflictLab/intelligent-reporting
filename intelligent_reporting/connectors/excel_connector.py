from .base_connector import BaseConnector
import polars as pl
from .registry import register_file
from ..expection import *
import os

import logging
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

@register_file([".xls", ".xlsx"])
class ExcelConnector(BaseConnector):
    def __init__(self, *, path: str):
        self.path = path
        self.allowed_options = {"sheet_id", "sheet_name", "table_name", "has_header"}


    def _load_all_sheets_with_schema_check(
        self,
        *,
        has_header: bool,
        engine: str,
        infer_schema_length: int,
    ) -> pl.DataFrame:

        try:
            sheets = pl.read_excel(
                source=self.path,
                has_header=has_header,
                engine=engine,
                infer_schema_length=infer_schema_length,
            )
        except Exception as e:
            raise DataLoadingError(
                f"Failed to read Excel sheets from {self.path}"
            ) from e
        if isinstance(sheets, pl.DataFrame):
            return sheets

        if not isinstance(sheets, dict) or not sheets:
            raise DataLoadingError(
                f"No sheets found in Excel file: {self.path}"
            )

        reference_df = None
        dfs = []

        for sheet_name, df in sheets.items():
            if reference_df is None:
                reference_df = df
            else:
                if df.columns != reference_df.columns:
                    raise DataLoadingError(
                        f"Schema mismatch in sheet '{sheet_name}'"
                        f"Expected columns {reference_df.columns}, "
                        f"got {df.columns}"
                    )

                if df.dtypes != reference_df.dtypes:
                    raise DataLoadingError(
                        f"Type mismatch in sheet '{sheet_name}'"
                        f"Expected {reference_df.dtypes}, "
                        f"got {df.dtypes}"
                    )

            dfs.append(df)
        return pl.concat(dfs, how="vertical")



    def load(self, **options):
        """
        Read an Excel file using Polars.

        The loader first performs a lightweight preview read to validate:
        - file existence
        - sheet accessibility
        - non-empty structure

        Then it performs the full load.
        """
        logger.info("Excel loader initialized | path=%s", self.path)

        if not os.path.exists(self.path):
            raise DataLoadingError(f"File not found: {self.path}")

        # ---- configuration validation ----
        allowed_keys = {"sheet_id", "sheet_name", "table_name", "has_header"}
        for key in options:
            if key not in allowed_keys:
                raise ConfigurationError(
                    f"For {self.__class__.__name__}, expected parameters are "
                    f"{sorted(allowed_keys)} but got '{key}'"
                )

        # ---- parameter resolution + logging ----
        sheet_id = options.get("sheet_id", 1)
        if sheet_id < 0:
            raise ConfigurationError(f"sheet_id must be a positive integer. But got {sheet_id}")
        sheet_name = options.get("sheet_name")
        table_name = options.get("table_name")
        has_header = options.get("has_header")

        if "sheet_id" in options:
            logger.info("Excel loader | user-provided parameter: sheet_id=%s", sheet_id)
        else:
            logger.info("Excel loader | default parameter: sheet_id=%s", sheet_id)

        if "sheet_name" in options:
            logger.info("Excel loader | user-provided parameter: sheet_name=%s", sheet_name)

        if "table_name" in options:
            logger.info("Excel loader | user-provided parameter: table_name=%s", table_name)

        if "has_header" in options:
            logger.info("Excel loader | user-provided parameter: has_header=%s", has_header)

        # ---- special case: ALL sheets ----
        if sheet_id == 0:
            logger.info(
                "Excel loader | loading all sheets (sheet_id=0) with schema consistency check"
            )
            return self._load_all_sheets_with_schema_check(
                has_header=has_header,
                infer_schema_length=50,
                engine="calamine",
            )

        # ---- phase 1: preview read (validation only) ----
        try:
            logger.debug(
                "Excel loader | preview read | sheet_id=%s sheet_name=%s table_name=%s",
                sheet_id,
                sheet_name,
                table_name,
            )
            preview_df = pl.read_excel(
                source=self.path,
                sheet_id=sheet_id,
                sheet_name=sheet_name,
                table_name=table_name,
                has_header=has_header,
                infer_schema_length=50,
                raise_if_empty=False,
            )
            if preview_df.width == 0:
                raise EmptyDatasetError(
                    f"Excel sheet has no columns: {self.path}"
                )

            if preview_df.height == 0:
                raise EmptyDatasetError(
                    f"Excel sheet contains no rows: {self.path}"
                )
        except EmptyDatasetError:
            raise
        except Exception as e:
            raise DataLoadingError(
                f"Failed to open Excel file or sheet: {self.path} "
                f"(sheet_id={sheet_id}, sheet_name={sheet_name}): {e}"
            ) from e

        

        # ---- phase 2: full load ----
        try:
            logger.info(
                "Excel loader | performing full load | sheet_id=%s sheet_name=%s table_name=%s",
                sheet_id,
                sheet_name,
                table_name,
            )
            return pl.read_excel(
                source=self.path,
                sheet_id=sheet_id,
                sheet_name=sheet_name,
                table_name=table_name,
                has_header=has_header,
                infer_schema_length=0,
                raise_if_empty=False,
            )
        except Exception as e:
            raise DataLoadingError(
                f"Failed to fully load Excel file: {self.path}: {e}"
            ) from e
