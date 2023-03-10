"""
Authors:
Gonçalo Leal - 98008
Ricardo Rodriguez - 98388
"""

from time import time, strftime, gmtime
from math import log10, sqrt
import os
import psutil
import linecache
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

    def get_index_name(self):
        return self._index.__class__.__name__

    def build_index(self, reader, tokenizer, index_output_folder):
        raise NotImplementedError()

class SPIMIIndexer(Indexer):

    def __init__(self,
                 posting_threshold,
                 memory_threshold,
                 token_threshold,
                 **kwargs):
        # lets suppose that the SPIMIIindex uses the inverted index, so
        # it initializes this type of index
        super().__init__(
            InvertedIndex(posting_threshold, token_threshold=token_threshold),
            **kwargs
        )

        self.posting_threshold = posting_threshold
        self.memory_threshold = memory_threshold if memory_threshold else 75
        self.token_threshold = token_threshold if token_threshold else 50000
        self.weight_method = None
        self.kwargs = kwargs

        print("init SPIMIIndexer|", f"{posting_threshold=}, {memory_threshold=}")

        if kwargs["tfidf"]["cache_in_disk"]:
            self.weight_method = 'tfidf'
            self.smart = kwargs["tfidf"]["smart"]
            print(f"Using tfidf - {self.smart}")
        elif kwargs["bm25"]["cache_in_disk"]:
            self.weight_method = 'bm25'
            self.pub_length = {}
            self.pub_total_tokens = 0
            self.pub_avg_length = 0
            print("Using bm25")

    def build_index(self, reader, tokenizer, index_output_folder):
        print("Indexing some documents...")

        tic = time()
        n_documents = 0
        while 1:

            # read publication
            # pmid, pub = reader.read_next_pub(fields=["title", "abstract"])
            pmid, pub = reader.read_next_pub()
            if pmid is None:    # end of file
                break

            n_documents += 1

            # tokenize publication
            filtered_terms = tokenizer.tokenize(pub)

            tokens = {}

            # Store tokens term positions
            for i, token in enumerate(filtered_terms):
                if token not in tokens:
                    tokens[token] = { pmid : [i] }
                else:
                    tokens[token][pmid] += [i]

            # is there any step we need to give because of the weighting method?
            if self.weight_method == 'tfidf':
                if self.smart[0] == 'l':
                    # Calculate logarithm of term frequency
                    for token in tokens:
                        positions = tokens[token][pmid]
                        term_frequency = len(positions)
                        tokens[token][pmid] = (1 + log10(term_frequency), positions)    # (tf, positions_list)
                elif self.smart[0] == 'a':
                    # Calculate augmented
                    raise NotImplementedError
                elif self.smart[0] == 'b':
                    # Calculate boolean
                    raise NotImplementedError
                elif self.smart[0] == 'L':
                    # Calculate log ave
                    raise NotImplementedError
            elif self.weight_method == 'bm25':
                pub_tokens = 0
                for token in tokens:
                    positions = tokens[token][pmid]
                    term_frequency = len(positions)
                    tokens[token][pmid] = (term_frequency, positions)    # (tf, positions_list)
                    pub_tokens += term_frequency
                self.pub_length[pmid] = pub_tokens
                self.pub_total_tokens += pub_tokens

            _ = [
                self._index.add_term(
                    token,
                    doc_id,
                    tf_positions,
                    index_output_folder=index_output_folder
                )
                for token, data in tokens.items()
                for doc_id, tf_positions in data.items()
            ] # add terms to index

            mem_percentage = psutil.virtual_memory().percent
            print(
                (f"Using {mem_percentage}% of memory | "
                f"{self._index.block_counter} blocks written"),
                end="\r"
            )

            if mem_percentage > self.memory_threshold:
                self._index.write_to_disk(index_output_folder)
                self._index.clean_index()

        self._index.write_to_disk(index_output_folder)
        self._index.clean_index()

        n_temporary_files = len(self._index.filenames)

        # now we need to create the final index using all the temporary files
        self._index.merge_blocks(
            index_output_folder,
            n_documents=n_documents,
            weight_method=self.weight_method,
            kwargs=self.kwargs
        )

        # Write metadata in index.txt file
        # these will be used in the search and
        # could be helpful for other operations
        os.setxattr(
            f'{index_output_folder}/index.txt', 'user.indexer_index', f'{self.get_index_name()}'
            .encode('utf-8')
        )
        os.setxattr(
            f'{index_output_folder}/index.txt', 'user.indexer_tokenizer', f'{tokenizer.get_class()}'
            .encode('utf-8')
        )
        os.setxattr(
            f'{index_output_folder}/index.txt', 'user.indexer_stopwords',
            f'{tokenizer.stopwords_path if tokenizer.stopwords_path else ""}'
            .encode('utf-8')
        )
        os.setxattr(
            f'{index_output_folder}/index.txt', 'user.indexer_minL', f'{tokenizer.minL}'
            .encode('utf-8')
        )
        os.setxattr(
            f'{index_output_folder}/index.txt', 'user.indexer_stemmer',
            f'{tokenizer.stemmer if tokenizer.stemmer else ""}'
            .encode('utf-8')
        )
        os.setxattr(
            f'{index_output_folder}/index.txt', 'user.indexer_n_documents',
            f'{n_documents}'.encode('utf-8')
        )
        os.setxattr(
            f'{index_output_folder}/index.txt', 'user.indexer_stopwords',
            f'{tokenizer.stopwords_path if tokenizer.stopwords_path else ""}'
            .encode('utf-8')
        )
        os.setxattr(
            f'{index_output_folder}/index.txt', 'user.indexer_minL', f'{tokenizer.minL}'
            .encode('utf-8')
        )
        os.setxattr(
            f'{index_output_folder}/index.txt', 'user.indexer_weight',
            f'{self.weight_method}'.encode('utf-8')
        )
        os.setxattr(
            f'{index_output_folder}/index.txt', 'user.indexer_token_threshold',
            f'{self._index.token_threshold}'.encode('utf-8')
        )

        if self.weight_method == 'tfidf':
            os.setxattr(
                f'{index_output_folder}/index.txt', 'user.indexer_smart',
                f'{self.smart}'.encode('utf-8')
            )
        elif self.weight_method == 'bm25':
            # store pub_length dictionary | { pub_id : pub_length }
            with open(f"{index_output_folder}/pubs_length.txt", "wb") as f:
                for pmid, pub_len in self.pub_length.items():
                    f.write(f"{pmid} {pub_len}\n".encode('utf-8'))
            self.pub_avg_length = self.pub_total_tokens / n_documents
            os.setxattr(
                f'{index_output_folder}/index.txt', 'user.indexer_pub_avg_length',
                f'{self.pub_avg_length}'.encode('utf-8')
            )

        toc = time()

        print(
            f"Indexing finished in {strftime('%H:%M:%S', gmtime(toc-tic))} |",
            f"{self._index.index_size/(1<<20)}mb occupied in disk |",
            f"{n_temporary_files} temporary files |",
            f"{self._index.n_tokens} tokens"
        )

        # check if stats file exists
        if not os.path.exists("stats.txt"):
            with open("stats.txt", "w") as stats_file:
                stats_file.write(
                    "total_indexing_time | " +
                    "merging_time | " +
                    "index_size_on_disk | " +
                    "n_temporary_files | " +
                    "vocabulary_size | " +
                    "index_file_size\n"
                )

        # store statistics
        with open("stats.txt", "a") as stats_file:
            stats_file.write(
                f"{strftime('%H:%M:%S', gmtime(toc-tic))} | " +
                f"{self._index.merging_time} | " +
                f"{self._index.index_size/(1<<20)} MB | " +
                f"{os.path.getsize(f'{index_output_folder}/index.txt')/(1<<20)} MB | " +
                f"{n_temporary_files} | {self._index.n_tokens}\n"
            )


