import polars as pl
class JsonLoader:

    def __init__(self):
        """
        Initialize internal structures used for flattening nested JSON data.

        takes
        ----------
        __rebuild_data_structure : dict
            A dictionary mapping flattened JSON paths to lists of values.
        __ind : int
            A counter tracking the current row index being processed.
        __special_separator : str
            A separator used to construct hierarchical flattened keys.
        """

        self.__rebuild_data_structure={}
        self.__ind=0
        self.__special_separator="###"
 
        
    def _help_deep_smart_flatten_json(self, data, new_key):
        """
        Recursively flatten nested JSON values into `__rebuild_data_structure`.

        takes
        ----------
        data : any
            The current JSON value (dict, list, primitive, or None).
        new_key : str
            The hierarchical key path used to identify this value.

        Notes
        -----
        This method handles:
        - None values → stored as None
        - lists → flattened with numeric indices
        - primitives → appended directly
        - dicts → recursively flatten each child key

        The method also ensures:
        - Missing values are padded with None to maintain row alignment.
        - Key paths are assembled using the special separator.
        """

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
        """
        Flatten an entire Polars DataFrame of JSON objects into a tabular structure.

        takes
        ----------
        df : pl.DataFrame
            The DataFrame returned by `pl.read_json`.

        Returns
        -------
        pl.DataFrame
            A fully flattened DataFrame where nested objects and arrays are expressed
            as individual columns.

        Notes
        -----
        - Each row is processed independently.
        - For each column, nested JSON is walked recursively.
        - Final column names are simplified by taking only the last 2 components
          of the hierarchical key.
        - All columns are padded with None to ensure consistent DataFrame shape.
        """

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
    

    def load(self, file_path):
        """
        Load a JSON file into a Polars DataFrame and flatten all nested structures.

        takes
        ----------
        file_path : str
            Path to the JSON file.

        Returns
        -------
        pl.DataFrame
            A flattened DataFrame representation of the JSON structure.

        Raises
        ------
        ValueError
            If the file is not a `.json` file.

        Notes
        -----
        - The file is first read as a normal Polars JSON DataFrame.
        - Nested objects, lists, and values are then flattened recursively.
        """
        
        file_extension=file_path.split(".")[-1].lower() 
        if(file_extension!="json"):
            raise ValueError("The input file must be in JSON format (.json)")
        df = pl.read_json(file_path)   
        return self._deep_smart_flatten_json(df) 