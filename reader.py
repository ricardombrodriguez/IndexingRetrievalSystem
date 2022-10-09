import gzip
import json
import sys
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

        terms = {}

        with gzip.open(self.path_to_collection, mode="rt") as f:

            for pub in f:

                pub_json = json.loads(pub)
                pmid = pub_json['pmid']
                pub_terms = set(pub_json['title'].split() + pub_json['abstract'].split())
                for term in pub_terms:
                    if term not in terms:
                        terms[term] = [pmid]
                    else:
                        terms[term] += [pmid]

        print("The size of the dictionary is {} MBs".format(sys.getsizeof(terms)/1000000))
        print(terms["science"])
    