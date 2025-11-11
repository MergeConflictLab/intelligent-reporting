import pandas as pd
import os
import xml.etree.ElementTree as ET

FOLDER_PATH = "./data/"
def read_all_file_name_from_folder(folder_path):
    all_files = []

    for root, dirs, files in os.walk(folder_path):
        for file in files:
            path = os.path.join(root, file)
            all_files.append(path)
    return all_files 
def load_file(path):
    if path.endswith(".csv"):
        return pd.read_csv(path)
    elif path.endswith(".json"):
        return pd.read_json(path)
    elif path.endswith(".xlsx") or path.endswith(".xls"):
        return pd.read_excel(path)
    elif path.endswith(".txt"):
        return pd.read_csv(path, sep=",", engine="python", error_bad_lines=False)
    elif path.endswith(".xml"):
        tree = ET.parse(path)
        root = tree.getroot()
        rows = []
        for child in root:
            row = {elem.tag: elem.text for elem in child}
            rows.append(row)
        return pd.DataFrame(rows)
    else:
        raise ValueError("Unsupported file")
m={}
ind=0
# Transform json dataframe -> transform all type to primitive type and transform table structure to a more readable table
def help_deep_smart_flatten(data, new_key):
    global m
    global ind
    if(data is None):
       if(new_key not in m):
          m[new_key]=[]
       while(len(m[new_key])<=ind):
           m[new_key].append(None)   
       m[new_key].append(None)
       return
    _type = type(data)
    if(isinstance(data, list)):
       for index, value in enumerate(data):
           help_deep_smart_flatten(value, new_key+"###"+str(index))
       return 
    if(isinstance(data, int) or 
       isinstance(data, float) or 
       isinstance(data, bool) or 
       isinstance(data, str) or
       isinstance(data, bytes)):
       if(new_key not in m):
           m[new_key]=[]
       while(len(m[new_key])<ind):
           m[new_key].append(None)    
       m[new_key].append(data)
       return
    for key in data:
        help_deep_smart_flatten(data[key], new_key+"###"+str(key))
def deep_smart_flatten(df):
    global m  
    global ind
    global mx
    m.clear()
    ind=0
    for index, row in df.iterrows():
        for col in df.columns:
            help_deep_smart_flatten(row[col], col)
        ind+=1 
    print(ind)
    for key in m:
       while(len(m[key])<ind):
           m[key].append(None) 
       
    result=[{} for _ in range(ind)]
    for new_ind in range(ind):
        for key in m:
            new_key = key.split("###")
            if(len(new_key)==0):
                continue
            new_key = '_'.join(new_key[-2:])  
            result[new_ind][new_key]=m[key][new_ind]
    return pd.json_normalize(result)          