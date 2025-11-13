from intelligent_reporting.loading.dataLoader import DataLoader
from intelligent_reporting.profiling.schemaInferer import SchemaInferer
from datetime import datetime
import json
#from ydata_profiling import ProfileReport
#import pandas_datatypes
from pandas.api.types import infer_dtype

loader = DataLoader()
df = loader.load(file_path="mssql+pyodbc://@localhost\\SQLEXPRESS/anissa?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes",
        table="Reviews")

df, nulls_report = loader.standardize_nulls(df)

# inferer = SchemaInferer()
# schema, df = inferer.infer_schema(df)

# inferer.dump_schema(schema, f"data_file/schema_{datetime.now()}.csv", "schema_output/schema")

# profile = ProfileReport(df, minimal=True, infer_dtypes=True)
# schema_summary = profile.get_description()
# profile.to_file("schema_output/ydata_profiling/summary.json")

for column in df.columns :
    type=infer_dtype(df[column])
    print(f"{column} is {type}")
