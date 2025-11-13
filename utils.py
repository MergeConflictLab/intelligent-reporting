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
def walk_in_order(elem, level=0):
    print("  " * level + elem.tag + ": " + (elem.text.strip() if elem.text else ""))
    for child in elem: 
        walk_in_order(child, level + 1)

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
        return deep_smart_flatten_xml(root)
    else:
        raise ValueError("Unsupported file")
m={}
ind=0
def help_deep_smart_flatten_json(data, new_key):
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
           help_deep_smart_flatten_json(value, new_key+"###"+str(index))
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
        help_deep_smart_flatten_json(data[key], new_key+"###"+str(key))
def deep_smart_flatten_json(df):
    global m  
    global ind
    m.clear()
    ind=0
    for index, row in df.iterrows():
        for col in df.columns:
            help_deep_smart_flatten_json(row[col], col)   
        ind+=1    
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
def help_deep_smart_flatten_xml(root, new_key):
    global ind
    if(root.text is None or root.text.strip()!=""):
       if(new_key not in m):
          m[new_key]=[]
       while(len(m[new_key])<ind):
          m[new_key].append(None)
       if(root.text is None):
          m[new_key].append(None)
       else:  
          m[new_key].append(root.text.strip())          
    for child in root:        
        help_deep_smart_flatten_xml(child, new_key+"###"+child.tag)      
def deep_smart_flatten_xml(root):
    global m  
    global ind
    ind=0
    m.clear()        
    for child in root:
        help_deep_smart_flatten_xml(child, child.tag)
        ind+=1 
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