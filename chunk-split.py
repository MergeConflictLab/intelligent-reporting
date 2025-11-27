import polars as pl
from pathlib import Path

OUTPUT_PATH="./output/"
CHUNK_SIZE=100000
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

# 1GB of data chunk split in 1 minute still slow and need optimisation
def jsonSPlitToChunks(path):
    global CHUNK_SIZE
    global OUTPUT_PATH
    content_value=[]
    counter=-1
    content_values=[]
    offset=0
    index_i=index_j=0
    with open(path, "r") as f:
        while True:
            index_i=index_j=0
            chunk = f.read(1_000_000)
            if not chunk:   # end of file
                break
            for _char in chunk:
                if(_char=='{'):
                   if(counter==-1):
                      counter=0
                   counter+=1
                elif(_char=='}'):
                   counter-=1 
                index_j+=1  
                if(counter==0):
                   if(index_j-index_i>1):
                      content_value.append(chunk[index_i:index_j])
                      content_values.append("".join(content_value))
                      content_value=[]
                      if(len(content_values)>=CHUNK_SIZE):
                         folder_path=f"{OUTPUT_PATH}json/"
                         file_path=f"file{offset+CHUNK_SIZE}.json"
                         with open(folder_path+file_path, 'w') as out:
                            if(offset!=0):
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
                      index_i=index_j+1
            if(index_j-index_i>1):
               content_value.append(chunk[index_i:index_j])
        if(len(content_values)!=0):
           folder_path=f"{OUTPUT_PATH}json/"
           file_path=f"file{offset+CHUNK_SIZE}.json"
           with open(folder_path+file_path, 'w') as out:
              if(content_values[0][0]!='['):
                 out.write("[") 
              for i in range(len(content_values)):
                    obj = content_values[i]
                    if(i==len(content_values)-1):
                       out.write(obj + "\n")
                    else:
                       out.write(obj + "\n,")
              out.write("]")    
           content_values=[]     

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
    