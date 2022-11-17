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

        terms = {}
        
        pub_json = json.loads(line)
        pub_terms = pub_json['title'].split() + pub_json['abstract'].split()
        pmid = pub_json['pmid']

        for term in pub_terms:
            if term not in terms:
                terms[term] = { pmid:1 }        # new term in the publication
            else:
                terms[term][pmid] += 1          # repeated term in the publication

        return pmid, terms            # key -> term | value -> { pmid : count }

    def extract_file(self):
        self.file = gzip.open(self.path_to_collection, mode="rt")

    def close_file(self):
        self.file.close()
        
class QuestionsReader(Reader):
    def __init__(self, 
                 path_to_questions:str,
                 **kwargs):
        super().__init__(path_to_questions, **kwargs)
        # I do not want to refactor Reader and here path_to_collection does not make any sense.
        # So consider using self.path_to_questions instead (but both variables point to the same thing, it just to not break old code)
        self.path_to_questions = self.path_to_collection
        print("init QuestionsReader|", f"{self.path_to_questions=}")
        if kwargs:
            print(f"{self.__class__.__name__} also caught the following additional arguments {kwargs}")
