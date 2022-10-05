from ossaudiodev import SNDCTL_COPR_WCODE
from utils import dynamically_init_class
import nltk

def dynamically_init_tokenizer(**kwargs):
    return dynamically_init_class(__name__, **kwargs)
    

class Tokenizer:
    
    def __init__(self, **kwargs):
        super().__init__()
    
    def tokenize(self, document):
        """

        """

        # If there's an established mininum lenght for word filtering
        if self.minL:
            data = [el for el in data if len(el) < self.minL]

        # Normalization
        lowercase_tokens = [word.toLowercase() for word in data]

        # Stopword filter (specified or default)
        if self.stopwords_path:
            stopwords_file = open(self.stopwords_path, 'r')
            stopwords = [word.strip() for word in stopwords_file.readlines()]
        else:
            stopwords = set(nltk.corpus.stopwords.words("english"))
        filtered_tokens = [token for token in lowercase_tokens if token not in stopwords]

        #Stemming
        stemed_tokens = [nltk.stem.PorterStemmer.stem(token) for token in filtered_tokens]

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
        
