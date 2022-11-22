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

            query_tokens = {
                token: pubs['1']
                for token, pubs in tokenizer.tokenize('1', query).items()
            }
            results = self.search(index, query_tokens, top_k)

            # write results to disk

            query = reader.read_next_question()

    def compute_normal_index(self, posting_lists):
        """
        posting_lists = {'token': {'doc_id': no_normalized_weight}}
        And we want to work with documents, so our index should be
        normal_index = {'doc_id': {'token': no_normalized_weight}}
        """

        normal_index = {}
        for token, posting_list in posting_lists.items():
            for doc_id, weight in posting_list.items():
                if doc_id not in normal_index:
                    normal_index[doc_id] = {}

                normal_index[doc_id][token] = weight
        return normal_index

class TFIDFRanking(BaseSearcher):
    """
    This class is responsible for searching and ranking documents based on a tfidf weighted index
    """

    def __init__(self, smart, **kwargs) -> None:
        super().__init__(**kwargs)
        self.smart = smart
        print("init TFIDFRanking|", f"{smart=}")
        if kwargs:
            print(
                f"{self.__class__.__name__} also caught the following additional arguments {kwargs}"
            )

    def calc_term_frequency(self, term_frequency):
        """
        Returns the term frequency based on the smart notation
        """

        term_frequency_letter = self.smart.split('.')[1][0]
        if term_frequency_letter == 'n':
            return term_frequency
        if term_frequency_letter == 'l':
            return 1 + log10(term_frequency)
        if term_frequency_letter == 'a':
            # Calculate augmented
            raise NotImplementedError
        if term_frequency_letter == 'b':
            # Calculate boolean
            raise NotImplementedError
        if term_frequency_letter == 'L':
            # Calculate log ave
            raise NotImplementedError
        else:
            raise NotImplementedError

    def calc_document_frequency(self, posting_list, n_documents):
        """
        Returns the term frequency based on the smart notation
        """

        doc_frequency_letter = self.smart.split('.')[1][1]
        if doc_frequency_letter == 'n':
            return 1
        if doc_frequency_letter == 't':
            return log10(n_documents/len(posting_list))
        if doc_frequency_letter == 'p':
            # Calculate prob idf
            raise NotImplementedError
        else:
            raise NotImplementedError

    def normalize_weights(self, weights, normalization_letter):
        """
        Normalizes weigths based on smart notation
        """
        if normalization_letter == 'n':
            return weights
        if normalization_letter == 'c':
            weight_sum = 0
            for weight in weights:
                weight_sum += weight**2

            return sqrt(weight_sum)
        if normalization_letter == 'u':
            # Calculate pivoted unique
            raise NotImplementedError
        if normalization_letter == 'b':
            # Calculate byte size
            raise NotImplementedError
        else:
            raise NotImplementedError

    def search(self, index, query_tokens, top_k):
        # calc term frequency
        tokens_weights = {
            token: self.calc_term_frequency(frequency) for token, frequency in query_tokens.items()
        }

        # posting_lists = {'token': {'doc_id': no_normalized_weight}}
        posting_lists = {}
        # get posting list for each token
        for token in tokens_weights:
            posting_lists[token] = index.search_token(token)

        # compute "normal" index
        normal_index = self.compute_normal_index(posting_lists)

        # normalize doc weights 
        for doc_id, token_list in normal_index.items():
            normal_index[doc_id]['normalized_weight'] = self.normalize_weights(
                weights = [weight for _, weight in token_list.items()],
                normalization_letter = self.smart.split('.')[0][2]
            )

        # calc tokens weights
        for token, weight in tokens_weights.items():
            tokens_weights[token] = weight * self.calc_document_frequency(
                posting_list=posting_lists[token],
                n_documents = int(index.n_documents)
            )

        # normalize query weights (in other words, get vector norm)
        query_normalized_weight = self.normalize_weights(
            weights = [weight for _, weight in tokens_weights.items()],
            normalization_letter = self.smart.split('.')[1][2]
        )

        # get results
        doc_weights = {}
        for doc_id, tokens in normal_index.items():
            # calc weight
            # para cada token na query, multiplicamos o seu peso pelo peso do
            # documento e depois dividimos pelos pesos normalizados de cada um
            doc_weight = 0
            for token, weight in tokens_weights.items():
                if token not in tokens:
                    continue
                doc_weight += weight * tokens[token]
            doc_weights[doc_id] = doc_weight / (query_normalized_weight * tokens['normalized_weight'])

        # Now we sort the documents by weight and choose the top_k 
        results = dict(sorted(doc_weights.items(), key=lambda item: item[1], reverse=True))
        counter = 0
        for doc_id, weight in results.items():
            if counter > top_k:
                break
            counter += 1
            print(f"{counter}: {doc_id} | weight={weight} | tokens={normal_index[doc_id].keys()}")

        # reversed sort min-heap
        # top_pubs = nlargest(top_k, weights, key = lambda score: (weights[score], -score))
        # return top_pubs
        return results # SÓ DEVE RETORNAR OS top_k RESULTADOS

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