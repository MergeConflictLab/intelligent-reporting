import polars as pl
from .base_connector import BaseConnector
from .registry import register_file
import json
from ..expection import *
import os

import logging
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

@register_file([".json", 'jsonl'])
class JsonConnector(BaseConnector):
    def __init__(self, path: str):
        """
        Initialize internal structures used for flattening nested JSON data.
        """
        self.path = path
        self.__rebuild_data_structure={}
        self.__ind=0
        self.__special_separator="###"
        self.allowed_options = {}
        
        
    def _help_deep_smart_flatten_json(self, data, new_key):
        """
        Recursively flatten nested JSON values into `__rebuild_data_structure`.
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
    

    def load(self):
        """
        Load a JSON file into a Polars DataFrame and flatten all nested structures.
        """
        if not os.path.exists(self.path):
            raise DataLoadingError(
                f"File not found: {self.path}"
            )

        # sanity check
        try:
            with open(self.path) as f:
                json.load(f)
        except json.JSONDecodeError as e:
            raise DataLoadingError(
                f"Invalid JSON content in file: {self.path}: {e}"
            ) from e

        # full read
        try:
            df = pl.read_json(self.path, infer_schema_length=None)   
            return self._deep_smart_flatten_json(df)
        except Exception as e:
            raise DataLoadingError(
                f"Failed to fully load JSON file: {self.path}: {e}"
            ) from e