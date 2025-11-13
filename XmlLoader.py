import polars as pl
import xml.etree.ElementTree as ET
class XmlLoader:
    def __init__(self):
        self.__rebuild_data_structure={}
        self.__ind=0
        self.__special_separator="###"
    def loadfile(self, path):
        file_extension=path.split(".")[-1].lower() 
        if(file_extension!="xml"):
            raise ValueError("The input file must be in XML format (.xml)")
        tree = ET.parse(path)
        root = tree.getroot()
        return self._deep_smart_flatten_xml(root)
    def _help_deep_smart_flatten_xml(self, root, new_key):
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