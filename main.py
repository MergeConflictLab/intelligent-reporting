from intelligent_reporting.loading.CSVLoader import CSVLoader
from intelligent_reporting.loading.ParquerLoader import ParquetLoader
from dotenv import load_dotenv
import json
import os     

# -------------------- CSVLoader tester-----------------------#
csvfile = "data_file/sample.csv"
loader = CSVLoader()

gen = loader.load(csvfile, 5000)

for chunk in gen:
    print(chunk.head(5))

# -------------------- ParquetLoader tester ------------------# 
parquetfile= "data.parquet"

loader = ParquetLoader()

gen = loader.load(parquetfile, chunksize=1000)

for chunk in gen:
    print(chunk.describe())