class BaseIndex:

    def __init__(self, posting_threshold, **kwargs):
        self.posting_list = {}
        self._posting_threshold = posting_threshold

        self.token_threshold = kwargs['token_threshold'] if kwargs['token_threshold'] else 50000

        self.block_counter = 0

        self.filenames = []

        self.index_size = 0
        self.n_tokens = 0
        self.merging_time = 0

    def add_term(self, term, doc_id, *args, **kwargs):
        # check if postings list size > postings_threshold
        if self._posting_threshold and len(self.posting_list) > self._posting_threshold:
            # if 'index_output_folder' not in kwargs or 'filename' not in kwargs:
            if 'index_output_folder' not in kwargs:
                raise ValueError(
                    "index_output_folder is required in kwargs in order to store the index on disk"
                )

            self.write_to_disk(kwargs['index_output_folder'])
            self.clean_index()

        if doc_id not in self.posting_list:
            self.posting_list[doc_id] = [term]
        else:
            self.posting_list[doc_id].append(term)

    def print_statistics(self):
        print(f"{self.index_size/(1<<20)}mb occupied in disk | {self.n_tokens} tokens | merge took {self.merging_time} seconds")

    def clean_index(self):
        self.posting_list = {}

    # Apenas escreve o indice em disco de forma ordenada
    def write_to_disk(self, folder):
        pass

    def get_number_documents(self):
        n_documents = os.getxattr(
            f"{self.path_to_folder}/index.txt", 'user.indexer_n_documents'
        ).decode('utf-8')
        return n_documents

    @classmethod
    def load_from_disk(cls, path_to_folder:str):
        if not os.path.exists(f"{path_to_folder}/index.txt"):
            raise FileNotFoundError

        index_classname = os.getxattr(
                f"{path_to_folder}/index.txt", 'user.indexer_index'
            ).decode('utf-8')

        if index_classname == "InvertedIndex":
            return InvertedIndexSearcher(
                path_to_folder=path_to_folder,
                posting_threshold=0
            )

        raise NotImplementedError

