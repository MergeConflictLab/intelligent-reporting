from typing import Tuple, Optional
from urllib.parse import urlparse
import polars as pl
from intelligent_reporting.loading import *
from intelligent_reporting.profiling import *
from intelligent_reporting.custom_typing import *


DB_SCHEMES = [
    "postgresql", "mysql", "mariadb", "sqlite",
    "oracle", "mssql", "snowflake"
]


class DataPipelineSelector:
    """
    Selects the appropriate loader + schema inferer for files or DB connections.
    """

    def __init__(self, *, file: str = None, db_url: str = None,db_table: str = None):
        if file and db_table and not db_url:
            raise ValueError("Cannot provide db_table without db_url")

        if file and db_url:
            raise ValueError("Provide either a file OR a db_url, not both")

        self.file = file
        self.db_url = db_url
        self.db_table = db_table

    # ----------------------------------------------
    # FILE MODE: Determine loader/inferer by extension
    # ----------------------------------------------
    def select_loader_inferer(self):
        """
        Choose loader + schema inferer based on file extension.
        """
        if self.file :
            if self.file.endswith((".csv", ".txt", ".tsv")):
                return CSVLoader, SchemaInfererFlatFiles

            if self.file.endswith(".json"):
                return JsonLoader, SchemaInfererFlatFiles

            if self.file.endswith((".parquet", ".pq")):
                return ParquetLoader, SchemaInfererFlatFiles

            if self.file.endswith(".xml"):
                return XmlLoader, SchemaInfererFlatFiles
        if self.db_url :
            return DBLoader, SchemaInfererDB

        raise ValueError(f"No loader found for file type: {self.file}")

    # ----------------------------------------------
    # MAIN ENTRYPOINT
    # ----------------------------------------------
    def run(self) -> Tuple["pl.DataFrame", Optional[dict]]:
        """
        Generic data pipeline for loading + schema inference.

        Returns:
            (df, schema)
            schema is None for DB mode.
        """
        # --------------------------
        # DATABASE MODE
        # --------------------------
        if self.db_url:
            scheme = urlparse(self.db_url).scheme

            if scheme not in DB_SCHEMES:
                raise ValueError(f"Unsupported DB scheme: {scheme}")

            if not self.db_table:
                raise ValueError("Table name must be provided for DB loading")

            loader = DBLoader(db_url=self.db_url)
            inferer = SchemaInfererDB()

            df = loader.load(table=self.db_table)

            # No schema inference for DB
            schema = inferer.dump_schema(df=df, schema_dir="./results/schema")

            return df, schema

        # --------------------------
        # FILE MODE
        # --------------------------
        if self.file:
            LoaderClass, InfererClass = self.select_loader_inferer()

            loader = LoaderClass()
            inferer = InfererClass()

            df = loader.load(file_path=self.file)

            df, schema = inferer.infer_schema(df)

            inferer.dump_schema(schema=schema, schema_dir="./results/schema")

            return df, schema

        raise ValueError("You must provide either a file or a db_url.")