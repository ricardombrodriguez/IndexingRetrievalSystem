from utils import dynamically_init_class
from heapq import nlargest
from math import log10, sqrt


def dynamically_init_searcher(**kwargs):
    """Dynamically initializes a Tokenizer object from this
    module.
    Parameters
    ----------
    kwargs : Dict[str, object]
        python dictionary that holds the variables and their values
        that are used as arguments during the class initialization.
        Note that the variable `class` must be here and that it will
        not be passed as an initialization argument since it is removed
        from this dict.
    
    Returns
        ----------
        object
            python instance
    """
    return dynamically_init_class(__name__, **kwargs)

class BaseSearcher:

    def search(self, index, query_tokens, top_k):
        pass

    def batch_search(self, index, reader, tokenizer, output_file, top_k=1000):
        print("searching...")
        # loop that reads the questions

        # aplies the tokenization to get the query_tokens
        query_tokens = []
        results = self.search(index, query_tokens, top_k)

        # write results to disk

    def get_token_postings_list(self, token):
        pass

    def normalise_token(self, token):

        pass

class TFIDFRanking(BaseSearcher):

    def __init__(self, smart, **kwargs) -> None:
        super().__init__(**kwargs)
        self.smart = smart
        print("init TFIDFRanking|", f"{smart=}")
        if kwargs:
            print(f"{self.__class__.__name__} also caught the following additional arguments {kwargs}")

    def search(self, index, query_tokens, top_k):

        tokens = [ normalise_term(token) for token in query_tokens ]
        query_matrix = { token : 1 + log10(tokens.count(token)) for token in tokens }
        
        weights = dict()

        for token in query_matrix:

            token_idf, postings_list = self.get_token_postings_list(token)
            if not postings_list:       # no token
                continue

            query_weight = query_matrix[token] *  token_idf

            for pmid, pub_weight in postings_list.items():
                token_score = query_weight * pub_weight
                
                try:
                    weights[pmid] += token_score
                except KeyError:
                    weights[pmid] = token_score

        query_length = sqrt( sum([score**2 for score in weights ]) )

        for pmid in weights:
            weights[pmid] /= query_length

        top_pubs = nlargest(top_k, weights, key = lambda score: (weights[score], -score))   # reversed sort min-heap

        return top_pubs



class BM25Ranking(BaseSearcher):

    def __init__(self, k1, b, **kwargs) -> None:
        super().__init__(**kwargs)
        self.k1 = k1
        self.b = b
        print("init BM25Ranking|", f"{k1=}", f"{b=}")
        if kwargs:
            print(f"{self.__class__.__name__} also caught the following additional arguments {kwargs}")

    def search(self, index, query_tokens, top_k):
        # index must be compatible with bm25
        pass
