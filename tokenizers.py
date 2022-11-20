"""
Authors:
Gonçalo Leal - 98008
Ricardo Rodriguez - 98388
"""

from utils import dynamically_init_class
import nltk
import re
from os.path import exists
from math import log10

def dynamically_init_tokenizer(**kwargs):
    return dynamically_init_class(__name__, **kwargs)
    

class Tokenizer:
    
    def __init__(self, **kwargs):
        super().__init__()


    def tokenize(self, pub_id, terms):

        # Lowercase, remove ponctuation, parentheses, numbers, and replace
        filtered_terms = []
        for term in terms:      
                                                            
            lower_term = term.lower()                                                                                                
            filtered_term = re.sub('[^a-zA-Z\d\s-]',' ',lower_term).lstrip('-')              # remove all non alphanumeric characters for the exception of the hiphens (removed at the beginning)

            if not filtered_term or len(filtered_term) < self.minL:
                continue

            if lower_term != filtered_term:
                for splitted_term in filtered_term.split(' '):   
                    filtered_terms.append(splitted_term)
            else:
                filtered_terms.append(filtered_term)

        tokens = {}
        for t in filtered_terms:
            if t not in self.stopwords:
                stem_t = self.stemmer_obj.stem(t) if self.stemmer else t
                if stem_t not in tokens:
                    tokens[stem_t] = { pub_id : 1 }
                else:
                    tokens[stem_t][pub_id] += 1

        # Calculate logarithm of term frequency
        for t in tokens:
            term_frequency = tokens[t][pub_id]
            tokens[t][pub_id] = 1 + log10(term_frequency)

        return tokens

    def get_stemmer(self, stemmer_name):
        # This function is used to get the stemmer object

        if stemmer_name == "potterNLTK":
            return nltk.stem.PorterStemmer()
        elif stemmer_name == "snowballNLTK":
            return nltk.stem.SnowballStemmer("english")
        elif stemmer_name == "lancasterNLTK":
            return nltk.stem.LancasterStemmer()
        else:
            return None

        
class PubMedTokenizer(Tokenizer):
    
    def __init__(self, 
                 minL, 
                 stopwords_path, 
                 stemmer, 
                 *args, 
                 **kwargs):
        
        super().__init__(**kwargs)
        self.minL = minL if minL else 0
        self.stopwords_path = stopwords_path
        self.stemmer = stemmer
        print("init PubMedTokenizer|", f"{minL=}, {stopwords_path=}, {stemmer=}")

        self.stopwords = set()
        if self.stopwords_path and exists(self.stopwords_path):
            stopwords_file = open(self.stopwords_path, 'r')
            self.stopwords = [word.strip() for word in stopwords_file.readlines()]
            stopwords_file.close()
        elif self.stopwords_path and not exists(self.stopwords_path): 
            raise FileNotFoundError(f"Stopwords file not found: {self.stopwords_path}")  

        #Stemmer
        self.stemmer_obj = self.get_stemmer(self.stemmer)  
        