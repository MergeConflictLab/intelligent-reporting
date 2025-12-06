import polars as pl
from datetime import datetime
import os
import json

class SchemaInfererFlatFiles():
    """This class should be responsible of infering the pl.DataFrame object's schema, apply it and generate the schema report."""

    def __init__(self):
       """Constructor"""
       self.schema = {}
       self.nulls = {}


    def _infer_column_type(self, series: pl.Series):
        """Determine the column's data type ratios,
        returns a dictionary with each type and the probability that the column in in that type"""
        s = series.drop_nulls()
        total = len(s)
        if total == 0:
           return "No data"
        def is_integer_dtype(dtype) -> bool:
            return dtype in [pl.Int8, pl.Int16, pl.Int32, pl.Int64]

        def is_float_dtype(dtype) -> bool:
            return dtype in [pl.Float32, pl.Float64]
        
        def is_numeric_dtype(dtype) -> bool:
            return is_integer_dtype(dtype) or is_float_dtype(dtype)
      
        # boolean detection
        def is_boolean_column(s: pl.Series) -> pl.Series:
            """
                Returns:
                    - bool_mask: Series of True/False indicating which values are boolean-like
                    - bool_ratio: fraction of values that are boolean-like (ignoring nulls)
            """            
            if s.dtype == pl.Utf8:
                lowered = s.str.to_lowercase().str.strip_chars()
                valid = ["true", "false", "yes", "no", "0", "1"]
                bool_mask = lowered.is_in(valid)
                if False in bool_mask:
                    bool_mask = pl.Series([False] * s.len())
                    return bool_mask, 0
            
            elif is_numeric_dtype(s.dtype):
                bool_mask = s.is_in([0, 1])
            
            else:
                # for other types, nothing is bool
                bool_mask = pl.Series([False] * s.len())
            
            # ignore nulls when calculating ratio
            not_null_mask = ~s.is_null()
            bool_ratio = (bool_mask & not_null_mask).sum() / not_null_mask.sum() if not_null_mask.sum() > 0 else 0.0
            
            return bool_mask, float(bool_ratio)
        
        bool_mask, bool_ratio = is_boolean_column(s)


        # category detection
        def category_ratio_calc(s: pl.Series) -> float:
            unique_ratio = s.n_unique() / len(s)
            return unique_ratio
        category_ratio = category_ratio_calc(s)
                
        
        
        def int_mask_calc(s: pl.Series) -> pl.Series:
            """
            Returns a mask where True indicates integer-like values
            """
            if is_integer_dtype(s.dtype):
                return pl.Series([True] * len(s))
            elif is_float_dtype(s.dtype):
                # float column: check which values are exact integers
                return (s.fill_null(0) % 1 == 0) & s.is_not_null()
            else:
                # Try casting to float and check for integer values
                numeric_cast = s.cast(pl.Float64, strict=False)
                return (numeric_cast % 1 == 0) & numeric_cast.is_not_null()
        int_mask = int_mask_calc(s)
        int_ratio = int_mask.mean()

        # float
        
        
        
        def float_mask_calc(s: pl.Series, int_mask: pl.Series) -> pl.Series:
            """
            Returns a mask where True indicates float-like values (excluding integers)
            """
            if is_numeric_dtype(s.dtype):
                numeric_mask = s.is_not_null()
            else:
                numeric_cast = s.cast(pl.Float64, strict=False)
                numeric_mask = numeric_cast.is_not_null()
            
            # Remove integer values from float mask
            float_mask = numeric_mask & (~int_mask)
            return float_mask
        float_mask = float_mask_calc(s, int_mask)
        float_ratio = float_mask.mean()


        def parse_datetime_generic(s: pl.Series) -> pl.Series:
            COMMON_DATETIME_FORMATS = [
                "%Y-%m-%d %H:%M:%S",
                "%d-%m-%Y %H:%M:%S",
                "%d/%m/%Y %H:%M:%S",
                "%d %b %Y %H:%M:%S",
                "%d %B %Y %H:%M:%S",
                "%Y-%m-%d",
                "%d-%m-%Y",
                "%m-%d-%Y",
                "%d/%m/%Y",
                "%m/%d/%Y",
            ]

            if s.dtype != pl.Utf8:
                return pl.Series(s.name, [None] * len(s), dtype=pl.Datetime)

            # Try formats
            for fmt in COMMON_DATETIME_FORMATS:
                dt = s.str.strptime(pl.Datetime, format=fmt, strict=False)
                if dt.null_count() < len(s):
                    return dt

            # All formats failed
            return pl.Series(s.name, [None] * len(s), dtype=pl.Datetime)

        # datetime detection
        datetime_cast = parse_datetime_generic(s)
        datetime_mask = datetime_cast.is_not_null()
        datetime_ratio = datetime_mask.mean()


        # everything else then string
        non_string_mask = bool_mask | int_mask | datetime_mask | float_mask
        string_mask = ~non_string_mask
        string_ratio = string_mask.mean()


        return {
            "int": float(int_ratio),
            "float": float(float_ratio),
            "datetime": float(datetime_ratio),
            "boolean": float(bool_ratio),
            "category": 1 - float(category_ratio),
            "string": float(string_ratio)
        }


    def _decide_type(self, ratios: dict):
        """
        Decide final inferred type based on type ratios.
        Takes:
            ratios = {
                "int": ...,
                "float": ...,
                "datetime": ...,
                "boolean": ...,
                "categoricy": ...,
                "string": ...
            }
        Return:
            the infered type and the confidence
        """
        # Define thresholds
        THRESH_BOOLEAN = 0.98
        THRESH_CATEGORY = 0.95
        THRESH_INT = 0.9
        THRESH_FLOAT = 0.9
        THRESH_DATETIME = 0.7

        # Priority order: bool -> category -> int -> float -> datetime -> string -> object
        
        if ratios["boolean"] >= THRESH_BOOLEAN:
            return "Boolean", ratios["boolean"] / (ratios["boolean"] + ratios["string"])

        if ratios["int"] >= THRESH_INT:
            return "Int", ratios["int"]

        if ratios["float"] >= THRESH_FLOAT:
            return "Float", ratios["float"]

        if ratios["datetime"] >= THRESH_DATETIME:
            return "Datetime", ratios["datetime"] / (ratios["datetime"] + ratios["string"])

        # category based on unique-ratio (separately computed)
        if ratios["category"] >= THRESH_CATEGORY:
            return "Category", ratios["category"] / (ratios["category"] + ratios["string"])

        # fallback
        return "String", ratios["string"]


    def _convert_column(self, col_data: pl.Series, inferred_type: str):
        """Actually converts the column into the infered type, drops the invalids"""
        if inferred_type == "Int":
            converted = col_data.cast(pl.Float64).round(0).cast(pl.Int64)

        elif inferred_type == "Float":
            converted = col_data.cast(pl.Float64, strict=False)

        elif inferred_type == "Datetime":
            converted = col_data.str.strptime(
                pl.Datetime,
                format="%Y-%m-%d %H:%M:%S",
                strict=False
            )

        elif inferred_type == "Boolean":
            bool_map = {
                "true": True, "1": True, "yes": True,
                "false": False, "0": False, "no": False
            }

            # Convert a Series safely
            def series_to_boolean(col: pl.Series) -> pl.Series:
                # Ensure it's string and lowercase
                s = col.cast(pl.Utf8).str.to_lowercase()

                # Map values using list comprehension (works in any version)
                return pl.Series([bool_map.get(v, None) for v in s])
            converted = series_to_boolean(col_data)

        else:  # String or any unhandled
            converted = col_data.clone()

        invalid_count = converted.is_null().sum() - col_data.is_null().sum()
        return converted, invalid_count


    def _compute_stats(self, original: pl.Series, converted: pl.Series):
        """generate a dict containing the general stats of a column"""
        cleaned = converted.drop_nulls()

        null_values = original.null_count()
        distinct_count = cleaned.n_unique()

        mean_length = (
            cleaned.str.len_chars().mean()
            if converted.dtype == pl.Utf8
            else None
        )

        return {
            "null_values": null_values,
            "distinct_count": distinct_count,
            "unique_ratio": distinct_count / len(original) if len(original) else 0,
            "missing_ratio": null_values / len(original) if len(original) else 0,
            "mean_length": mean_length,
            "is_constant": distinct_count == 1,
            "is_identifier": distinct_count == len(original),
        }


    def _init_schema_metadata(self, df: pl.DataFrame):
        """Add the first metadata for the schema"""
        self.schema.setdefault("num_rows", df.height)
        self.schema.setdefault("num_cols", df.width)
        self.schema.setdefault("memory_usage_mb", float(round(df.estimated_size() / 1024**2, 2)))
        self.schema.setdefault("columns", {})


    def _build_schema_entry(
            self,
            col: str,
            inferred_type: str,
            confidence: float,
            invalid_count: int,
            stats: dict,
        ):
            """Build schema entry"""
            return {
                "name": col,
                "inferred_type": inferred_type,
                "confidence": f"{confidence * 100:.2f}%",
                "invalid_conversions": invalid_count,

                "null_values": stats["null_values"],
                "distinct_count": stats["distinct_count"],
                "unique_ratio": f"{stats['unique_ratio'] * 100:.2f}%",
                "missing_ratio": f"{stats['missing_ratio'] * 100:.2f}%",
                "mean_length": (
                    f"{stats['mean_length']:.2f}" if stats["mean_length"] is not None else None
                ),
                "is_constant": stats["is_constant"],
                "is_identifier": stats["is_identifier"],
            }


    def _apply_conversions(self, df: pl.DataFrame, converted_cols: dict):
        """Apply conversions to the pl.DataFrame object"""
        return df.with_columns([
            converted_cols[col].alias(col) for col in df.columns
        ])
    

    def infer_schema(self, df: pl.DataFrame):
        """
        Infers column types, uniqueness, and missing ratio for each column.
        Inforce the schema infered to the pl.DataFrame df.
        Returns the actual pl.DataFrame and a structured schema dictionary.
        """
        self._init_schema_metadata(df)

        converted_cols = {}

        for col in df.columns:
            col_data = df[col]

            # 1. infer type
            ratios = self._infer_column_type(col_data)
            inferred_type, confidence = self._decide_type(ratios)

            # 2. convert column
            converted, invalid_count = self._convert_column(col_data, inferred_type)
            converted_cols[col] = converted.alias(col)

            # 3. compute stats
            stats = self._compute_stats(col_data, converted)

            # 4. add schema entry
            self.schema["columns"][col] = self._build_schema_entry(
                col,
                inferred_type,
                confidence,
                invalid_count,
                stats
            )

        # 5. apply conversions
        cleaned_df = self._apply_conversions(df, converted_cols)

        return cleaned_df, self.schema
           
    @staticmethod
    def _to_serializable(obj):
        """Convert NumPy / pandas / non-serializable types to JSON-safe values."""
        if hasattr(obj, "item"):
            return obj.item()
        if isinstance(obj, set):
            return list(obj)
        return str(obj)
    
    def dump_schema(self, *, schema: dict, schema_dir: str):
        """
        Dump the inferred schema to a JSON file.
        The output file will be named schema-yyyy-mm-dd hh-mm-ss.json inside schema_dir.
        """
        # ensure output directory exists
        os.makedirs(schema_dir, exist_ok=True)


        # extract base filename without extension
        base_name = "schema-"+ datetime.now().strftime("%Y-%m-%d %H-%M-%S")


        # make full schema file path
        schema_file = os.path.join(schema_dir, f"{base_name}.json")


        # write the json file
        with open(schema_file, "w", encoding="utf-8") as f:
            json.dump(schema, f, indent=4, default=self._to_serializable, ensure_ascii=False)


        print(f"Schema saved to: {schema_file}")
        return schema_file