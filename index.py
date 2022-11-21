"""
Authors:
Gonçalo Leal - 98008
Ricardo Rodriguez - 98388
"""

from time import time, strftime, gmtime
from math import log10
import gzip
import os
import psutil
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
        super().__init__(InvertedIndex(posting_threshold, token_threshold=token_threshold), **kwargs)
        self.posting_threshold = posting_threshold
        self.memory_threshold = memory_threshold if memory_threshold else 75
        self.token_threshold = token_threshold if token_threshold else 50000
        self.weight_method = None
        self.kwargs = kwargs
        self.stemmer = ""

        print("init SPIMIIndexer|", f"{posting_threshold=}, {memory_threshold=}")

        if kwargs["tfidf"]["cache_in_disk"]:
            self.weight_method = 'tfidf'
            self.smart = kwargs["tfidf"]["smart"]
            print(f"Using tfidf - {self.smart}")
        elif kwargs["bm25"]["cache_in_disk"]:
            self.weight_method = 'bm25'
            self.bm25_k1 = kwargs["bm25"]["k1"]
            self.bm25_b = kwargs["bm25"]["b"]
            print(f"Using bm25 - k1 = {self.bm25_k1}; b = {self.bm25_b}")

    def build_index(self, reader, tokenizer, index_output_folder):
        print("Indexing some documents...")

        tic = time()
        n_documents = 0
        while 1:

            pmid, pub_terms = reader.read_next_pub()         # read publication
            if pmid is None:                                # end of file
                break

            n_documents += 1

            tokens, self.stemmer = tokenizer.tokenize(pmid, pub_terms)    # tokenize publication

            if self.weight_method == 'tfidf':
                if self.smart[0] == 'l':
                    # Calculate logarithm of term frequency
                    for token in tokens:
                        term_frequency = tokens[token][pmid]
                        tokens[token][pmid] = 1 + log10(term_frequency)
                elif self.smart[0] == 'a':
                    # Calculate augmented
                    raise NotImplementedError
                elif self.smart[0] == 'b':
                    # Calculate boolean
                    raise NotImplementedError
                elif self.smart[0] == 'L':
                    # Calculate log ave
                    raise NotImplementedError

            [self._index.add_term(token, doc_id, counter, index_output_folder=index_output_folder) for token, data in tokens.items() for doc_id, counter in data.items()] # add terms to index

            pub_terms = {}

            print(f"Using {psutil.virtual_memory().percent}% of memory | {self._index.block_counter} blocks written", end="\r")

            if psutil.virtual_memory().percent > self.memory_threshold:
                self._index.write_to_disk(index_output_folder)
                self._index.clean_index()

        self._index.write_to_disk(index_output_folder)
        self._index.clean_index()

        n_temporary_files = len(self._index.filenames)

        # now we have to merge all the blocks
        self._index.merge_blocks(index_output_folder, n_documents=n_documents, weight_method=self.weight_method, kwargs=self.kwargs)

        # Write metadata in index.txt file
        os.setxattr(f'{index_output_folder}/index.txt', 'user.indexer_index', f'{self.get_index_name()}'.encode('utf-8'))
        os.setxattr(f'{index_output_folder}/index.txt', 'user.indexer_stemmer', f'{self.stemmer}'.encode('utf-8'))
        os.setxattr(f'{index_output_folder}/index.txt', 'user.indexer_n_documents', f'{n_documents}'.encode('utf-8'))
        os.setxattr(f'{index_output_folder}/index.txt', 'user.indexer_weight', f'{self.weight_method}'.encode('utf-8'))
        if self.weight_method == 'tfidf':
            os.setxattr(f'{index_output_folder}/index.txt', 'user.indexer_smart', f'{self.smart}'.encode('utf-8'))
        elif self.weight_method == 'bm25':
            os.setxattr(f'{index_output_folder}/index.txt', 'user.indexer_k1', f'{self.bm25_k1}'.encode('utf-8'))
            os.setxattr(f'{index_output_folder}/index.txt', 'user.indexer_b', f'{self.bm25_b}'.encode('utf-8'))

        toc = time()

        print(f"Indexing finished in {strftime('%H:%M:%S', gmtime(toc-tic))} | {self._index.index_size/(1<<20)}mb occupied in disk | {n_temporary_files} temporary files | {self._index.n_tokens} tokens")

        # check if stats file exists
        if not os.path.exists("stats.txt"):
            with open("stats.txt", "w") as f:
                f.write("total_indexing_time | merging_time | index_size_on_disk | n_temporary_files | vocabulary_size | index_file_size\n")

        # store statistics
        with open("stats.txt", "a") as f:
            f.write(f"{strftime('%H:%M:%S', gmtime(toc-tic))} | {self._index.merging_time} | {self._index.index_size/(1<<20)} MB | {os.path.getsize(f'{index_output_folder}/index.txt')/(1<<20)} MB | {n_temporary_files} | {self._index.n_tokens}\n")

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
                raise ValueError("index_output_folder is required in kwargs in order to store the index on disk")

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

    @classmethod
    def load_from_disk(cls, path_to_folder:str):
        if not os.path.exists(f"{path_to_folder}/index.txt"):
            raise FileNotFoundError

        index_classname = os.getxattr(
                'indexes/pubmedSPIMIindexTiny/index.txt', 'user.indexer_index'
            ).decode('utf-8')

        if index_classname == "InvertedIndex":
            return InvertedIndexSearcher(
                path_to_folder=path_to_folder,
                posting_threshold=0
            )

        raise NotImplementedError

