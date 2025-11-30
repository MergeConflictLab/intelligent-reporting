from loading import *
from custom_typing import *
import time


class pipeline:
    
    DB_SCHEMES = [
        "postgresql", "mysql", "mariadb", "sqlite", "oracle",
        "mssql", "snowflake"
    ]

    # def select_loader(self, source: str):
        # if source.endswith((".csv", ".txt", ".tsv")):
        #     return pipeline.LOADERS["csv"]
        # elif source.endswith(".json"):
        #     return pipeline.LOADERS["json"]
        # elif source.endswith((".parquet", ".pq")):
        #     return pipeline.LOADERS["parquet"]
        # elif source.endswith(".xml"):
        #     return pipeline.LOADERS["xml"]
        # parsed = urlparse(source)
        # if parsed.scheme.lower() in self.DB_SCHEMES:
        #     return pipeline.LOADERS["db"]
        # else:
        #     raise ValueError(f"No loader found for {source}")
    def select_loader_inferer(self, source: str):
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


start = time.perf_counter()
pip = pipeline()
pip.run(db_url="snowflake://NAOUARELB:Naouar2002ensah$@bxbmyrn-yy31127/INSURANCE_CSV/public?warehouse=COMPUTE_WH&role=ACCOUNTADMIN",db_table="insurance_table")
latency = time.perf_counter() - start
print(f"Latency: {latency:.6f} seconds")

# snowflake://NAOUARELB:Naouar2002ensah$@bxbmyrn-yy31127/INSURANCE_CSV/public?warehouse=COMPUTE_WH&role=ACCOUNTADMIN
