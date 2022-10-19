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

    # not going to be used -> read_next_pub() instead
    def open_file(self):
        terms = {}

        time_i = time()
        with gzip.open(self.path_to_collection, mode="rt") as file:
            cursor = 0

            while True:
                cursor += 1
            
                # Get next line from file
                line = file.readline()
            
                # if line is empty
                # end of file is reached
                if not line:
                    break

                pub_json = json.loads(line)
                pub_terms = set(pub_json['title'].split() + pub_json['abstract'].split())

                for term in pub_terms:
                    if term not in terms:
                        terms[term] = [pub_json['pmid']]
                    else:
                        terms[term] += [pub_json['pmid']]

        return terms