class InvertedIndex(BaseIndex):
    # make an efficient implementation of an inverted index

    def __init__(self, posting_threshold, **kwargs):
        super().__init__(posting_threshold, **kwargs)

    def add_term(self, term, doc_id, *args, **kwargs):
        # check if postings list size > postings_threshold
        if (self._posting_threshold and sum([v for data in self.posting_list.values() for v in data.values() ]) > self._posting_threshold or (self.token_threshold and len(self.posting_list) > self.token_threshold)):
            
            # if 'index_output_folder' not in kwargs or 'filename' not in kwargs:
            if 'index_output_folder' not in kwargs:
                raise ValueError("index_output_folder is required in kwargs in order to store the index on disk")

            self.write_to_disk(kwargs['index_output_folder']) #, kwargs['filename'])
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
        f = gzip.GzipFile(f"{folder}/block_{self.block_counter}.txt", "wb") # to read use the same line with rb
        self.filenames.append(f"{folder}/block_{self.block_counter}.txt")
        for term, posting in sorted_index.items():
            f.write(f"{term} {','.join([ str(pmid) + ':' + str(tf) for pmid, tf in posting.items()])}\n".encode("utf-8"))
        f.close()
        self.block_counter += 1

    def merge_blocks(self, folder, n_documents, weight_method, kwargs):
        print("Merging blocks...")

        # We will iterate over the files containing the blocks
        # and we will merge them by reading the first line of each file
        # and then we will compare them and append the smallest one
        # (alphabetically) to the final block files (after merging)
        # and we will read the next line of the file that we appended
        # we will do this until we reach the end of all the files

        files_ended = 0 # when this variable is equal to the number of files, it means we have already read all the files

        # We will create a file object for each file
        files = [gzip.GzipFile(filename, "rb") for filename in self.filenames]

        # We will read the first line of each file
        lines = [file.readline().decode("utf-8").strip() for file in files]

        # each time we create a new block, we will increment this variable
        final_block_counter = 0
        # We will create a file object for the final block file
        final_block_file = gzip.GzipFile(f"{folder}/final_block_{final_block_counter}.txt", "wb")

        # These variables will hold the first and last term in a block so we can use them to create the index file
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

        func = None
        if weight_method == "tfidf":
            if kwargs["tfidf"]["smart"][1] == 't':
                func = lambda df: log10(n_documents/df)
            elif kwargs["tfidf"]["smart"][1] == 'p':
                # Calculate augmented
                raise NotImplementedError

        recent_term = None

        current_term = None

        while files_ended < len(files):

            min_index = lines.index(min(lines))
            line = lines[min_index]

            current_term = line.split(" ", 1)[0]
            current_postings = line.split(" ", 1)[1]

            # We will update the first term if needed
            first_term = current_term if first_term is None else first_term

            if current_term != recent_term:

                # We are building blocks of files and an index file
                # We will create a new block file when the number of lines in
                # the current block file is greater than the token_threshold
                if block_lines >= self.token_threshold - 1:

                    print(f"Block {final_block_counter} finished | \
                        first_term={first_term} and recent_term={current_term}", end="\r")

                    # IMPLEMENTAR IDF
                    final_block_file.write(f"\n{current_term} {current_postings}".encode('utf-8'))
                    recent_term = current_term

                    # We have to update the index file
                    # We will write the first and last term of the block and the block's filename
                    with open(f"{folder}/index.txt", "a") as index_file:
                        index_file.write(f"{first_term} {current_term} \
                            {folder}/final_block_{final_block_counter}.txt\n")

                    # Close the actual block file
                    final_block_file.close()

                    # Add the size of the block file to the index size
                    index_size += os.path.getsize(f"{folder}/final_block_{final_block_counter}.txt")

                    # Create a new block file
                    final_block_counter += 1
                    final_block_file = gzip.GzipFile(
                        f"{folder}/final_block_{final_block_counter}.txt", "wb"
                    )

                    # We need to reset the variables
                    first_term = None
                    block_lines = 0

                else:

                    final_block_file.write(f"\n{current_term} {current_postings}".encode('utf-8'))
                    recent_term = current_term
                    block_lines += 1

            else:
                # IMPLEMENTAR IDF
                final_block_file.write(f",{current_postings}".encode('utf-8'))

            lines[min_index] = files[min_index].readline().decode('utf-8')[:-1]

            if lines[min_index] is None or lines[min_index] == "":
                files[min_index].close()
                files.pop(min_index)
                lines.pop(min_index)
                files_ended += 1

        # We have to update the index file
        # We will write the first and last term of the block and the block's filename
        with open(f"{folder}/index.txt", "a") as index_file:
            index_file.write(f"{first_term} {current_term} \
                {folder}/final_block_{final_block_counter}.txt\n")

        # Add the size of the index file to the index size
        index_size += os.path.getsize(f"{folder}/index.txt")

        print(f"Block {final_block_counter} finished")

        # Add the size of the block file to the index size
        index_size += os.path.getsize(f"{folder}/final_block_{final_block_counter}.txt")

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

    def read_index_file(self):
        """
        This function reads the index.ttx created by the merge function from InvertedIndex function
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

    def search_token(self, token):
        """
        Verifies if a token exists in the index
        If it exists the function returns its posting list
        If it doesn't exist the function returns None

        This function uses Binary Search to find the token in the index
        and then searches in the block file until it find the token
        """
        # em vez de ler linha a linha do ficheiro block podíamos começar pelo 
        # fim ou pela linha do meio, mas para já isso é muito complexo e 
        # temos coisas mais importantes a fazer


        pass
