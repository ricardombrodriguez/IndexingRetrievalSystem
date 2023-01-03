"""
Authors:
Gonçalo Leal - 98008
Ricardo Rodriguez - 98388
"""

from utils import dynamically_init_class
import nltk
import re
from os.path import exists

def dynamically_init_tokenizer(**kwargs):
    return dynamically_init_class(__name__, **kwargs)

class Tokenizer:

    def __init__(self, **kwargs):
        super().__init__()

    def tokenize(self, pub_id, terms):
        return NotImplementedError

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
            self.stopwords = {word.strip() for word in stopwords_file.readlines()}
            stopwords_file.close()
        elif self.stopwords_path and not exists(self.stopwords_path): 
            raise FileNotFoundError(f"Stopwords file not found: {self.stopwords_path}")

        #Stemmer
        self.stemmer_obj = self.get_stemmer(self.stemmer)

    def get_class(self):
        """
        Return class name
        """
        return self.__class__.__name__

    def tokenize(self, pub_id, terms):
        filtered_terms = []

        for term in terms:

            lower_term = term.lower()
            # remove all non alphanumeric characters for the exception
            # of the hiphens (removed if at the beginning)
            filtered_term = re.sub('[^a-zA-Z\d\s-]',' ',lower_term).lstrip('-').strip()

            # the filtered term must have more than minL chars
            # and cannot be in the list of stopwords
            if (not filtered_term or filtered_term == ""
                or len(filtered_term) < self.minL or filtered_term in self.stopwords):
                continue

            # has the lower_term variable end up being divided into two or more terms?
            if lower_term != filtered_term:
                for splitted_term in filtered_term.split(' '):
                    if (
                        splitted_term and splitted_term.strip() != ""
                        and len(splitted_term) > self.minL or splitted_term in self.stopwords
                    ):
                        stem_t = self.stemmer_obj.stem(splitted_term) if self.stemmer else splitted_term.strip()
                        filtered_terms.append(stem_t)
            else:
                stem_t = self.stemmer_obj.stem(filtered_term) if self.stemmer else filtered_term
                filtered_terms.append(stem_t)

        tokens = {}
        # tokens will contain a dictionary with
        # {token1: {pub1: <list of positions>, pub2: <list of positions>, ...}, token2: ... }
        # the term frequency (TF) is given by the length of the list of positions
        for token in filtered_terms:
            if token not in tokens:
                tokens[token] = { pub_id : [filtered_terms.index(token)] }
            else:
                tokens[token][pub_id] += [filtered_terms.index(token)]

        return tokens
