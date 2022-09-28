from utils import dynamically_init_class


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
        print("init SPIMIIndexer|", f"{posting_threshold=}, {memory_threshold=}")
        
    def build_index(self, reader, tokenizer, index_output_folder):
        print("Indexing some documents...")
        
        
class BaseIndex:
    
    def add_term(self, term, doc_id, *args, **kwargs):
        raise NotImplementedError()
    
    def print_statistics(self):
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
    
    