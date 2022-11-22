"""
Authors:
Gonçalo Leal - 98008
Ricardo Rodriguez - 98388
"""

import re
from heapq import nlargest
from math import log10, sqrt
from utils import dynamically_init_class

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


        # loop that reads the questions from the QuestionsReader
        query = reader.read_next_question()
        while query:
            # aplies the tokenization to get the query_tokens
            # Tokenizer returns a dictionary with

            #     {
            #         'term': {
            #             'pub_id1': counter1,
            #             'pub_id2': counter2,
            #             'pub_id3': counter3,
            #         },
            #         ...
            #     }

            # We will only have one pub ID because we will address each query at a time
            # so, after getting the result from tokenize we transform the return into

            #     {
            #         'term': counter,
            #         ...
            #     }


            query_tokens = {token: pubs['1'] for token, pubs in tokenizer.tokenize('1', query).items()}
            print(query_tokens)
            results = self.search(index, query_tokens, top_k)

            # write results to disk

            query = reader.read_next_question()

    def normalise_token(self, term):

        lower_term = term.lower()                                                                                                
        filtered_term = re.sub('[^a-zA-Z\d\s-]',' ',lower_term).lstrip('-')              # remove all non alphanumeric characters for the exception of the hiphens (removed at the beginning)

        filtered_terms = [ filtered_term ]

        if lower_term != filtered_term:
            for splitted_term in filtered_term.split(' '):   
                filtered_terms.append(splitted_term)

        tokens = []
        for t in filtered_terms:
            if t not in self.stopwords:
                stem_t = self.stemmer_obj.stem(t) if self.stemmer else t
                tokens.append(stem_t)

        return tokens

class TFIDFRanking(BaseSearcher):

    def __init__(self, smart, **kwargs) -> None:
        super().__init__(**kwargs)
        self.smart = smart
        print("init TFIDFRanking|", f"{smart=}")
        if kwargs:
            print(
                f"{self.__class__.__name__} also caught the following additional arguments {kwargs}"
            )

    def calc_frequency(self, term_frequency):
        """
        Returns the term frequency based on the smart notation
        """

        frequency_letter = self.smart.split('.')[1][0]
        if frequency_letter == 'n':
            return term_frequency
        if frequency_letter == 'l':
            return 1 + log10(term_frequency)
        if frequency_letter == 'a':
            # Calculate augmented
            raise NotImplementedError
        if frequency_letter == 'b':
            # Calculate boolean
            raise NotImplementedError
        if frequency_letter == 'L':
            # Calculate log ave
            raise NotImplementedError

    def search(self, index, query_tokens, top_k):
        # calc term frequency
        tokens_weights = {
            token: self.calc_frequency(frequency) for token, frequency in query_tokens.items()
        }

        # posting_lists = {'token': {'doc_id': no_normalized_weight}}
        posting_lists = {}
        # get posting list for each token
        for token in tokens_weights:
            print("Searching for "+token)
            posting_lists[token] = index.search_token(token)

        # normalize doc weights

        # calc tokens weights (normalized)

        # compute "normal" index

        # get results

        # reversed sort min-heap
        # top_pubs = nlargest(top_k, weights, key = lambda score: (weights[score], -score))
        # return top_pubs
        return None

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
