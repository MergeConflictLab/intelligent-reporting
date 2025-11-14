import polars as pl
class JsonLoader:

    def __init__(self):
        self.__rebuild_data_structure={}
        self.__ind=0
        self.__special_separator="###"

    def loadfile(self, file_path):
        """
        Load data from a file_path into a pl.DataFrame
        """
        file_extension=file_path.split(".")[-1].lower() 
        if(file_extension!="json"):
            raise ValueError("The input file must be in JSON format (.json)")
        df = pl.read_json(file_path)   
        return self._deep_smart_flatten_json(df)  
        
    def _help_deep_smart_flatten_json(self, data, new_key):
        if(data is None):
           if(new_key not in self.__rebuild_data_structure):
              self.__rebuild_data_structure[new_key]=[]
           while(len(self.__rebuild_data_structure[new_key])<=self.__ind):
               self.__rebuild_data_structure[new_key].append(None)   
           self.__rebuild_data_structure[new_key].append(None)
           return
        if(isinstance(data, list)):
           for index, value in enumerate(data):
               self._help_deep_smart_flatten_json(value, new_key+self.__special_separator+str(index))
           return 
        if(isinstance(data, int) or 
           isinstance(data, float) or 
           isinstance(data, bool) or 
           isinstance(data, str) or
           isinstance(data, bytes)):
           if(new_key not in self.__rebuild_data_structure):
               self.__rebuild_data_structure[new_key]=[]
           while(len(self.__rebuild_data_structure[new_key])<self.__ind):
               self.__rebuild_data_structure[new_key].append(None)    
           self.__rebuild_data_structure[new_key].append(data)
           return
        for key in data:
            self._help_deep_smart_flatten_json(data[key], new_key+self.__special_separator+str(key))

    def _deep_smart_flatten_json(self, df):
        self.__rebuild_data_structure.clear()
        self.__ind=0
        for row in df.iter_rows(named=True):
            for col in df.columns:
                self._help_deep_smart_flatten_json(row[col], col)   
            self.__ind+=1    
        for key in self.__rebuild_data_structure:
           while(len(self.__rebuild_data_structure[key])<self.__ind):
               self.__rebuild_data_structure[key].append(None)    
        result=[{} for _ in range(self.__ind)]
        for new_ind in range(self.__ind):
            for key in self.__rebuild_data_structure:
                new_key = key.split(self.__special_separator)
                if(len(new_key)==0):
                   continue
                new_key = '_'.join(new_key[-2:])  
                result[new_ind][new_key]=self.__rebuild_data_structure[key][new_ind]
        return pl.DataFrame(result) 