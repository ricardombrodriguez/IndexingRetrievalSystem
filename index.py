from cgitb import small
from utils import dynamically_init_class
import psutil
from time import time, strftime, gmtime
import math
import gzip
import os

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
        self.token_threshold = token_threshold

        print("init SPIMIIndexer|", f"{posting_threshold=}, {memory_threshold=}")

        
    def build_index(self, reader, tokenizer, index_output_folder):
        print("Indexing some documents...")

        tic = time()
        while 1:

            pmid, pub_terms = reader.read_next_pub()         # read publication

            if pmid is None:                                # end of file
                break

            tokens = tokenizer.tokenize(pmid, pub_terms)    # tokenize publication

            [self._index.add_term(token, doc_id, int(counter), index_output_folder=index_output_folder) for token, data in tokens.items() for doc_id, counter in data.items()] # add terms to index

            pub_terms = {}

            print(f"Using {psutil.virtual_memory().percent}% of memory | {self._index.block_counter} blocks written", end="\r")

            if psutil.virtual_memory().percent > self.memory_threshold:
                self._index.write_to_disk(index_output_folder)
                self._index.clean_index()

        self._index.write_to_disk(index_output_folder)
        self._index.clean_index()

        n_temporary_files = len(self._index.filenames)

        # now we have to merge all the blocks
        self._index.merge_blocks(index_output_folder)

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
        self.token_threshold = kwargs['token_threshold'] if 'token_threshold' in kwargs else 30000

        self.block_counter = 0

        self.filenames = []
    
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
        raise NotImplementedError()

    def clean_index(self):
        self.posting_list = {}

    # Apenas escreve o indice em disco de forma ordenada
    def write_to_disk(self, folder):
        if not os.path.exists(folder):
            os.makedirs(folder)

        # First, we need to sort the index
        sorted_index = sorted(self.posting_list.items(), key=lambda x: x[0])

        # Then we write it to disk
        f = gzip.GzipFile(f"{folder}/block_{self.block_counter}.txt", "wb") # to read use the same line with rb
        self.filenames.append(f"{folder}/block_{self.block_counter}.txt")
        for term, posting in sorted_index:
            f.write(f"{term} {','.join([ str(el[0]) + ':' + str(el[1]) for el in posting])}\n".encode("utf-8"))
        f.close()
        self.block_counter += 1

    @classmethod
    def load_from_disk(cls, path_to_folder:str):
        # cls is an argument that referes to the called class, use it for initialize your index
        raise NotImplementedError()

class InvertedIndex(BaseIndex):
    # make an efficient implementation of an inverted index

    def __init__(self, posting_threshold, **kwargs):
        super().__init__(posting_threshold, **kwargs)
    
    def add_term(self, term, doc_id, *args, **kwargs):
        # check if postings list size > postings_threshold
        if (self._posting_threshold and len(self.posting_list) > self._posting_threshold) or (len(self.posting_list) > self.token_threshold):
            if 'index_output_folder' not in kwargs: # or 'filename' not in kwargs:
                raise ValueError("index_output_folder and filename are required in kwargs in order to store the index on disk")

            self.write_to_disk(kwargs['index_output_folder']) #, kwargs['filename'])
            self.clean_index()

        term_count = args[0]

        # term: [doc_id1, doc_id2, doc_id3, ...]
        if term not in self.posting_list:
            self.posting_list[term] = { doc_id : term_count }
        else:
            self.posting_list[term][doc_id] = term_count

    def merge_blocks(self, folder):
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

        # We will initialize the variable which will hold the line until the merge is done
        merge_line = None
        may_write = False

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

        tic = time()

        while files_ended < len(files):
            
            # The lines are in the format "term doc_id:counter,doc_id:counter,doc_id:counter"
            # We will split the lines by the space and we will get the term and the posting list
            terms = [line.split(" ", 1)[0] if line else None for line in lines]

            # We will get the index of the smallest term (which will be the index of the line that we will append to the block)
            smallest_term_index = 0
            for i in range(1, len(terms)):
                if (terms[smallest_term_index]) is None or (terms[i] is not None and terms[i] < terms[smallest_term_index]):
                    smallest_term_index = i 

            # We won't write the line for now, because we may need to merge 
            # the posting list in this line with the posting list in the next line

            # If the merge_line's term and the smallest term are the same, we will merge them
            # and we will keep without writing until the merge_line's term smallest term are different
            # which means the posting list of the merge_line's term is finished
            if merge_line is not None and merge_line.split(" ", 1)[0] == terms[smallest_term_index]:
                merge_line = f"{merge_line.split(' ', 1)[0]} {merge_line.split(' ', 1)[1]},{lines[smallest_term_index].split(' ', 1)[1]}"
                may_write = False
            else:
                may_write = True

            # If the merge_line is not None, it means we have to write it to the block file
            if may_write:
                if merge_line is not None:
                    final_block_file.write(merge_line.encode("utf-8"))
                    block_lines += 1
                    n_tokens += 1

                    # We will update the first term if needed
                    if first_term is None:
                        first_term = merge_line.split(" ", 1)[0]

                    # We are building blocks of files and an index file
                    # We will create a new block file when the number of lines in
                    # the current block file is greater than the token_threshold
                    if block_lines >= self.token_threshold:
                        last_term = merge_line.split(' ', 1)[0]

                        print(f"Block {final_block_counter} finished | first_term={first_term} and last_term={last_term}", end="\r")

                        # We have to update the index file
                        # We will write the first and last term of the block and the block's filename
                        with open(f"{folder}/index.txt", "a") as index_file:
                            index_file.write(f"{first_term} {last_term} {folder}/final_block_{final_block_counter}.txt\n")

                        # Close the actual block file
                        final_block_file.close()

                        # Add the size of the block file to the index size
                        index_size += os.path.getsize(f"{folder}/final_block_{final_block_counter}.txt")

                        # Create a new block file
                        final_block_counter += 1
                        final_block_file = gzip.GzipFile(f"{folder}/final_block_{final_block_counter}.txt", "wb")

                        # We need to reset the variables
                        first_term = None
                        block_lines = 0

                # The line we need to merge is now the actual smallest line
                merge_line = lines[smallest_term_index]
                may_write = False

            # We will read the next line of the file that we appended
            next_line = files[smallest_term_index].readline().decode("utf-8").strip()

            # If the next line is empty, it means that we have reached the end of the file
            # so we will close the file and we will increment the files_ended variable
            if next_line == None or next_line == "":
                files[smallest_term_index].close()
                files_ended += 1
                lines[smallest_term_index] = None
            else:
                lines[smallest_term_index] = next_line
        
        # Now we have to close the last block file
        final_block_file.close()

        # We have to update the index file
        # We will write the first and last term of the block and the block's filename
        with open(f"{folder}/index.txt", "a") as index_file:
            index_file.write(f"{first_term} {merge_line.split(' ', 1)[0]} {folder}/final_block_{final_block_counter}.txt\n")

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
    
    def print_statistics(self):
        print("Print some stats about this index.. This should be implemented by the base classes")
    
    