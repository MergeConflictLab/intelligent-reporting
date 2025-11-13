from utils import FOLDER_PATH, read_all_file_name_from_folder, load_file, deep_smart_flatten_json
data_flow_paths=read_all_file_name_from_folder(FOLDER_PATH)
for path in data_flow_paths: 
    df=load_file(path)
    file_extension=path.split(".")[-1].lower() 
    result=None
    if(file_extension=="json"):   
       result = deep_smart_flatten_json(df)
    elif(file_extension in ["csv", "xml"]): 
       result = df