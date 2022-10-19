from utils import dynamically_init_class
import psutil
import time
import json
import gzip
import math
import os
from itertools import islice

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
                 **kwargs):
        # lets suppose that the SPIMIIindex uses the inverted index, so
        # it initializes this type of index
        super().__init__(InvertedIndex(posting_threshold), **kwargs)
        self.posting_threshold = posting_threshold
        self.memory_threshold = memory_threshold if memory_threshold is not None else 75
        print("init SPIMIIndexer|", f"{posting_threshold=}, {memory_threshold=}")
        print(f"{self.memory_threshold}mb")

        self.BLOCK_TERMS_LIMIT = 10000
        
    def build_index(self, reader, tokenizer, index_output_folder):
        print("Indexing some documents...")

        while True:
            pmid, pub_terms = reader.read_next_pub()         # read publication

            if pmid is None:
                break

            tokens = tokenizer.tokenize(pmid, pub_terms)    # tokenize publication

            [self._index.add_term(token, doc_id, int(counter), index_output_folder=index_output_folder, filename=f'{time.time()}') for token,data in tokens.items() for doc_id, counter in data.items()] # add terms to index

            print(f"Using {psutil.virtual_memory().percent}% of memory")
            # used_memory = psutil.virtual_memory().used >> 20  # in MB
            if psutil.virtual_memory().percent > self.memory_threshold:
                self._index.write_to_disk(index_output_folder)
                self._index.clean_index()

        self._index.write_to_disk(index_output_folder)
        self._index.clean_index()

