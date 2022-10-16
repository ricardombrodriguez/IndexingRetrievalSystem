from utils import dynamically_init_class
import psutil
import time
import json
import os

def dynamically_init_indexer(**kwargs):
    return dynamically_init_class(__name__, **kwargs)


class Indexer:
    
    def __init__(self, 
                 index_instance,
                 **kwargs):
        super().__init__()
        self._index = index_instance
    
    def get_index(self):
        return self._index
    
    def build_index(self, reader, tokenizer, index_output_folder):
        raise NotImplementedError()
    

class SPIMIIndexer(Indexer):
    
    def __init__(self, 
                 posting_threshold, 
                 memory_threshold, 
                 **kwargs):
        # lets suppose that the SPIMIIindex uses the inverted index, so
        # it initializes this type of index
        super().__init__(InvertedIndex(posting_threshold), **kwargs)
        self.posting_threshold = posting_threshold
        self.memory_threshold = memory_threshold if memory_threshold is not None else (psutil.virtual_memory().used + int(psutil.virtual_memory().available / 2)) >> 20
        print("init SPIMIIndexer|", f"{posting_threshold=}, {memory_threshold=}")
        
    def build_index(self, reader, tokenizer, index_output_folder):
        print("Indexing some documents...")

        while True:
            pmid, pub_terms = reader.read_next_pub()         # read publication

            if pmid is None:
                break

            tokens = tokenizer.tokenize(pmid, pub_terms)    # tokenize publication

            [self._index.add_term(token, doc_id) for token in tokens for doc_id in tokens[token]] # add terms to index

            # used_memory = psutil.virtual_memory().used >> 20  # in MB
            if psutil.virtual_memory().used >> 20 > self.memory_threshold:
                self._index.write_to_disk(index_output_folder, f'{time.time()}')
                self._index.clean_index()

        self._index.write_to_disk(index_output_folder, f'{time.time()}')
        self._index.clean_index()

class BaseIndex:

    def __init__(self, posting_threshold, **kwargs):
        self.posting_list = {}
        self._posting_threshold = posting_threshold
    
    def add_term(self, term, doc_id, *args, **kwargs):
        # check if postings list size > postings_threshold
        if self._posting_threshold and len(self.posting_list) > self._posting_threshold:
            self.write_to_disk()
            self.clean_index()

        # document: [term1, term2, term3, ...]
        if doc_id not in self.posting_list:
            self.posting_list[doc_id] = [term]
        else:
            self.posting_list[doc_id].append(term)
    
    def print_statistics(self):
        raise NotImplementedError()

    def clean_index(self):
        self.posting_list = {}

    def write_to_disk(self, folder, filename):
        if not os.path.exists(folder):
            os.makedirs(folder)

        with open(f"{folder}/{filename}.json", "w") as file:
            json.dump(self.posting_list, file)
    
    @classmethod
    def load_from_disk(cls, path_to_folder:str):
        # cls is an argument that referes to the called class, use it for initialize your index
        raise NotImplementedError()

class InvertedIndex(BaseIndex):
    # make an efficient implementation of an inverted index

    def __init__(self, posting_threshold, **kwargs):
        super().__init__(posting_threshold, **kwargs)
    
    def add_term(self, term, doc_id, *args, **kwargs):
        # check if postings list size > postings_threshold
        if self._posting_threshold and len(self.posting_list) > self._posting_threshold:
            self.write_to_disk()
            self.clean_index()

        # term: [doc_id1, doc_id2, doc_id3, ...]
        if term not in self.posting_list:
            self.posting_list[term] = [doc_id]
        else:
            self.posting_list[term].append(doc_id)

    @classmethod
    def load_from_disk(cls, path_to_folder:str):
        raise NotImplementedError()
        # index = cls(posting_threshold, **kwargs)
        # index.posting_list = ... Adicionar os postings do ficheiro
    
    def print_statistics(self):
        print("Print some stats about this index.. This should be implemented by the base classes")
    
    