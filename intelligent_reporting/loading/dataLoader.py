import pandas as pd
import numpy as np
import sqlalchemy
import re
exts = {
    "text": {
        "extensions": [".csv", ".tsv", ".txt"],
        "method": "read_csv",
        "parameters": {"header":{}}
    },
    "excel": {
        "extensions": [".xls", ".xlsx", ".xlsb", ".ods"],
        "method": "read_excel"
    },
    "parquet": {
        "extensions": [".parquet"],
        "method": "read_parquet"
    },
    "feather": {
        "extensions": [".feather", ".ft"],
        "method": "read_feather"
    },
    "orc": {
        "extensions": [".orc"],
        "method": "read_orc"
    },
    "pickle": {
        "extensions": [".pkl", ".pickle"],
        "method": "read_pickle"
    },
    "json": {
        "extensions": [".json"],
        "method": "read_json",
        "parameters": {"lines": False, "orient": "records"}
    },
    "jsonl": {
        "extensions": [".jsonl", ".ndjson"],
        "method": "read_json",
        "parameters": {"lines": True,"orient": "records"}
    },
    "xml": {
        "extensions": [".xml"],
        "method": "read_xml"
    },
    "web": {
        "extensions": [".html", ".htm"],
        "method": "read_html"
    }
}


class DataLoader:
    def __init__(self):
        df = None
        self.schema = {}
        self.nulls = {}

    def _is_number(self, val):
        try:
            float(val)
            return True
        except (ValueError, TypeError):
            return False

    def _detect_header(self, file_path, sep=","):
        """Say whether a text file has a header row"""
        try:
            sample = pd.read_csv(file_path, sep=sep, nrows=5, header=None, dtype=str)
            first_row = sample.iloc[0].tolist()
            second_row = sample.iloc[1].tolist() if len(sample) > 1 else []
            
            # types consistency check
            first_is_num = sum(self._is_number(v) for v in first_row)
            second_is_num = sum(self._is_number(v) for v in second_row)
            # strong difference then likely header
            dtype_shift = second_is_num > first_is_num * 2 

            # uniqueness & pattern check: check if most values in the first row look like identifiers
            unique_ratio = len(set(first_row)) / len(first_row)
            identifier_like = sum(bool(re.match(r"^[A-Za-z_][A-Za-z0-9_ ]*$", str(v))) for v in first_row)
            id_ratio = identifier_like / len(first_row)

            # repetition test
            repeated = any(val in second_row for val in first_row)

            # decision
            if dtype_shift and unique_ratio > 0.8 and id_ratio > 0.5 and not repeated:
                return 0
            return None
        except Exception:
            return 0 

    
    def load(self, file_path: str, table:str=None, query:str=None):
        """Load data based on file extension"""
        if file_path.startswith(
            ("postgresql://", "mysql://", "sqlite://", "mssql+pyodbc://")):
            engine = sqlalchemy.create_engine(file_path)
            if query:
                df = pd.read_sql(query, engine)
            elif table:
                df = pd.read_sql(f"SELECT * FROM {table}", engine)
            else:
                raise ValueError(
                    "Specify either table or query when connecting to a database."
                )
            engine.dispose()
            return df
        ext = "." + file_path.split(".")[-1].lower()
        for value in exts.values():
            if ext in value["extensions"]:
                method = value["method"]
                params = value.get("parameters", {}).copy()

                if ext in [".csv", ".tsv", ".txt"]:
                    header_value = self._detect_header(file_path)
                    if header_value is not None:
                        params["header"] = header_value
                    
                df = getattr(pd, method)(file_path, **params)

        return df

    def standardize_nulls(self, df: pd.DataFrame):
        """

        """
        null_values = [None, np.nan, pd.NA, "", " ", "null", "NaN", "N/A", "na", "--", "?", "unknown",  "missing", "None", "#VALUE!"]

        string_nulls = {str(v).lower() for v in null_values if v is not None}

        for column in df.columns:
            col_data = df[column]

            # convert everything to str for comparison
            col_as_str = col_data.astype("object").astype(str).str.strip().str.lower()

            # build mask: match normalized string nulls OR real NaNs
            mask = col_as_str.isin(string_nulls) | col_data.isna()
            
            # construct the nulls dict

            if column not in self.nulls:
                self.nulls[column] = {}
            
            self.nulls[column]["n°nulls"] = int(mask.sum())

            df.loc[mask, column] = np.nan

        return df, df.isna().sum()