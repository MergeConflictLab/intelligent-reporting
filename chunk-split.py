import polars as pl
from pathlib import Path
import ijson

OUTPUT_PATH="./output/"
CHUNK_SIZE=1000
def csvSplitToChunks(path):
    global CHUNK_SIZE
    global OUTPUT_PATH
    scan = pl.scan_csv(path)
    total_rows = scan.select(pl.len()).collect().item()
    offset = 0
    while offset < total_rows:
        df = scan.slice(offset, CHUNK_SIZE).collect()
        df.write_csv(f"{OUTPUT_PATH}csv/file{offset+CHUNK_SIZE}.csv")
        offset += CHUNK_SIZE

# Need optimisations
def jsonSPlitToChunks(path):
    global CHUNK_SIZE
    global OUTPUT_PATH
    content_value=""
    counter=0
    content_values=[]
    offset=0
    with open(path, "r") as f:
        while True:
            chunk = f.read(1_000_000)
            if not chunk:   # end of file
                break
            for _char in chunk:
                if(_char=='{'):
                   counter+=1
                elif(_char=='}'):
                   counter-=1 
                if(counter==0):
                   if(content_value!=""):
                      content_values.append(content_value+_char)
                      if(len(content_values)>=CHUNK_SIZE):
                         folder_path=f"{OUTPUT_PATH}json/"
                         file_path=f"file{offset+CHUNK_SIZE}.json"
                         with open(folder_path+file_path, 'w') as out:
                            out.write("[")
                            for i  in range(len(content_values)):
                                obj = content_values[i]
                                if(i==len(content_values)-1):
                                   out.write(obj + "\n")
                                else:
                                   out.write(obj + "\n,")
                            out.write("]")    
                         content_values=[]     
                         offset+=CHUNK_SIZE     
                      content_value=""
                else:
                   content_value+=_char  
            if(len(content_values)!=0):  
               folder_path=f"{OUTPUT_PATH}json/"
               file_path=f"file{offset+CHUNK_SIZE}.json"
               with open(folder_path+file_path, 'w') as out:            
                    out.write("[")
                    for i  in range(len(content_values)):
                        obj = content_values[i]
                        if(i==len(content_values)-1):
                           out.write(obj + "\n")
                        else:
                           out.write(obj + "\n,")
                    out.write("]")        
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
    