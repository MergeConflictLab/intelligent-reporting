from utils import FOLDER_PATH, read_all_file_name_from_folder, load_file, deep_smart_flatten
data_flow_paths=read_all_file_name_from_folder(FOLDER_PATH)
for path in data_flow_paths: 
    df = load_file(path)
    file_extension =path.split(".")[-1] 
    if(file_extension=="json"):   
       result = deep_smart_flatten(df)
       print(result)