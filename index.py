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

        pmid, pub_terms = reader.read_next_pub()         # read publication
        print("ANTES DO TOKENIZER")
        print(pub_terms.keys())
        tokens = tokenizer.tokenize(pmid, pub_terms) 
        print("DEPOISSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSS")
        print(tokens.keys()) 

        # while True:
        #     pub_terms = reader.read_next_pub()         # read publication
        #     if not pub_terms:
        #         break   # EOF
        #     tokens = tokenizer.tokenize(pub_terms)     # flush publication terms to be filtered in the tokenizer
        #     # merge tokens in data structure



        """
        NUM_PUBS = 0
        BUFFER_SIZE = 1000
        
        While True:

            document = reader.read_document(line=NUM_PUBS)
            tokens = tokenizer.tokenize(document)
            indexer += tokens

            if RAM > threshold:
                write_index_to_disk() #store metadata about it too
                clean(indexer)


        merge_indexes()


        """

        #ret = tokenizer.tokenize(reader.open_file())
        #print(ret.keys())
        
        
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
    
    