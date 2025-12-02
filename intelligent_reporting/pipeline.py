from loading import *
from profiling import *
#from agents import *

from custom_typing import *
import time


#temp
from agents.metadata_agent import metadata_query
from scripts.script import load_data, get_schema, describe_schema, clean_dataframe
from agents.insights_agent import insights_query
from scripts.utils import strip_code_fence, encode_image
import json


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

            #temp
            import polars as pl
            df = pl.read_csv('intelligent_reporting/data/cleaned_salad_data.csv')
            #temp
        
        #profiling & profiling

        sampler = DataSampler(df=df, max_rows=4, output_path = "EDA_output/sample.json")
        summarizer = DataSummarizer(df=df, output_dir="EDA_output", figures_dir='figures')
        visualizer = DataVisualizer(df=df, output_dir="EDA_output", figures_dir="figures",top_k_categories=5)
        correlater = DataCorrelater(df=df, result_dir="EDA_output")


        #temp
        df = load_data(source='intelligent_reporting/data/cleaned_salad_data.csv')
        df = clean_dataframe(df)
        schema = get_schema(df)
        description = describe_schema(df)
        #tamp




        sample = sampler.run_sample()
        print(sample)
        summarizer.summary()
        visualizer.run_viz()
        correlater.run()

        #agents
        
        raw_response = metadata_query(
        #model="deepseek-v3.1:671b-cloud",
        model = 'qwen3-vl:235b-cloud',

        sample_data=sample,
        schema=schema,
        description=description,
    )

        response = strip_code_fence(raw_response)
        print('response',response)
        try:
            metadata = json.loads(response)
        except:
            metadata = {"table_description": response, "columns": []}




start = time.perf_counter()
pip = pipeline()
pip.run(file='intelligent_reporting/data/cleaned_salad_data.csv')

latency = time.perf_counter() - start

print(f"Latency: {latency:.6f} seconds")

# snowflake://NAOUARELB:Naouar2002ensah$@bxbmyrn-yy31127/INSURANCE_CSV/public?warehouse=COMPUTE_WH&role=ACCOUNTADMIN
