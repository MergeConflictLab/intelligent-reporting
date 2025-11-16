import polars as pl
import xml.etree.ElementTree as ET
class XmlLoader:
    def __init__(self):
        self.__rebuild_data_structure={}
        self.__ind=0
        self.__special_separator="###"
    

    def _help_deep_smart_flatten_xml(self, root, new_key):
        """
        Recursively walk the XML tree and populate `__rebuild_data_structure`
        with flattened keys and their corresponding values.

        takes
        ----------
        root : xml.etree.ElementTree.Element
            The current XML node being processed.
        new_key : str
            The accumulated key path representing the XML nesting hierarchy.

        Notes
        -----
        - If the node contains text, it is stored under the correct key.
        - Missing values are padded with None so all columns stay aligned.
        - Children are processed recursively, appending their tag to the key path.
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

        takes
        ----------
        root : xml.etree.ElementTree.Element
            The root element of the XML document.

        Returns
        -------
        pl.DataFrame
            A DataFrame where each row corresponds to one top-level XML element
            and nested tags are flattened into columns

        Notes
        -----
        - This method clears the internal buffer and processes each top-level
          element sequentially.
        - Keys like "book###author###name" are simplified to "author_name".
        - Missing values are padded so all columns have equal length.
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
    


    def load(self, file_path):
        """
        Load an XML file and return it as a flattened Polars DataFrame.

        takes:
        ----------
        file_path : str
            Path to the XML file.

        Returns
        -------
        pl.DataFrame
            A DataFrame representation of the XML structure.

        Raises
        ------
        ValueError
            If the file is not an `.xml` file.

        Notes
        -----
        - This method detects XML format, parses the file, and delegates
          to `_deep_smart_flatten_xml` to produce the tabular output.
        """
        file_extension=file_path.split(".")[-1].lower() 
        if(file_extension!="xml"):
            raise ValueError("The input file must be in XML format (.xml)")
        tree = ET.parse(file_path)
        root = tree.getroot()
        return self._deep_smart_flatten_xml(root)