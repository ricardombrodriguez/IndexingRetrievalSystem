"""
Created by: Tiago Almeida & Sérgio Matos
Last update: 27-09-2022

Main python CLI interface for the IR class 
assigments.

The code was tested on python version 3.9.
Older versions (until 3.6) of the python 
interpreter may run this code [No verification
was performed, yet].

"""

import argparse
from core import engine_logic, add_more_options_to_indexer

class Params:
    """
    A container class used to store group of parameters.
    
    Note: Students can ignore this class, this is only used to
    help with grouping of similar arguments at the CLI.

    Attributes
    ----------
    params_keys : List[str]
        a list that holds the all of the name of the parameters
        added to this class

    """
    def __init__(self):
        self.params_keys = []
        
    def __str__(self):
        attr_str = ", ".join([f"{param}={getattr(self,param)}" for param in self.params_keys])
        return f"Params({attr_str})"
    
    def __repr__(self):
        return self.__str__()
    
    def add_parameter(self, parameter_name, parameter_value):
        """
        Adds at runtime a parameter with its respective 
        value to this object.
        
        Parameters
        ----------
        parameter_name : str
            Name of the parameter/variable (identifier)
        parameter_value: object
            Value of the variable
        """
        setattr(self, parameter_name, parameter_value)
        self.params_keys.append(parameter_name)
        
    def get_kwargs(self) -> dict:
        """
        Gets all of the parameters stored inside as
        python keyword arguments.
        
        Returns
        ----------
        dict
            python dictionary with variable names as keys
            and their respective value as values.
        """
        return {var_name:getattr(self, var_name) for var_name in self.params_keys}

def grouping_args(args):
    """
    Auxiliar function to group the arguments group
    the optional arguments that belong to a specific group.
    
    A group is identified with the dot (".") according to the
    following format --<group name>.<variable name> <variable value>.
    
    This method will gather all of the variables that belong to a 
    specific group. Each group is represented as an instance of the
    Params class.
    
    For instance:
        indexer.posting_threshold and indexer.memory_threshold, will be 
        assigned to the same group "indexer", which can be then accessed
        through args.indexer
        
    Parameters
        ----------
        args : argparse.Namespace
            current namespace from argparse
            
    Returns
        ----------
        argparse.Namespace
            modified namespace after performing the grouping
    """
    
    
    namespace_dict = vars(args)
    keys = set(namespace_dict.keys())
    for x in keys:
        if "." in x:
            group_name, param_name = x.split(".")
            if group_name not in namespace_dict:
                namespace_dict[group_name] = Params()
            namespace_dict[group_name].add_parameter(param_name, namespace_dict[x])
            del namespace_dict[x]
    
    return args

if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description="CLI interface for the IR engine")
    
    # operation modes
    # - indexer
    # - searcher
    mode_subparsers = parser.add_subparsers(dest='mode', 
                                            required=True)
    
    ############################
    ## Indexer CLI interface  ##
    ############################
    indexer_parser = mode_subparsers.add_parser('indexer', 
                                                help='Indexer help')
    
    indexer_parser.add_argument('path_to_collection', 
                                type=str, 
                                help='Name of the folder or file that holds the document collection to be indexed.')
    
    indexer_parser.add_argument('index_output_folder', 
                                type=str, 
                                help='Name of the folder where all the index related files will be stored.')
    
    indexer_settings_parser = indexer_parser.add_argument_group('Indexer settings', 'This settings are related to how the inverted index is built and stored.')
    indexer_settings_parser.add_argument('--indexer.class', 
                                    type=str, 
                                    default="SPIMIIndexer",
                                    help='(default=SPIMIIndexer).')
    
    indexer_settings_parser.add_argument('--indexer.posting_threshold', 
                                    type=int, 
                                    default=None,
                                    help='Maximum number of postings that each index should hold.')
    
    indexer_settings_parser.add_argument('--indexer.memory_threshold', 
                                    type=int, 
                                    default=None,
                                    help='Maximum limit of RAM that the program (index) should consume.')
        
    indexer_doc_parser = indexer_parser.add_argument_group('Indexer document processing settings', 'This settings are related to how the documents should be loaded and processed to tokens.')
    # corpus reader
    indexer_doc_parser.add_argument('--reader.class', 
                                    type=str, 
                                    default="PubMedReader",
                                    help='Type of reader to be used to process the input document collection. (default=PubMedReader).')
    
    # tokenizer
    indexer_doc_parser.add_argument('--tk.class', 
                                    #dest="class",
                                    type=str, 
                                    default="PubMedTokenizer",
                                    help='Type of tokenizer to be used to process the loaded document. (default=PubMedTokenizer).')
    
    indexer_doc_parser.add_argument('--tk.minL',
                                    #dest="minL",
                                    type=int, 
                                    default=None,
                                    help='Minimum token length. The absence means that will not be used (default=None).')
    
    indexer_doc_parser.add_argument('--tk.stopwords_path',
                                    #dest="stopwords_path",
                                    type=str, 
                                    default=None,
                                    help='Path to the file that holds the stopwords. The absence means that will not be used (default=None).')
    
    indexer_doc_parser.add_argument('--tk.stemmer',
                                    #dest="stemmer",
                                    type=str, 
                                    default=None,
                                    help='Type of stemmer to be used. The absence means that will not be used (default=None).')
    
    add_more_options_to_indexer(indexer_parser, indexer_settings_parser, indexer_doc_parser)
    
    ############################
    ## Searcher CLI interface ##
    ############################
    searcher_parser = mode_subparsers.add_parser('searcher', help='Searcher help')
    
    searcher_parser.add_argument('index_folder', 
                                type=str, 
                                help='Folder where all the index related files will be loaded.')
    
    # CLI parsing
    
    args = grouping_args(parser.parse_args())
    
    engine_logic(args)
