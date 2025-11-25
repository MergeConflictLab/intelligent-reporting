import polars as pl
import math
from pathlib import Path

OUTPUT_PATH="./output/"
CHUNK_SIZE=5000
def csvSplitToChunks(path):
    global CHUNK_SIZE
    global OUTPUT_PATH
    scan = pl.scan_csv(path)
    total_rows = scan.select(pl.len()).collect().item()
    offset = 0
    while offset < total_rows:
        df = scan.slice(offset, CHUNK_SIZE).collect()
        df.write_csv(f"{OUTPUT_PATH}/csv/file{offset+CHUNK_SIZE}.csv")
        offset += CHUNK_SIZE

def jsonSPlitToChunks(path):
    global CHUNK_SIZE
    global OUTPUT_PATH
    pass

folder = Path("./data")

for file in folder.iterdir():
    if file.is_file():
       file_extension = file.suffix.lower()
       if(file_extension==".csv"):
          csvSplitToChunks(file)
       elif(file_extension==".json"):
         jsonSPlitToChunks(file)
       elif(file_extension==".xml"):
          pass
    