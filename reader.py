"""
Authors:
Gonçalo Leal - 98008
Ricardo Rodriguez - 98388
"""

import gzip
import json
import sys
from time import time
from utils import dynamically_init_class


def dynamically_init_reader(**kwargs):
    return dynamically_init_class(__name__, **kwargs)


class Reader:
    
    def __init__(self, 
                 path_to_collection:str, 
                 **kwargs):
        super().__init__()
        self.path_to_collection = path_to_collection
        
    
class PubMedReader(Reader):
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        print("init PubMedReader|", f"{self.path_to_collection=}", )
        self.extract_file()

    def read_next_pub(self):

        line = self.file.readline()
        if not line:
            return None, None # fim do ficheiro

        pub_json = json.loads(line)
        pub_terms = pub_json['title'].split() + pub_json['abstract'].split()
        pmid = pub_json['pmid']

        return pmid, pub_terms            # key -> term | value -> { pmid : count }

    def extract_file(self):
        self.file = gzip.open(self.path_to_collection, mode="rt")

    def close_file(self):
        self.file.close()