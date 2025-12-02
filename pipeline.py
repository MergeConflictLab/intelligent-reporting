from intelligent_reporting.loading import *
from intelligent_reporting.custom_typing import *


class pipeline:
    
    DB_SCHEMES = [
        "postgresql", "mysql", "mariadb", "sqlite", "oracle",
        "mssql", "snowflake"
    ]

    def select_loader_inferer(self, source: str):
        """
        Select loader based on data source
        """
        if source.endswith((".csv", ".txt", ".tsv")):
            return CSVLoader, SchemaInfererFlatFiles
        elif source.endswith(".json"):
            return JsonLoader, SchemaInfererFlatFiles
        elif source.endswith((".parquet", ".pq")):
            return ParquetLoader, SchemaInfererFlatFiles
        elif source.endswith(".xml"):
            return XmlLoader, SchemaInfererFlatFiles

        raise ValueError(f"No loader found for {source}")


    def run(self, *,file: str = None, db_url: str = None, db_table: str = None):
        """
        Generic data pipeline that can load from flat files or databases.
        
        Provide either:
            - source=<filepath>
        OR:
            - db_url=<URL> and db_table=<table>
        """
        if file and db_table and not db_url:
            raise ValueError("Cannot provide db_table without db_url")
        
        if file and db_url:
            raise ValueError("Provide either a file 'source' OR 'db_url', not both")
        
        # --- DB MODE ---------------------------------------------------------
        if db_url:
            loader = DBLoader(db_url=db_url)
            inferer = schemaInfererDB()

            table_name = db_table

            if not table_name:
                raise ValueError("Table name must be provided for DB loading")

            df = loader.load(table=table_name)

            # NO SCHEMA INFERENCE FOR DB
            inferer.dump_schema(df=df, schema_dir="./DB_schema")

        # --- File MODE -------------------------------------------------------
        if file:
            LoaderClass, infererClass = self.select_loader_inferer(source=file)
            loader = LoaderClass()
            inferer = infererClass()
            
            df = loader.load(file_path=file)

            # schema inference
            df, schema = inferer.infer_schema(df)
            inferer.dump_schema(schema=schema, schema_dir="./schema")