class BaseIndex:

    def __init__(self, posting_threshold, **kwargs):
        self.posting_list = {}
        self._posting_threshold = posting_threshold

        self.block_counter = 0
        self.BLOCK_TERMS_LIMIT = 10000
    
    def add_term(self, term, doc_id, *args, **kwargs):
        # check if postings list size > postings_threshold
        if self._posting_threshold and len(self.posting_list) > self._posting_threshold:
            if 'index_output_folder' not in kwargs or 'filename' not in kwargs:
                raise ValueError("index_output_folder and filename are required in kwargs in order to store the index on disk")

            self.write_to_disk(kwargs['index_output_folder'], kwargs['filename'])
            self.clean_index()

        if doc_id not in self.posting_list:
            self.posting_list[doc_id] = [term]
        else:
            self.posting_list[doc_id].append(term)
    
    def print_statistics(self):
        raise NotImplementedError()

    def clean_index(self):
        self.posting_list = {}

    def write_to_disk(self, folder):

        print("Writing index to disk...")
        if not os.path.exists(folder):
            os.makedirs(folder)

        if not os.path.exists(folder.replace("/","") + "/metadata.txt"):
            os.mknod(folder.replace("/","") + "/metadata.txt")    # create metadata file

        sorted_index = dict(sorted(self.posting_list.items(), key=lambda x : x[0]))   # index sorted by tokens

        metadata = self.load_metadata(folder)

        tokens = list(sorted_index.keys())

        blocks = []

        if not metadata:

            blocks = self.get_block_chunks(tokens, sorted_index)

        else:

            # if there's a metadata file with content

            for i in range(len(list(metadata))-1,-1,-1):                  # reverse for

                block_terms = [token for token in tokens if token > metadata[i][0]]
                
                block_index = { token : sorted_index[token] for token in block_terms }

                # read block and get block index to merge
                with open(folder.replace("/","") + "/BLOCK_" + str(metadata[i][1]) + ".txt", "r+") as block_file:

                    for line in block_file:

                        line = line.split()

                        term = line[0]
                        postings_list = { posting.split(":")[0] : posting.split(":")[1] for posting in line[1:] }

                        if term not in block_index:

                            block_index[term] = postings_list

                        else:

                            block_index[term] |= postings_list

                    block_terms = sorted(block_index)      # sorted key list

                    blocks = self.get_block_chunks(block_terms, block_index)

                    if len(blocks) == 1:

                        # no need for additional block, only merge the index

                        block_file.truncate(0)      # erase file content

                        for term in block_terms:
                            
                            block_file.write(term + " " + " ".join([ str(k) + ":" + str(v) for k,v in block_index[term].items()] ) + "\n" )     # term 19334:2 29193:1 348243:4 ....

                        blocks = []

                        chunk_keys = block_terms
                        initial_token = chunk_keys[0]
                        num_tokens = len(block_terms)
                        num_postings = sum([len(postings) for postings in block_index.values()])

                        idx = None
                        for i, item in enumerate(metadata):
                            if item[1] == metadata[i][1]:
                                idx = i

                        metadata[idx] = [initial_token, metadata[i][1], num_tokens, num_postings]
                        metadata.sort(key = lambda x : x[0])    # sort by initial token
                        self.write_metadata(folder, metadata)

                if blocks:

                    os.remove(folder.replace("/","") + "/BLOCK_" + metadata[i][1] + ".txt")

                    metadata.pop(i)                        
            
        # exists a list of block indexes ready to be written on disk
        if blocks:

            for block in blocks:

                self.block_counter += 1

                filename = folder.replace("/","") + "/BLOCK_" + str(self.block_counter) + ".txt"

                if not os.path.exists(filename):
                    os.mknod(filename)

                with open(filename, "r+") as chunk_file:

                    for k,v in block.items():

                        chunk_file.write(k + " " + " ".join([ str(el[0]) + ":" + str(el[1]) for el in v]) + "\n" )

                chunk_keys = list(block.keys())
                initial_token = chunk_keys[0]
                num_tokens = len(chunk_keys)
                num_postings = sum([len(postings) for postings in block.values()])

                metadata.append([initial_token, self.block_counter, num_tokens, num_postings])
                metadata.sort(key = lambda x : x[0])    # sort by initial token
                self.write_metadata(folder, metadata)


    def get_blocks_number(self, index):

        index_terms = list(index.keys())

        num_blocks = 1

        if (len(index_terms) > self.BLOCK_TERMS_LIMIT) or ( self._posting_threshold and (sum([len(postings) for postings in index.values()]) > self._posting_threshold )):

            terms_ratio = math.ceil(len(index_terms) / self.BLOCK_TERMS_LIMIT)
            postings_list_ratio = math.ceil(sum([len(postings) for postings in index.values()] ) / self._posting_threshold) if self._posting_threshold else 1

            num_blocks = max([terms_ratio, postings_list_ratio])
            
        return num_blocks

    def get_block_chunks(self, terms, index):

        blocks = []

        num_blocks = self.get_blocks_number(index)

        if num_blocks != 1:

            chunk_length = math.floor(len(terms) / num_blocks)

            for i in range(num_blocks):

                chunk_terms = terms[i*chunk_length:(i+1)*chunk_length]

                chunk_index = { term : index[term] for term in chunk_terms  }

                blocks.append(chunk_index)
        
        else:

            blocks.append(index)
        
        return blocks

    def load_metadata(self, folder):

        metadata = []

        with open(folder.replace("/","") + "/metadata.txt", "r+") as meta_file:
            
            for line in meta_file:

                data = line.split()
                metadata.append([data[0]] + [int(element) for element in data[1:]])

        return metadata
    
    def write_metadata(self, folder, metadata):

        with open(folder.replace("/","") + "/metadata.txt", "r+") as meta_file:
            
            meta_file.truncate(0)
 
            for line in metadata:

                meta_file.write(" ".join([str(el) for el in line]) + "\n")

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
        if self._posting_threshold and len(self.posting_list) > self._posting_threshold:
            if 'index_output_folder' not in kwargs or 'filename' not in kwargs:
                raise ValueError("index_output_folder and filename are required in kwargs in order to store the index on disk")

            self.write_to_disk(kwargs['index_output_folder'], kwargs['filename'])
            self.clean_index()

        term_count = args[0]

        # term: [doc_id1, doc_id2, doc_id3, ...]
        if term not in self.posting_list:
            self.posting_list[term] = { doc_id : term_count }
        else:
            self.posting_list[term] += { doc_id : term_count }

    @classmethod
    def load_from_disk(cls, path_to_folder:str):
        raise NotImplementedError()
        # index = cls(posting_threshold, **kwargs)
        # index.posting_list = ... Adicionar os postings do ficheiro
        # esta classe tem de retornar um InvertedIndex
    
    def print_statistics(self):
        print("Print some stats about this index.. This should be implemented by the base classes")
    
    