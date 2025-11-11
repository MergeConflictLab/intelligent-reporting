import pandas as pd
import json
import warnings
import os

class SchemaInferer():

    def __init__(self):
        self.schema = {}
        self.nulls = {}

                 
    def _infer_column_type(self, series: pd.Series):
        """
        Determine the column's data type ratios.
        """

        s = series.dropna()
        total = s.size
        if total == 0:
            return "No data"
        
        # boolean
        if s.dtype == object:
            bool_like = s.astype(str).str.lower().isin(["true", "false", "yes", "no", "0", "1"])
            bool_ratio = bool_like.mean()
        else:
            bool_like = pd.Series(False, index=s.index)
            bool_ratio = 0.0

        # categorical
        unique_ratio = s.nunique() / total
        if unique_ratio < 0.3 :
            category_ratio = 1

        # numeric
        elif pd.api.types.is_numeric_dtype(s):
            numeric_mask = pd.Series(True, index=s.index)
            numeric_ratio = 1.0
        else:
            numeric_mask = pd.to_numeric(s, errors="coerce").notna()
            numeric_ratio = numeric_mask.mean()

        # datetime
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            datetime_mask = pd.to_datetime(s, errors="coerce").notna()
        datetime_ratio = datetime_mask.mean()

        # everything else then string
        non_string_mask = numeric_mask | datetime_mask | bool_like
        string_ratio = 1 - non_string_mask.mean()

        return {
            "numeric": float(numeric_ratio),
            "datetime": float(datetime_ratio),
            "boolean": float(bool_ratio),
            "categorical": float(category_ratio),
            "string": float(string_ratio)
        }

    def _decide_type(self, ratios: dict):
        """
        Decide final inferred type based on ratio thresholds.
        ratios = {
            "numeric": ...,
            "datetime": ...,
            "boolean": ...,
            "categorical": ...,
            "string": ...
        }
        """
        # Define thresholds
        THRESH_NUMERIC = 0.9
        THRESH_DATETIME = 0.8
        THRESH_BOOLEAN = 0.8
        THRESH_STRING = 0.8

        # Priority order: numeric > datetime > boolean > categorical > string
        if ratios["numeric"] >= THRESH_NUMERIC:
            return "numeric", ratios["numeric"]
        

        if ratios["datetime"] >= THRESH_DATETIME:
            return "datetime", ratios["datetime"]

        if ratios["boolean"] >= THRESH_BOOLEAN:
            return "boolean", ratios["boolean"]

        if ratios["string"] >= THRESH_STRING:
            # if many strings but low unique ratio then categorical
            if ratios["categorical"] < 0.05:
                return "categorical", 1 - ratios["categorical"]
            
            elif ratios["categorical"] < 0.2:
                return "ambiguous", 1 - ratios["categorical"]
            
            else:
                return "string", ratios["string"]

        # mixed data
        return "unknown", max(ratios.values())

    def infer_schema(self, df: pd.DataFrame):
        """
        Infers column types, uniqueness, and missing ratio for each column.
        Returns a structured schema dictionary.
        """
        num_rows = df.shape[0]
        num_cols = df.shape[1]
        memory_usage = round(df.memory_usage(deep=True).sum() / 1024**2, 2)

        self.schema.setdefault("num_rows", num_rows)
        self.schema.setdefault("num_cols", num_cols)
        self.schema.setdefault("memory_usage_mb", float(memory_usage))
        self.schema.setdefault("columns", {})

        for col in df.columns:
            col_data = df[col]

            # --- core type inference ---
            ratios = self._infer_column_type(col_data)
            inferred_type, confidence, notes = self._decide_type(ratios)

            # --- convert column to inferred type & drop invalid ---
            converted = col_data.copy()
            invalid_count = 0

            if inferred_type == "numeric":
                converted = pd.to_numeric(converted, errors="coerce")
                invalid_count = converted.isna().sum() - col_data.isna().sum()

            elif inferred_type == "datetime":
                converted = pd.to_datetime(converted, errors="coerce")
                invalid_count = converted.isna().sum() - col_data.isna().sum()

            elif inferred_type == "boolean":
                converted = converted.astype(str).str.lower().map({
                    "true": True, "1": True, "yes": True,
                    "false": False, "0": False, "no": False
                })
                # mark invalid booleans as NaN
                invalid_count = converted.isna().sum() - col_data.isna().sum()

            # drop invalid (NaN / NaT) rows
            valid_mask = ~converted.isna()
            cleaned_col = converted[valid_mask]

            # --- general stats ---
            null_values = col_data.isna().sum()
            unique_ratio = cleaned_col.nunique(dropna=True) / len(col_data)
            missing_ratio = col_data.isna().mean()
            distinct_count = cleaned_col.nunique(dropna=True)
            sample_values = cleaned_col.dropna().unique()[:5].tolist()

            # --- default stat values ---
            mean_length = None
            min_value = None
            max_value = None
            mean_value = None
            std_value = None

            # --- compute stats based on inferred type ---
            if inferred_type == "string":
                mean_length = cleaned_col.dropna().astype(str).str.len().mean()

            # elif inferred_type == "numeric":
            #     min_value = float(cleaned_col.min(skipna=True))
            #     max_value = float(cleaned_col.max(skipna=True))
            #     mean_value = float(cleaned_col.mean(skipna=True))
            #     std_value = float(cleaned_col.std(skipna=True))

            # elif inferred_type == "datetime":
            #     min_value = cleaned_col.min(skipna=True)
            #     max_value = cleaned_col.max(skipna=True)

            # --- flags ---
            is_constant = distinct_count == 1
            is_identifier = unique_ratio == 1.0

            # --- column schema ---
            self.schema["columns"][col] = {
                "name": col,
                "null_values": int(null_values),
                "invalid_conversions": int(invalid_count),
                "inferred_type": inferred_type,
                "confidence": f"{confidence * 100:.2f}%",
                "unique_ratio": f"{unique_ratio * 100:.2f}%",
                "missing_ratio": f"{missing_ratio * 100:.2f}%",
                "distinct_count": distinct_count,
                "sample_values": sample_values,
                "mean_length": f"{mean_length:.2f}" if mean_length is not None else None,
                # "min_value": str(min_value) if min_value is not None else None,
                # "max_value": str(max_value) if max_value is not None else None,
                # "mean_value": f"{mean_value:.2f}" if mean_value is not None else None,
                # "std_value": f"{std_value:.2f}" if std_value is not None else None,
                "is_constant": is_constant,
                "is_identifier": is_identifier,
                "notes": notes,
            }

        # Optionally return both the schema and cleaned dataframe
        return self.schema, df[[*self.schema["columns"].keys()]]
    
    @staticmethod
    def _to_serializable(obj):
        """Convert NumPy / pandas / non-serializable types to JSON-safe values."""
        if hasattr(obj, "item"):
            return obj.item()
        if isinstance(obj, set):
            return list(obj)
        return str(obj)
    
    def dump_schema(self, schema: dict, data_file_path: str, schema_dir: str):
        """
        dump the inferred schema to a JSON file.
        
        The output file will be named <datafilename>_schema.json inside schema_dir.
        """
        # ensure output directory exists
        os.makedirs(schema_dir, exist_ok=True)

        # extract base filename without extension
        base_name = os.path.splitext(os.path.basename(data_file_path))[0]

        # make full schema file path
        schema_file = os.path.join(schema_dir, f"{base_name}_schema.json")

        # write the json file
        with open(schema_file, "w", encoding="utf-8") as f:
            json.dump(schema, f, indent=4, default=self._to_serializable, ensure_ascii=False)

        print(f"Schema saved to: {schema_file}")
        return schema_file

"""
handle cells that don't obey to the infered schema (probably dump them)
deduplocation
Enhancements:

Advanced type detection (ID, URL, email, categorical vs high-cardinality text)

Semantic type hints (e.g., phone number, zipcode)

Custom flags (e.g., “likely categorical”, “suspicious numeric”)
"""