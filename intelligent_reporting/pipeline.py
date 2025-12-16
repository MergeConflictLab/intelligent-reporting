"""
High-level orchestration pipeline.
"""
import polars as pl
from .orchestrator.selector import Selector
from .core.decorator import measure_latency
from .expection import *
import sys


class Pipeline:
    """
    High-level orchestration pipeline.
    Owns execution lifecycle and delegates data loading.
    """
    def __init__(
            self, 
            *, 
            file: str | None = None, 
            db_url: str | None = None, 
        ):
        """Initialize pipeline with file path or database URL"""
        self.file = file
        self.db_url = db_url
        


    def _load_data(self, **options):
        """Load raw data using the appropriate connector"""
        selector = Selector(
            file=self.file,
            db_url=self.db_url,
        )
        df = selector.get_data(**options)       
        return df
    
    def _get_schema(self, *, data: pl.DataFrame, schema_dir: str|None = None):
        """Infer or load schema for the given dataframe"""
        selector = Selector(
            file=self.file,
            db_url=self.db_url,
        )
        data, schema = selector.get_schema(data=data, schema_dir=schema_dir)
        return data, schema
    
    def _get_downcaster(self, data: str):
        """Apply type downcasting to reduce memory usage"""
        selector = Selector(
            file=self.file,
            db_url=self.db_url,
        )
        df = selector._get_downcaster(data=data)
        return df

    @measure_latency
    def load(self, **options):
        """Public API to load data with error handling"""
        try:
            return self._load_data(**options)
        except ReportingException as e:
            print(f"[ERROR] {e}", file=sys.stderr)
            sys.exit(1)
        except Exception:
            import traceback
            print("[FATAL] Unexpected error occurred", file=sys.stderr)
            traceback.print_exc()
            sys.exit(2)

    @measure_latency        
    def infer(self, **options):
        """Infer schema from an existing dataframe"""
        if "data" not in options.keys():
            raise ConfigurationError(
                "The dataframe (data) must be provided"
            )
        data = options["data"]
        if "schema_dir" not in options.keys():
            schema_dir = "schema"
        else :
            schema_dir = options["schema_dir"]

        try:
            return self._get_schema(data=data, schema_dir=schema_dir)
        except ReportingException as e:
            print(f"[ERROR] {e}", file=sys.stderr)
            sys.exit(1)
        except Exception:
            import traceback
            print("[FATAL] Unexpected error occurred", file=sys.stderr)
            traceback.print_exc()
            sys.exit(2)

    @measure_latency
    def downcast(self, **options):
        """Downcast dataframe column types"""
        if "data" not in options.keys():
            raise ConfigurationError(
                "The dataframe (data) must be provided"
            )
        data = options["data"]
        try:
            return self._get_downcaster(data=data)
        except ReportingException as e:
            print(f"[ERROR] {e}", file=sys.stderr)
            sys.exit(1)
        except Exception:
            import traceback
            print("[FATAL] Unexpected error occurred", file=sys.stderr)
            traceback.print_exc()
            sys.exit(2)
