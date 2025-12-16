from .base_connector import BaseConnector
import polars as pl
from .registry import register_file
from ..expection import *
import os

@register_file([".xls", ".xlsx"])
class ExcelConnector(BaseConnector):
    def __init__(self, *, path: str):
        self.path = path


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
        Read the excel file with polars, Caller can override sheet_id/sheet_name/table_name/has_header
        by passing them in options
        """
        if not os.path.exists(self.path):
            raise DataLoadingError(
                f"File not found: {self.path}"
            )
        
        sheet_id = options["sheet_id"] if "sheet_id" in options.keys() else 1
        sheet_name = options["sheet_name"] if "sheet_name" in options.keys() else None
        table_name = options["table_name"] if "table_name" in options.keys() else None
        has_header = options["has_header"] if "has_header" in options.keys() else None
        preview_df = None
        try:
            preview_df = pl.read_excel(
                source=self.path,
                sheet_id=sheet_id,
                sheet_name=sheet_name,
                table_name=table_name,
                has_header=has_header,
                infer_schema_length=0,
            )
            if preview_df.width == 0:
                raise EmptyDatasetError(
                    f"Excel sheet has no columns: {self.path}"
                )

            if preview_df.height == 0:
                raise EmptyDatasetError(
                    f"Excel sheet contains no rows: {self.path}"
                )
        except Exception as e:
            raise DataLoadingError(
                f"Failed to open Excel file or sheet: {self.path} "
                f"(sheet_id={sheet_id}, sheet_name={sheet_name})"
            ) from e

        # special case: sheet_id == 0 then ALL sheets
        if sheet_id == 0:
            return self._load_all_sheets_with_schema_check(
                has_header=has_header,
                infer_schema_length=50,
            )
        
         # normal single-sheet load
        try:
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
                f"Failed to fully load Excel file: {self.path}"
            ) from e
