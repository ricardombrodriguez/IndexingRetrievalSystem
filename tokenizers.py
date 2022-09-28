from utils import dynamically_init_class


def dynamically_init_tokenizer(**kwargs):
    return dynamically_init_class(__name__, **kwargs)
    

class Tokenizer:
    
    def __init__(self, **kwargs):
        super().__init__()
    
    def tokenize(self, document):
        raise NotImplementedError()

        
class PubMedTokenizer(Tokenizer):
    
    def __init__(self, 
                 minL, 
                 stopwords_path, 
                 stemmer, 
                 *args, 
                 **kwargs):
        
        super().__init__(**kwargs)
        self.minL = minL
        self.stopwords_path = stopwords_path
        self.stemmer = stemmer
        print("init PubMedTokenizer|", f"{minL=}, {stopwords_path=}, {stemmer=}")
        
