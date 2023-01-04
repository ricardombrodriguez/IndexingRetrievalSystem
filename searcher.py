"""
Authors:
Gonçalo Leal - 98008
Ricardo Rodriguez - 98388
"""
import itertools
from heapq import nlargest
from math import log10, sqrt
from utils import dynamically_init_class
from json import loads

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

    def __init__(self,
                **kwargs):

        self.interactive = False
        if kwargs["interactive"]:
            self.interactive = True

    def search(self, index, query_tokens, top_k):
        return NotImplementedError

    def interactive_search(self, index, tokenizer, top_k=1000, boost=None):
        # Continue query interactive mode
        cont = True

        # Don't stop until cont = False
        while cont:

            print("\n==================")
            query = input("Insert the query: ").split()

            query_tokens = {
                token: pubs['1']
                for token, pubs in tokenizer.tokenize('1', query).items()
            }

            results = self.search(index, query_tokens, top_k, boost)

            results_list = [ (pmid, score) for pmid,score in dict(results).items() ]

            # Paginator variable counter
            current_page = 0

            # Paginator (starts presenting page 1)
            while True:
                page_str = ""
                for i, pub in enumerate(results_list[current_page*10:current_page*10+10]):
                    page_str += f"#{(current_page)*10+i+1} - pub_id = {pub[0]} | weight = {pub[1]}\n"
                print(f"========= PAGE #{current_page+1} =========")
                print(page_str)

                command = input(
                    "[Commands]\n" +
                    "P - Go to previous page\n" +
                    "N - Go to next page\n" + 
                    "E - Leave results page\nCommand: "
                )

                match command:
                    case "P":
                        current_page -= 1
                        if current_page < 0:
                            print("You're in the first page!")
                            current_page = 0
                    case "N":
                        current_page += 1
                        if current_page > top_k//10 - 1:
                            print("You're in the last page!")
                            current_page -= 1
                    case "E":
                        break
                    case _:
                        print("Command not found!")

            while True:

                command = input("Do you want to keep querying? [Y/N]\nCommand: ")

                match command:
                    case "Y":
                        break
                    case "N":
                        cont = False
                        break
                    case _:
                        print("Command not found!")

    def batch_search(self, index, reader, tokenizer, output_file, top_k=1000, boost=None):
        """
        Function responsible for orchestrating the search process
        """

        if self.interactive:
            self.interactive_search(index, tokenizer, top_k, boost)
        else:
            with open(output_file, 'w+') as output_file:

                # loop that reads the questions from the QuestionsReader
                query_id, query = reader.read_next_question()
                while query:

                    query_tokens = {
                        token: pubs['1']
                        for token, pubs in tokenizer.tokenize('1', query).items()
                    }

                    results = self.search(index, query_tokens, top_k, boost)

                    # write results to disk

                    output_file.write(" ".join(query)+"\n")

                    for i, pmid in enumerate(results):
                        output_file.write(
                            f"#{i+1} - {pmid} | weight = {results[pmid]}\n"
                        )
                    output_file.write('\n')

                    query = reader.read_next_question()


    def boost_scores(self, query, document, boost):
        """
        This function is responsible for boosting the scores of the documents
        that contain all the query terms (and not only some of them)

        "If the document does not contain all the words in the query,
        it cannot be considered a match for the query and the boost
        factor would not be applied. The boost factor is a way to adjust
        the ranking of documents that are considered matches for a query
        by giving more weight to certain terms or groups of terms.
        If a document does not contain all the words in the query,
        it is not considered a match and the boost factor would not be applied."
        """

        # Number of distinct query terms in document
        num_distinct_terms = len(set(document).intersection(set(query)))

        # boost_factor is 1 by default (when document does not contain all query terms)
        boost_factor = 1

        if num_distinct_terms == len(set(query)):
            # Document contains all distinct query tokens (can apply min boost factor)
            token_positions = [ loads(data[1]) for data in document.values() ]
            # min_window_size = self.find_min_window_size(token_positions)
            min_window_size = self.find_min_window(token_positions)
            boost_factor = boost * (1 - (min_window_size - num_distinct_terms) / min_window_size)

        if boost_factor > 1:
            print("?======?")
            print(boost_factor)

        return boost_factor

    def find_min_window_size(self, token_positions):

        min_window_size = float("inf")
        for x in token_positions[0]:
            window = [x]
            for lst in token_positions[1:]:
                min_diff = float("inf")
                closest_y = None
                for y in lst:
                    for z in window:
                        distance = abs(z - y)
                        if distance < min_diff:
                            min_diff = distance
                            closest_y = y
                window.append(closest_y)
            sorted_window = sorted(window)
            window_size = sorted_window[-1] - sorted_window[0]
            if min_window_size is None or window_size < min_window_size:
                min_window_size = window_size

        return min_window_size

    def combinations(self, lists):
        """
        Generate all possible combinations using itertools
        Using yield instead of return to avoid memory issues and improve performance

        input: list of integer lists, example lists= [[1, 2, 3], [4, 5], [6, 7]]
        """
        for comb in itertools.product(*lists):
            yield comb

    def find_min_window(self, positions):
        """
        Looks for the minimum window size in the given positions
        using the brute force approach (inspirado no trabalho de AA)
        """
        min_distance = float("inf")
        for comb in self.combinations(positions):
            distance = max(comb) - min(comb)
            if distance < min_distance:
                min_distance = distance
        return min_distance

    def compute_normal_index(self, posting_lists):
        """
        posting_lists = {'token': {'doc_id': no_normalized_weight}}
        And we want to work with documents, so our index should be
        normal_index = {'doc_id': {'token': no_normalized_weight}}
        """
        if not posting_lists:
            return {}

        normal_index = {}
        for token, posting_list in posting_lists.items():
            if not posting_list:
                continue
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
        self.pivot = None
        # this should be tested, but for now we will use the value ranked as best in the paper
        self.slope = 0.3
        print("init TFIDFRanking|", f"{smart=}")
        if kwargs:
            print(
                f"{self.__class__.__name__} also caught the following additional arguments {kwargs}"
            )

    def calc_term_frequency(self, positions):
        """
        Returns the term frequency based on the smart notation
        """

        term_frequency = len(positions)
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
            if not posting_list:
                return 0
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
            if self.pivot is None:
                raise Exception("You cannot mix normalization methods")

            return (1.0 - self.slope) * self.pivot + self.slope * len(weights)
        if normalization_letter == 'b':
            # Calculate byte size
            raise NotImplementedError
        else:
            raise NotImplementedError

    def get_doc_norms(self, index, normal_index, normalization_letter):
        """
        Based on the normalization method returns a dictionary with
        doc_id: norm
        """

        if normalization_letter == 'n':
            return {doc_id: 1 for doc_id in normal_index.keys()}
        if normalization_letter == 'c':
            return index.read_norm_file()
        if normalization_letter == 'u':
            unique_counts = index.read_unique_counts_file()
            self.pivot = sum([n_unique for _, n_unique in unique_counts.items()]) / len(unique_counts)
            return {
                doc_id: (1.0 - self.slope) * self.pivot + self.slope * n_unique
                for doc_id, n_unique in unique_counts.items()
            }
        else:
            raise NotImplementedError

    def search(self, index, query_tokens, top_k, boost):
        """
        Get the top_k documents for query
        """

        # calc term frequency
        tokens_weights = {
            token: self.calc_term_frequency(positions) for token, positions in query_tokens.items()
        }

        # posting_lists = {'token': {'doc_id': no_normalized_weight}}
        posting_lists = {}
        # get posting list for each token
        for token in tokens_weights:
            posting_lists[token] = index.search_token(token)

        # compute "normal" index
        normal_index = self.compute_normal_index(posting_lists)

        # get doc norms
        doc_norms = self.get_doc_norms(
            index = index,
            normal_index = normal_index,
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

        normalized_tokens={}
        for token, weight in tokens_weights.items():
            normalized_tokens[token] = weight/query_normalized_weight

        # get results
        doc_weights = {}
        for doc_id, doc_tokens in normal_index.items():

            # calc weight
            # para cada token na query, multiplicamos o seu peso pelo peso do
            # documento e depois dividimos pelos pesos normalizados de cada um
            doc_weight = 0
            for token, weight in tokens_weights.items():
                if token not in doc_tokens:
                    continue
                doc_weight += weight/query_normalized_weight * doc_tokens[token][0]/doc_norms[doc_id]
            doc_weights[doc_id] = doc_weight

            # Get boosted score of the document (optional)
            if boost:
                #doc_weights[doc_id] *= self.boost_scores(query_tokens, doc_tokens)
                self.boost_scores(query_tokens, doc_tokens, boost)


        # Now we sort the documents by weight and choose the top_k
        results = []
        counter = 0
        for doc_id, weight in dict(
                    sorted(doc_weights.items(), key=lambda item: item[1], reverse=True)
                ).items():
            if counter > top_k:
                break
            counter += 1
            results.append({
                'doc_id': doc_id,
                'weight': weight,
                'norm': doc_norms[doc_id]
            })
        return { result['doc_id'] : result['weight'] for result in results }

class BM25Ranking(BaseSearcher):
    """
    This class is responsible for searching and ranking documents based on a bm25 weighted index
    """

    def __init__(self, k1, b, **kwargs) -> None:
        super().__init__(**kwargs)
        self.k1 = k1
        self.b = b
        print("init BM25Ranking|", f"{k1=}", f"{b=}")
        if kwargs:
            print(
                f"{self.__class__.__name__} also caught the following additional arguments {kwargs}"
            )

    def search(self, index, query_tokens, top_k, boost):

        # Dictionary to store the bm25 ranking of each publication, according to the current query
        pub_scores = {}

        # avg_pub_length -> average length of the publications
        # n_documents -> total number of documents/publications
        # pubs_length -> dictionary containing the pmid as key and 
        # the length of the publications as value
        parameters = index.get_pubs_length()
        avg_pub_length = float(parameters['pub_avg_length'])
        n_documents = int(parameters['n_documents'])
        pubs_length = parameters['pubs_length']

        # posting_lists = {'token': {'doc_id': no_normalized_weight}}
        posting_lists = {}
        # get posting list for each token
        for token in query_tokens.keys():
            posting_lists[token] = index.search_token(token)

        # compute "normal" index
        normal_index = self.compute_normal_index(posting_lists)

        for query_token, postings_list in posting_lists.items():
            if not postings_list:
                continue

            # compute idf
            idf = self.calculate_idf(postings_list, n_documents)

            # Iterating each publication in the postings list and update its BM25 score
            for pub_id, data in postings_list.items():

                positions = loads(data[1])

                score = self.calculate_bm25(
                    idf, len(positions), self.k1, self.b, pubs_length[pub_id], avg_pub_length
                )

                # Add score to pub_scores. Note: if a token is repeated two times in a query,
                # the score is going to be multiplied by 2
                if pub_id not in pub_scores:
                    pub_scores[pub_id] = score * len(query_tokens[query_token])
                else:
                    pub_scores[pub_id] += score * len(query_tokens[query_token])

                # Get boosted score of the document (optional)
                if boost:
                    self.boost_scores(query_tokens, normal_index[pub_id], boost)

        # Using heapq.nlargest to find the k best scored publications in decreasing order
        top_k_pubs = nlargest(top_k, pub_scores.keys(), key=lambda k: pub_scores[k])

        # Return top-k pmid : pub_score
        return { pmid : pub_scores[pmid] for pmid in top_k_pubs }

    def calculate_bm25(self, idf, tf, k1, b, pub_length, avg_pub_length):
        """
        Calculates bm25 formula for a publication given a query token
        """
        coefficient = idf
        nominator = tf * (k1 + 1)
        denominator = tf + k1 * ( (1 - b) + b * (int(pub_length)/avg_pub_length) )
        return coefficient * ( nominator / denominator )

    def calculate_idf(self, postings_list, n_documents):
        """
        Calculates document frequency and then the inverted document frequency
        """
        df = len(postings_list)
        idf = log10( int(n_documents) / df )
        return idf
