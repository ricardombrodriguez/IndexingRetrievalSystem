"""
Authors:
Gonçalo Leal - 98008
Ricardo Rodriguez - 98388
"""

from cgitb import small
from operator import index
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
        self.token_threshold = token_threshold if token_threshold else 50000

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
        self.token_threshold = kwargs['token_threshold'] if kwargs['token_threshold'] else 50000

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

        # First, we need to sort the index by key
        sorted_index = {k: self.posting_list[k] for k in sorted(self.posting_list)}

        # Then we write it to disk
        f = gzip.GzipFile(f"{folder}/block_{self.block_counter}.txt", "wb") # to read use the same line with rb
        self.filenames.append(f"{folder}/block_{self.block_counter}.txt")
        for term, posting in sorted_index.items():
            f.write(f"{term} {','.join([ str(el[0]) + ':' + str(el[1]) for el in posting])}\n".encode("utf-8"))
        f.close()
        self.block_counter += 1

    def merge_blocks(self, folder):
        print("Merging blocks...")
    
        #open all block files at the same time and read the first line from them
        block_files = [open(block_file, 'r', encoding='utf-8') for block_file in self.filenames]
        lines = [block_file.readline()[:-1] for block_file in block_files]
        most_recent_term = ""

        #remove empty blocks from list
        i = 0
        for b in block_files:
            if lines[i] == "":
                block_files.pop(i)
                lines.pop(i)
            else:
                i += 1

        #fill the final index file
        with open('final_index.txt', "w", encoding='utf-8') as output:
            while len(block_files) > 0:

                min_index = lines.index(min(lines))
                line = lines[min_index]
                current_term = line.split()[0]
                current_postings = " ".join(map(str, sorted(list(map(str, line.split()[1:])))))

                if current_term != most_recent_term:
                    output.write("\n%s %s" % (current_term, current_postings))
                    most_recent_term = current_term
                else:
                    output.write(" %s" % current_postings)

                lines[min_index] = block_files[min_index].readline()[:-1]

                if lines[min_index] == "":
                    block_files[min_index].close()
                    block_files.pop(min_index)
                    lines.pop(min_index)

            output.close()

        #clean all temporary index files
        [os.remove(block_file) for block_file in self.filenames]

        return True

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
        if (self._posting_threshold and sum([v for data in self.posting_list.values() for v in data.values() ]) > self._posting_threshold):
            
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

    @classmethod
    def load_from_disk(cls, path_to_folder:str):
        raise NotImplementedError()
        # index = cls(posting_threshold, **kwargs)
        # index.posting_list = ... Adicionar os postings do ficheiro
        # esta classe tem de retornar um InvertedIndex
    
    def print_statistics(self):
        print("Print some stats about this index.. This should be implemented by the base classes")
    
    