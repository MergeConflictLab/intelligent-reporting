import polars as pl
import xml.etree.ElementTree as ET
from .base_connector import BaseConnector
from .registry import register_file
from ..expection import *
import os

import logging
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

@register_file(["xml"])
class XmlConnector(BaseConnector):
    def __init__(self, path: str):
        self.__rebuild_data_structure={}
        self.__ind=0
        self.__special_separator="###"
        self.path = path

    def _help_deep_smart_flatten_xml(self, root, new_key):
        """
        Recursively walk the XML tree and populate `__rebuild_data_structure`
        with flattened keys and their corresponding values
        """
        if(root.text is None or root.text.strip()!=""):
           if(new_key not in self.__rebuild_data_structure):
              self.__rebuild_data_structure[new_key]=[]
           while(len(self.__rebuild_data_structure[new_key])<self.__ind):
              self.__rebuild_data_structure[new_key].append(None)
           if(root.text is None):
              self.__rebuild_data_structure[new_key].append(None)
           else:  
              self.__rebuild_data_structure[new_key].append(root.text.strip())          
        for child in root:        
            self._help_deep_smart_flatten_xml(child, new_key+self.__special_separator+child.tag)      


    def _deep_smart_flatten_xml(self, root):
        """
        Flatten an entire XML document by extracting all nested elements into
        a tabular structure and converting it into a pl.Dataframe
        """
        self.__rebuild_data_structure.clear()
        self.__ind=0        
        for child in root:
            self._help_deep_smart_flatten_xml(child, child.tag)
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
        Load an XML file and return it as a flattened Polars DataFrame
        """
        if not os.path.exists(self.path):
            raise DataLoadingError(
                f"File not found: {self.path}"
            )

        # sanity check: parse XML
        try:
            tree = ET.parse(self.path)
        except ET.ParseError as e:
            raise DataLoadingError(
                f"Invalid or malformed XML file: {self.path}"
            ) from e
        except OSError as e:
            raise DataLoadingError(
                f"Failed to read XML file: {self.path}"
            ) from e

        root = tree.getroot()

        # sanity check: empty XML
        if root is None or len(root) == 0:
            raise DataLoadingError(
                f"XML file has no content: {self.path}"
            )

        # flatten
        try:
            df = self._deep_smart_flatten_xml(root)
        except Exception as e:
            raise DataLoadingError(
                f"Failed to flatten XML structure: {self.path}"
            ) from e

        # sanity check: flatten result
        if df.width == 0:
            raise EmptyDatasetError(
                f"Flattened XML has no columns: {self.path}"
            )

        if df.height == 0:
            raise EmptyDatasetError(
                f"Flattened XML has no rows: {self.path}"
            )

        return df
        