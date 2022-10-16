from utils import dynamically_init_class
import psutil


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
        super().__init__(InvertedIndex(), **kwargs)
        self.posting_threshold = posting_threshold
        self.memory_threshold = memory_threshold
        print("init SPIMIIndexer|", f"{posting_threshold=}, {memory_threshold=}")
        
    def build_index(self, reader, tokenizer, index_output_folder):
        print("Indexing some documents...")

        index = InvertedIndex()

        while True:
            pmid, pub_terms = reader.read_next_pub()         # read publication
            print("ANTES DO TOKENIZER")
            print(pub_terms.keys())
            tokens = tokenizer.tokenize(pmid, pub_terms) 
            print("DEPOISSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSS")
            print(tokens.keys()) 

            used_memory = psutil.virtual_memory().used() >> 20  # in MB
            if used_memory > self.memory_threshold:
                index.write_index_to_disk()
                index.clean_index()

        
class BaseIndex:
    
    def add_term(self, term, doc_id, *args, **kwargs):
        # check if postings list size > postings_threshold
        raise NotImplementedError()
    
    def print_statistics(self):
        raise NotImplementedError()

    def clean_index(self):
        raise NotImplementedError()

    def write_to_disk(self):
        raise NotImplementedError()
    
    @classmethod
    def load_from_disk(cls, path_to_folder:str):
        # cls is an argument that referes to the called class, use it for initialize your index
        raise NotImplementedError()

class InvertedIndex(BaseIndex):
    
    # make an efficient implementation of an inverted index
        
    @classmethod
    def load_from_disk(cls, path_to_folder:str):
        raise NotImplementedError()
    
    def print_statistics(self):
        print("Print some stats about this index.. This should be implemented by the base classes")
    
    