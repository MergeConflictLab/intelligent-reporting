import polars as pl
from intelligent_reporting.connectors import registry
from intelligent_reporting.custom_typing import *
from urllib.parse import urlparse
from ..expection import *

DB_SCHEMES = [
    "postgresql", "mysql", "mariadb", "sqlite",
    "oracle", "mssql", "snowflake"
]


class Selector:
    """
    Tiny orchestrator:
    - validates inputs
    - picks the correct connector from the registry
    - runs `load`, `infer` and `downcast` and returns a Polars DataFrame object and its schema
    """

    def __init__(self, *, file: str = None, db_url: str = None):
        if file and db_url:
            raise ConfigurationError(
                "Cannot provide both the data source (file) and the conectiong string (db_url)"
            )

        if file and db_url:
            raise ConfigurationError(
                "Provide either a file OR a db_url, not both"
            )

        self.file = file
        self.db_url = db_url


    # --- loading ---
    def _run_db_mode(self, table: str | None = None) -> pl.DataFrame:
        scheme = urlparse(self.db_url).scheme

        if scheme not in DB_SCHEMES:
            raise ConfigurationError(
                f"Unsupported DB scheme: {scheme}. "
                f"Supported schemes: {', '.join(DB_SCHEMES)}"
            )
        
        if not table:
            raise ConfigurationError(
                "Table name must be provided when using db_url"
            )

        loader = registry.get_db_connector(db_url=self.db_url)
        return loader.load(table=table)


    def _run_file_mode(self, **options) -> pl.DataFrame:
        loader = registry.get_file_connector(self.file)
        return loader.load(**options)
    

    def get_data(self, **options) -> pl.DataFrame:
        if self.db_url:
            table = options.get("table")
            self._df = self._run_db_mode(table=table)
            return self._df

        if self.file:
            self._df = self._run_file_mode(**options)
            return self._df

        raise ConfigurationError(
            "You must provide either a file path or a database URL"
        )
    
    
    # --- schema ---
    def _schema_db_mode(self, *, data: pl.DataFrame, schema_dir: str):
        inferer = SchemaInfererDB()
        return inferer.infer_schema(df=data, schema_dir=schema_dir)

    def _schema_file_mode(self, *,data= pl.DataFrame, schema_dir: str):
        inferer = SchemaInfererFlatFiles()
        return inferer.infer_schema(df=data, schema_dir=schema_dir)

    
    def get_schema(self, *,data: pl.DataFrame, schema_dir: str):
        if self.db_url:
            return self._schema_db_mode(data=data, schema_dir=schema_dir)

        if self.file:
            return self._schema_file_mode(data=data, schema_dir=schema_dir)

        raise ConfigurationError(
            "You must provide either a file path or a database URL"
        )
    
    # --- downcast
    def _get_downcaster(self, data: str):
        downcaster = DownCaster()
        return downcaster.optimize(df=data)