class InvertedIndex(BaseIndex):
    """
    An inverted index uses the term as key and each term is associated with a list of publications.

    This class implements all the code needed to create an inverted index for a set of documents.
    It uses and index of indexes in order to make searching process faster,
    so in the end it produces an index.txt file with
    "term1 term2 index_file" like a set of encyclopedias does with the index book
    """
    # make an efficient implementation of an inverted index

    def __init__(self, posting_threshold, **kwargs):
        super().__init__(posting_threshold, **kwargs)

    def add_term(self, term, doc_id, *args, **kwargs):
        # check if postings list size > postings_threshold
        if (
            (self._posting_threshold and
            sum(
                [v for data in self.posting_list.values() for v in data.values()]
            ) > self._posting_threshold)
            or
            (self.token_threshold and len(self.posting_list) > self.token_threshold)
        ):
            # if 'index_output_folder' not in kwargs or 'filename' not in kwargs:
            if 'index_output_folder' not in kwargs:
                raise ValueError(
                    "index_output_folder is required in kwargs in order to store the index on disk"
                )

            self.write_to_disk(kwargs['index_output_folder'])
            self.clean_index()

        # term: [doc_id1, doc_id2, doc_id3, ...]
        if term not in self.posting_list:
            self.posting_list[term] = { doc_id : args[0] }
        else:
            self.posting_list[term][doc_id] = args[0]

    # Apenas escreve o indice em disco de forma ordenada
    def write_to_disk(self, folder):

        if not os.path.exists(folder):
            os.makedirs(folder)

        # First, we need to sort the index by key
        sorted_index = {k: self.posting_list[k] for k in sorted(self.posting_list)}

        # Then we write it to disk
        f = open(f"{folder}/block_{self.block_counter}.txt", "wb")
        self.filenames.append(f"{folder}/block_{self.block_counter}.txt")
        for term, posting in sorted_index.items():
            # term pmid:tf:[<positions>];pmid:tf:[<positions>];...
            f.write(f"{term} {';'.join([ str(pmid) + ':' + str(tf_positions[0]) + ':[' + ','.join(map(str, tf_positions[1])) + ']' for pmid, tf_positions in posting.items()])}\n".encode("utf-8"))
        f.close()
        self.block_counter += 1

    def merge_blocks(self, folder, n_documents, weight_method, kwargs):
        """
        During the indexing process, we will create a lot of blocks
        and we will need to merge them in order to create a final index
        that will be used to search for documents
        """

        print("Merging blocks...")

        # We will iterate over the files containing the blocks
        # and we will merge them by reading the first line of each file
        # and then we will compare them and append the smallest one
        # (alphabetically) to the final block files (after merging)
        # and we will read the next line of the file that we appended
        # we will do this until we reach the end of all the files

        # when this variable is equal to the number of files,
        # it means we have already read all the files
        files_ended = 0

        # We will create a file object for each file
        files = [open(filename, "rb") for filename in self.filenames]

        # We will read the first line of each file
        lines = [file.readline().decode("utf-8").strip() for file in files]

        # each time we create a new block, we will increment this variable
        final_block_counter = 0
        # We will create a file object for the final block file
        final_block_file = open(f"{folder}/final_block_{final_block_counter}.txt", "w")

        # This variable will hold the first term in a block
        # so we can use it to create the index file
        first_term = None

        # number of lines in a block
        block_lines = 0

        # size of index in disk
        index_size = 0

        # n_tokens in index
        n_tokens = 0

        # clean index.txt
        f = open(f"{folder}/index.txt", "w")
        f.close()

        tic = time()

        # if we are using weight methods we may want to perform some actions during merge
        func = None
        # if the weight method is TFIDF we will calculate the document frequency here and
        # the stored value is the final tfidf weight
        if weight_method == "tfidf":
            if kwargs["tfidf"]["smart"][1] == 't':
                func = lambda df: log10(n_documents/df)
            elif kwargs["tfidf"]["smart"][1] == 'p':
                # Calculate augmented
                raise NotImplementedError

        recent_term = None
        recent_postings = None

        current_term = None

        doc_index = {}

        while files_ended < len(files):

            min_index = lines.index(min(lines))
            line = lines[min_index]

            #print(f"Reading line {line} | {files_ended/len(files) * 100}%", end="\r")
            current_term = line.split(" ", 1)[0]
            current_postings = line.split(" ", 1)[1]

            # We will update the first term if needed
            first_term = current_term if first_term is None else first_term

            if current_term != recent_term:

                # if func is none at this point, then we may assume that the 
                # document frequency chosen is the no (n) one
                posting_list = ""
                if recent_term and func is not None:
                    # merge_line is "<term> <doc1>:<term_frequency>,<doc2>:<term_frequency>,..."
                    # we want tfidf, so we have to multiply tf with idf

                    idf = func(len(recent_postings.split(";")))
                    for posting in recent_postings.split(";"):
                        posting_data = posting.split(":")
                        posting_list += f"{posting_data[0]}:{float(posting_data[1]) * idf}:{str(posting_data[2])};"
                    posting_list = posting_list[:-1]
                else:
                    posting_list = recent_postings

                # normalization calcs
                if recent_term and weight_method == "tfidf":
                    if kwargs["tfidf"]["smart"][2] == 'c':
                        for posting in recent_postings.split(";"):
                            doc_id = posting.split(':')[0]
                            weight = posting.split(':')[1]
                            if doc_id not in doc_index:
                                doc_index[doc_id] = 0
                            doc_index[doc_id] += float(weight) ** 2
                    elif kwargs["tfidf"]["smart"][2] == 'u':
                        for posting in recent_postings.split(";"):
                            # in the end we want to know how many unique terms are in each doc
                            doc_id = posting.split(':')[0]
                            if doc_id not in doc_index:
                                doc_index[doc_id] = 0
                            doc_index[doc_id] += 1

                final_block_file.write(f"{recent_term} {posting_list}\n")

                block_lines += 1
                n_tokens += 1

                # We are building blocks of files and an index file
                # We will create a new block file when the number of lines in
                # the current block file is greater than the token_threshold

                if block_lines >= self.token_threshold:

                    print(
                        (f"Block {final_block_counter} finished | " +
                        f"first_term={first_term} and recent_term={recent_term}"),
                        end="\r"
                    )

                    # We have to update the index file
                    # We will write the first and last term of the block and the block's filename
                    with open(f"{folder}/index.txt", "a") as index_file:
                        index_file.write(
                            f"{first_term} {recent_term} {folder}/final_block_{final_block_counter}.txt\n"
                        )

                    # Close the actual block file
                    final_block_file.close()

                    # Add the size of the block file to the index size
                    index_size += os.path.getsize(f"{folder}/final_block_{final_block_counter}.txt")

                    # Create a new block file
                    final_block_counter += 1
                    final_block_file = open(
                        f"{folder}/final_block_{final_block_counter}.txt", "w"
                    )

                    # We need to reset the variables
                    first_term = None
                    block_lines = 0

                # Process new term (current_term)
                recent_term = current_term
                recent_postings = current_postings

            elif current_term:
                # Merge postings list while current_term = recent_term
                recent_postings += f";{current_postings}"

            lines[min_index] = files[min_index].readline().decode('utf-8')[:-1]

            if lines[min_index] is None or lines[min_index] == "":
                files[min_index].close()
                files.pop(min_index)
                lines.pop(min_index)
                files_ended += 1

        # We have to update the index file
        # We will write the first and last term of the block and the block's filename
        with open(f"{folder}/index.txt", "a") as index_file:
            index_file.write(f"{first_term} {current_term}" \
                f" {folder}/final_block_{final_block_counter}.txt\n")

        # Add the size of the index file to the index size
        index_size += os.path.getsize(f"{folder}/index.txt")

        print(f"Block {final_block_counter} finished")

        # Add the size of the block file to the index size
        index_size += os.path.getsize(f"{folder}/final_block_{final_block_counter}.txt")

        # normalization calcs
        if weight_method == "tfidf":
            if kwargs["tfidf"]["smart"][2] == 'c':
                with open(f"{folder}/doc_norms.txt", "w") as norm_file:
                    for doc_id, weight in doc_index.items():
                        norm_file.write(
                            f"{doc_id} {sqrt(weight)}\n"
                        )
            elif kwargs["tfidf"]["smart"][2] == 'u':
                with open(f"{folder}/doc_unique_counts.txt", "w") as counts_file:
                    for doc_id, n_unique in doc_index.items():
                        counts_file.write(
                            f"{doc_id} {n_unique}\n"
                        )

        print("Merge complete...")

        print("Deleting temporary files...")
        # We will delete the temporary files
        for filename in self.filenames:
            os.remove(filename)

        toc = time()

        self.index_size = index_size
        self.n_tokens = n_tokens
        self.merging_time = toc - tic


    @classmethod
    def load_from_disk(cls, path_to_folder:str):
        raise NotImplementedError()
        # index = cls(posting_threshold, **kwargs)
        # index.posting_list = ... Adicionar os postings do ficheiro
        # esta classe tem de retornar um InvertedIndex

