import polars as pl
from pathlib import Path
import os

OUTPUT_PATH="./output/"
CHUNK_SIZE=1000

def createOutputFolders():
   os.makedirs(f"{OUTPUT_PATH}csv/", exist_ok=True)
   os.makedirs(f"{OUTPUT_PATH}json/", exist_ok=True)
   os.makedirs(f"{OUTPUT_PATH}jsonl/", exist_ok=True)
   os.makedirs(f"{OUTPUT_PATH}xml/", exist_ok=True)
   os.makedirs(f"{OUTPUT_PATH}parquet/", exist_ok=True)

def csvSplitToChunks(path):
    scan = pl.scan_csv(path)
    total_rows = scan.select(pl.len()).collect().item()
    offset = 0
    while offset < total_rows:
        df = scan.slice(offset, CHUNK_SIZE).collect()
        df.write_csv(f"{OUTPUT_PATH}csv/chunk{offset+CHUNK_SIZE}.csv")
        offset += CHUNK_SIZE

# Format accepted [{}, {}, ..., {}]                
def jsonSPlitToChunks(path):
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
                         file_path=f"chunk{offset+CHUNK_SIZE}.json"
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
               if(index_i==0 and index_j>=len(chunk)):
                  content_value.append(chunk)
               else:   
                  content_value.append(chunk[index_i:index_j])
        if(len(content_values)!=0):
           folder_path=f"{OUTPUT_PATH}json/"
           file_path=f"chunk{offset+CHUNK_SIZE}.json"
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

def jsonlSplitToChunks(path):
   scan = pl.scan_ndjson(path)
   total_rows = scan.select(pl.len()).collect().item()   
   offset=0
   while offset < total_rows:
      df = scan.slice(offset, CHUNK_SIZE).collect()
      folder_path=f"{OUTPUT_PATH}jsonl/"
      file_path=f"chunk{offset+CHUNK_SIZE}.jsonl"
      df.write_ndjson(folder_path+file_path)
      offset+=CHUNK_SIZE

def xmlFindRootObject(path):
   result = []
   counter = 0
   with open(path, "r") as f:
      chunk = f.read(10000)
      index1 = chunk.find("<")
      if(index1==-1): 
         return [None, None]
      index2 = chunk.find(">")
      fatherRoot = chunk[index1:index2+1]
      index1 = chunk.find("<", index2+1)
      index2 = chunk.find(">", index2+1)
      sonRoot = chunk[index1:index2+1] 
      return [fatherRoot, sonRoot]

def xmlSplitToChunks(path):
    content_values = []
    result = xmlFindRootObject(path)
    if(result[0] is None):
       raise ValueError("The file is empty")
    begin = result[1]
    end = result[1][0]+"/"+result[1][1:]
    offset = 0
    with open(path, "r") as f:
       while True:
          chunk = f.read(1_000_000)
          if not chunk:   # end of file
                break
          index1=0
          index2=0
          while(True):
            index1=chunk.find(begin, index1)
            if(index1==-1):
               break
            index2=chunk.find(end, index1+1)
            if(index2==-1):
                  break
            content_values.append(chunk[index1:index2]+end+"\n")
            if(len(content_values)>=CHUNK_SIZE):
               folder_path=f"{OUTPUT_PATH}xml/"
               file_path=f"chunk{offset+CHUNK_SIZE}.xml"
               with open(folder_path+file_path, 'w') as out:
                  out.write(result[0]+"\n")
                  for content_value in content_values:
                      out.write(content_value)
                  out.write(result[0][0]+"/"+result[0][1:]+"\n")  
               content_values = []     
               offset+=CHUNK_SIZE
            index1=index2+len(end)

       if(len(content_values)!=0):
         folder_path=f"{OUTPUT_PATH}xml/"
         file_path=f"chunk{offset+CHUNK_SIZE}.xml"
         with open(folder_path+file_path, 'w') as out:
            out.write(result[0]+"\n")
            for content_value in content_values:
                out.write(content_value)
            out.write(result[0][0]+"/"+result[0][1:]+"\n")          

def parquetSplitToChunks(path):
   scan = pl.scan_parquet(path)
   total_rows = scan.select(pl.len()).collect().item()
   offset = 0
   while offset < total_rows:
      df = scan.slice(offset, CHUNK_SIZE).collect()
      folder_path=f"{OUTPUT_PATH}parquet/"
      file_path=f"chunk{offset+CHUNK_SIZE}.parquet"
      df.write_parquet(folder_path+file_path)
      offset+=CHUNK_SIZE
      
folder = Path("./data")

createOutputFolders()

for file in folder.iterdir():  
    if file.is_file():
       file_extension = file.suffix.lower()
       if(file_extension==".csv"):
         csvSplitToChunks(file)
       elif(file_extension==".json"):
         jsonSPlitToChunks(file)
       elif(file_extension==".jsonl"):
         jsonlSplitToChunks(file)  
       elif(file_extension==".xml"):
          xmlSplitToChunks(file)
       elif(file_extension==".parquet"):
          parquetSplitToChunks(file)
       else:
          print(f"{file_extension} extension not supported")   