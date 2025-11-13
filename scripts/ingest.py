from typing import Dict, List
import polars as pl


def get_schema(df: pl.DataFrame) -> Dict[str, str]:
    """Return column -> dtype for a Polars DataFrame."""
    return {name: str(dtype) for name, dtype in df.schema.items()}


def describe_schema(df: pl.DataFrame) -> List[Dict]:
    """Describe each column with dtype, null_count, nullable, and unique_count."""
    out = []
    for col in df.columns:
        s = df[col]
        out.append(
            {
                "name": col,
                "dtype": str(s.dtype),
                "null_count": int(s.is_null().sum()),
                "nullable": bool(s.is_null().sum() > 0),
                "unique_count": int(s.n_unique()),
            }
        )
    return out