class InvertedIndexSearcher(BaseIndex):
    """
    Inverted Index with a focus for search operations
    Created to keep classes simple and focused on one task
    """

    def __init__(self, posting_threshold, path_to_folder):
        super().__init__(posting_threshold, **{'token_threshold': None})
        self.path_to_folder = path_to_folder
        self.index = self.read_index_file()

        # metadata
        self.n_documents = 0
        self.weight_method = None
        self.smart = None
        self.bm25_b = None
        self.bm25_k1 = None
        self.read_index_metadata()

    def read_index_metadata(self):
        """
        This function will read the file's metadata
        """

        self.n_documents = os.getxattr(
            f"{self.path_to_folder}/index.txt", 'user.indexer_n_documents'
        ).decode('utf-8')
        self.weight_method = os.getxattr(
            f"{self.path_to_folder}/index.txt", 'user.indexer_weight'
        ).decode('utf-8')

        if self.weight_method == 'tfidf':
            self.smart = os.getxattr(
                f"{self.path_to_folder}/index.txt", 'user.indexer_smart'
            ).decode('utf-8')
        elif self.weight_method == 'bm25':
            pass
        else:
            raise NotImplementedError

    def read_index_file(self):
        """
        This function reads the index.txt created by the merge function from InvertedIndex function
        """

        if not os.path.exists(f"{self.path_to_folder}/index.txt"):
            raise FileNotFoundError

        index_file = open(f"{self.path_to_folder}/index.txt")
        line = index_file.readline().strip()

        index = []
        while line != "" and line is not None:
            helper = line.split(" ")

            if len(helper) != 3:
                raise Exception(
                    "Bad formated index! It should be: <first_term> <last_term> <block_location>"
                )

            index.append({
                'first_token': helper[0],
                'last_token': helper[1],
                'path': helper[2]
            })

            line = index_file.readline().strip()

        return index

    def read_norm_file(self):
        """
        This function only works when the normalization method is cosine
        It reads the file that contains the sqrt(token_weigth**2 for every token in doc)
        """
        if self.weight_method != 'tfidf' or self.smart.split('.')[0][2] != 'c':
            raise Exception(
                'read_norm_file function can only be called when the normalization is based on cosine'
            )

        if not os.path.exists(f"{self.path_to_folder}/doc_norms.txt"):
            raise FileNotFoundError

        doc_norms = {}
        with open(f"{self.path_to_folder}/doc_norms.txt") as norm_file:
            line = norm_file.readline()
            while line != "" and line is not None:
                doc_id, weight = line.split(' ')

                doc_norms[doc_id] = float(weight)

                line = norm_file.readline()

        return doc_norms

    def read_unique_counts_file(self):
        """
        This function only works when the normalization method is pivoted unique
        It reads the file that contains the number of unique tokens in each document
        """
        if self.weight_method != 'tfidf' or self.smart.split('.')[0][2] != 'u':
            raise Exception(
                'read_norm_file function can only be called when \
                the normalization is based on pivoted unique'
            )

        if not os.path.exists(f"{self.path_to_folder}/doc_unique_counts.txt"):
            raise FileNotFoundError

        unique_counts = {}
        with open(f"{self.path_to_folder}/doc_unique_counts.txt") as norm_file:
            line = norm_file.readline()
            while line != "" and line is not None:
                doc_id, count = line.split(' ')

                unique_counts[doc_id] = int(count.strip())

                line = norm_file.readline()

        return unique_counts

    def find_in_index(self, token):
        """
        Binary search implementation to find token's block file in index
        """

        low = 0
        high = len(self.index) - 1
        mid = 0

        while low <= high:

            mid = (high + low) // 2

            # If token is greater than the last token on this index line,
            # we ignore the left half of the index
            if self.index[mid]['last_token'] < token:
                low = mid + 1

            # If token is smaller than the first token on this index line,
            # we ignore the right half of the index
            elif self.index[mid]['first_token'] > token:
                high = mid - 1

            # Token is between the first and last tokens on this index line
            else:
                return mid

        # If we reach here, then the element was not present
        return -1

    def find_in_block_binary(self, block_path, token):
        """
        Binary search implementation to find token's postings list in the block file.
        Returns 'None' if the line hasn't been found.
        Returns the postings list if the token is in the block file.
        """
        block_lines = []
        with open(block_path, 'r') as block:
            block_lines = block.readlines()

        low = 1
        high = len(block_lines)
        mid = 1

        while low <= high:

            mid = (high + low) // 2

            # Retrieve the middle line of the block file | { <token> : <postings_list> }
            line = linecache.getline(block_path,mid).strip().split(" ")
            print(line)

            # If token is greater than the last token on this index line,
            # we ignore the left half of the index
            if line[0] < token:
                low = mid + 1

            # If token is smaller than the first token on this index line,
            # we ignore the right half of the index
            elif line[0] > token:
                high = mid - 1

            # Token is between the first and last tokens on this index line
            else:
                return line[1]  # Return postings list

        # If we reach here, then the element was not present
        return None

    def find_in_block(self, block_path, token):
        """
        Iterates through all lines in the block and searches for the token
        """

        with open(block_path, 'r') as block:
            for line in block:
                if line.strip() == "":
                    continue

                block_token = line.strip().split(" ")[0]
                if block_token == token:
                    return line.strip().split(" ")[1]

                if block_token > token:
                    return None

        return None

    def search_token(self, token):
        """
        Verifies if a token exists in the index
        If it exists the function returns its posting list
        If it doesn't exist the function returns None
        This function uses Binary Search to find the token in the index
        and then searches in the block file until it finds the token
        """

        index_position = self.find_in_index(token)
        if index_position == -1:
            return None

        posting_list = self.find_in_block(
            block_path = self.index[index_position]['path'],
            token = token
        )
        if not posting_list:
            return None

        # posting list is a string with the format:
        # <doc1>:<no_normalized_weight1>,<doc2>:<no_normalized_weight2>,...
        # we want it to be a dictionary with
        # {'doc1': no_normalized_weight1, ...}

        return {
            doc_info.split(":")[0]: (float(doc_info.split(":")[1]),doc_info.split(":")[2])
            for doc_info in posting_list.split(";")
        }

    def get_tokenizer_kwargs(self):
        """
        This class is used to initialize the tokenizer, we use it to guarantee
        that the params used in the indexing process are also used for the
        tokenization of query tokens during searching process
        """

        tokenizer_class = os.getxattr(
            f"{self.path_to_folder}/index.txt", 'user.indexer_tokenizer'
        ).decode('utf-8')
        stemmer = os.getxattr(
            f"{self.path_to_folder}/index.txt", 'user.indexer_stemmer'
        ).decode('utf-8')
        min_length = os.getxattr(
            f"{self.path_to_folder}/index.txt", 'user.indexer_minL'
        ).decode('utf-8')
        stopwords_path = os.getxattr(
            f"{self.path_to_folder}/index.txt", 'user.indexer_stopwords'
        ).decode('utf-8')

        return {
            'class': tokenizer_class,
            'stemmer': stemmer,
            'stopwords_path': stopwords_path,
            'minL': int(min_length)
        }


    def get_pubs_length(self):
        """
        This method returns the *pubs_length.txt* file which contains the pub_id and the
        length of the publication. Additionally, it will get the metadata attributes
        containing the total number of documents and the average length of the publications. 
        Needed for BM25 ranking.
        """

        pubs_length = {}

        pub_avg_length = os.getxattr(
            f"{self.path_to_folder}/index.txt", 'user.indexer_pub_avg_length'
        ).decode('utf-8')
        n_documents = os.getxattr(
            f"{self.path_to_folder}/index.txt", 'user.indexer_n_documents'
        ).decode('utf-8')

        # Retrieve key-value pairs of pub_lenght | "<pmid> <pub_length>"
        with open(f"{self.path_to_folder}/pubs_length.txt","rb") as f:
            for line in f:
                pair = line.decode('utf-8').strip().split(" ")
                pubs_length[pair[0]] = pair[1]

        return {
            'pub_avg_length': pub_avg_length,
            'n_documents': n_documents,
            'pubs_length': pubs_length
        }
