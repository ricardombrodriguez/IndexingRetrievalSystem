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
        
        # Dictionary to store the bm25 ranking of each publication, according to the current query
        pub_scores = {}

        # Iterate through query pairs of (tokens : term frequency)
        for query_token, query_token_tf in query_tokens.items():

            # Retrieve token postings list, if it exists
            postings_list = index.search_token(query_token) 
            
            # If the token doesn't exists (None), discard the query token for the ranking
            if not postings_list:
                continue

            # Iterating each publication in the postings list and update its BM25 score
            for pub_id, tf in postings_list.items():

                score = self.calculate_bm25(idf, tf, self.k1, self.k, pub_length,avg_pub_length)

                # Add score to pub_scores. Note: if a token is repeated two times in a query, the score is going to be multiplied by 2
                if pub_id not in pub_scores:
                    pub_scores[pub_id] = score * query_token_tf
                else:
                    pub_scores[pub_id] += score * query_token_tf

        # Using heapq.nlargest to find the k best scored publications in decreasing order
        top_k_pubs = nlargest(top_k, pub_scores.keys(), key=lambda k: pub_scores[k])

        return top_k_pubs

    def calculate_bm25(self, idf, tf, k1, b, pub_length, avg_pub_length):
        """
        Calculates bm25 formula for a publication given a query token
        """

        coefficient = idf
        nominator = tf * (k1 + 1)
        denominator = tf + k1 * (1 - b + b * (pub_length/avg_pub_length) )
        return coefficient * ( nominator / denominator )