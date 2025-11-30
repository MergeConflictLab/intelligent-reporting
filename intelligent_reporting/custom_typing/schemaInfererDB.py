import polars as pl
import os
from datetime import datetime
import json

class schemaInfererDB:
    def __init__(self):
        self.schema = {}

    def _compute_stats(self, s: pl.Series):
        """generate a dict containing the general stats of a column"""
        cleaned = s.drop_nulls()

        null_values = s.null_count()
        distinct_count = cleaned.n_unique()

        mean_length = (
            cleaned.str.len_chars().mean()
            if s.dtype == pl.Utf8
            else None
        )

        return {
            "null_values": null_values,
            "distinct_count": distinct_count,
            "unique_ratio": distinct_count / len(s) if len(s) else 0,
            "missing_ratio": null_values / len(s) if len(s) else 0,
            "mean_length": mean_length,
            "is_constant": distinct_count == 1,
            "is_identifier": distinct_count == len(s),
        }
    
    @staticmethod
    def _to_serializable(obj):
        """
        Convert NumPy / pandas / non-serializable types to JSON-safe values
        """
        if hasattr(obj, "item"):
            return obj.item()
        if isinstance(obj, set):
            return list(obj)
        return str(obj)
    
    def dump_schema(self, df: pl.DataFrame, schema_dir: str):
        """
        Take the polars Dataframe and dumps its schema in a schema_dir
        """
        # ensure output directory exists
        os.makedirs(schema_dir, exist_ok=True)
        
        self.schema.setdefault("num_rows", df.height)
        self.schema.setdefault("num_cols", df.width)
        self.schema.setdefault("memory_usage_mb", float(round(df.estimated_size() / 1024**2, 2)))
        self.schema.setdefault("columns", {})
        for col in df.columns:
            stats = self._compute_stats(df[col])
            self.schema["columns"][col] = {
                    "name": col,
                    "inferred_type": df[col].dtype,
                    "confidence": "100%",
                    "invalid_conversions": 0,
                    "null_values": stats['null_values'],
                    "distinct_count": stats['distinct_count'],
                    "unique_ratio": f"{ stats['unique_ratio'] * 100:.2f}%",
                    "missing_ratio": f"{stats['missing_ratio'] * 100:.2f}%",
                    "mean_length": (
                        f"{stats['mean_length']:.2f}" if stats["mean_length"] is not None else None
                    ),
                    "is_constant": stats["is_constant"],
                    "is_identifier": stats["is_identifier"]
                }
        # extract base filename without extension
        base_name = "schema-"+ datetime.now().strftime("%Y-%m-%d %H-%M-%S")


        # make full schema file path
        schema_file = os.path.join(schema_dir, f"{base_name}.json")


        # write the json file
        with open(schema_file, "w", encoding="utf-8") as f:
            json.dump(self.schema, f, indent=4, default=self._to_serializable, ensure_ascii=False)


        print(f"Schema saved to: {schema_file}")
        return schema_file