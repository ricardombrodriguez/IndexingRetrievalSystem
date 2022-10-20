from utils import dynamically_init_class
import psutil
import time
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
                 **kwargs):
        # lets suppose that the SPIMIIindex uses the inverted index, so
        # it initializes this type of index
        super().__init__(InvertedIndex(posting_threshold), **kwargs)
        self.posting_threshold = posting_threshold
        self.memory_threshold = memory_threshold if memory_threshold is not None else 75

        print("init SPIMIIndexer|", f"{posting_threshold=}, {memory_threshold=}")

        self.BLOCK_TERMS_LIMIT = 10000
        
    def build_index(self, reader, tokenizer, index_output_folder):
        print("Indexing some documents...")

        tic = time.time()
        while True:
            pmid, pub_terms = reader.read_next_pub()         # read publication

            if pmid is None:                                # end of file
                break

            tokens = tokenizer.tokenize(pmid, pub_terms)    # tokenize publication

            [self._index.add_term(token, doc_id, int(counter), index_output_folder=index_output_folder) for token, data in tokens.items() for doc_id, counter in data.items()] # add terms to index
            # [self._index.add_term(token, doc_id, int(counter), index_output_folder=index_output_folder, filename=f'{time.time()}') for token,data in tokens.items() for doc_id, counter in data.items()] # add terms to index

            pub_terms = {}

            print(f"Using {psutil.virtual_memory().percent}% of memory | {self._index.block_counter} blocks written", end="\r")
            # print(f"Using {psutil.virtual_memory().percent}% of memory | pmid={pmid} | pub_terms_len={len(self._index.posting_list)}")
            # print(f"memory threshold ---> {self.memory_threshold}")
            # used_memory = psutil.virtual_memory().used >> 20  # in MB
            if psutil.virtual_memory().percent > self.memory_threshold:
                self._index.write_to_disk_v2(index_output_folder)
                self._index.clean_index()
            
            # if psutil.virtual_memory().percent > self.memory_threshold or len(self._index.posting_list) > self.BLOCK_TERMS_LIMIT or sum(len(self._index.posting_list.values()) > self.posting_threshold):
            #     self._index.write_to_disk(index_output_folder)
            #     self._index.clean_index()

        self._index.write_to_disk_v2(index_output_folder)
        self._index.clean_index()

        # now we have to merge all the blocks
        self._index.merge_blocks(index_output_folder)

        toc = time.time()

        print(f"Indexing finished in {time.strftime('%Hh%Mm%Ss', time.gmtime(toc-tic))}")

class BaseIndex:

    def __init__(self, posting_threshold, **kwargs):
        self.posting_list = {}
        self._posting_threshold = posting_threshold

        self.block_counter = 0
        self.BLOCK_TERMS_LIMIT = 15000

        self.filenames = []
    
    def add_term(self, term, doc_id, *args, **kwargs):
        # check if postings list size > postings_threshold
        if self._posting_threshold and len(self.posting_list) > self._posting_threshold:
            # if 'index_output_folder' not in kwargs or 'filename' not in kwargs:
            if 'index_output_folder' not in kwargs:
                raise ValueError("index_output_folder is required in kwargs in order to store the index on disk")

            self.write_to_disk_v2(kwargs['index_output_folder'])
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
    def write_to_disk_v2(self, folder):
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

    def merge_blocks(self, folder):
        print("Merging blocks...")
    
        # We will iterate over the files containing the blocks
        # and we will merge them by reading the first line of each file
        # and then we will compare them and we will append the smallest one 
        # (alphabetically) to the final block files (after merging)
        # and we will read the next line of the file that we appended
        # we will do this until we reach the end of all the files

        files_ended = 0 # when this variable is equal to the number of files, it means we have already read all the files

        # We will create a file object for each file
        files = [gzip.GzipFile(filename, "rb") for filename in self.filenames]

        # We will read the first line of each file
        lines = [file.readline().decode("utf-8").strip() for file in files]

        # We will initialize the variable which will hold the line untill the merge is done
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

                    # We will update the first term if needed
                    if first_term is None:
                        first_term = merge_line.split(" ", 1)[0]

                    # We are building blocks of files and an index file
                    # We will create a new block file when the number of lines in
                    # the current block file is greater than the BLOCK_TERMS_LIMIT
                    if block_lines >= self.BLOCK_TERMS_LIMIT:
                        last_term = merge_line.split(' ', 1)[0]

                        print(f"Block {final_block_counter} finished | first_term={first_term} and last_term={last_term}", end="\r")

                        # We have to update the index file
                        # We will write the first and last term of the block and the block's filename
                        with open(f"{folder}/index.txt", "a") as index_file:
                            index_file.write(f"{first_term} {last_term} {folder}/final_block_{final_block_counter}.txt\n")

                        # Close the actual block and create a new one
                        final_block_file.close()
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

        print(f"Block {final_block_counter} finished")
        
        print("Merge complete...")

        print("Deleting temporary files...")
        # We will delete the temporary files
        for filename in self.filenames:
            os.remove(filename)

    def write_to_disk(self, folder):

        if not os.path.exists(folder):
            os.makedirs(folder)

        sorted_index = dict(sorted(self.posting_list.items(), key=lambda x : x[0]))   # index sorted by tokens

        metadata = self.load_metadata(folder)

        tokens = list(sorted_index.keys())

        blocks = []

        if not metadata:

            print()
            print("NO METADATA")

            blocks = self.get_block_chunks(tokens, sorted_index)

        else:

            # if there's a metadata file with content

            print()
            print("YESSSSS")

            for i in range(len(list(metadata))-1,-1,-1):                  # reverse for

                print(f"initial word is {metadata[i][0]}")


                block_terms = [token for token in tokens if token > metadata[i][0]]
                
                block_index = { token : sorted_index[token] for token in block_terms }

                # read block and get block index to merge
                with open(folder.replace("/","") + "/BLOCK_" + str(metadata[i][1]) + ".txt", "r+", encoding='utf-8') as block_file:

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

            print("blokcs")

            for block in blocks:

                self.block_counter += 1

                filename = folder.replace("/","") + "/BLOCK_" + str(self.block_counter) + ".txt"

                print()
                print("filenameeee")
                print(filename)

                if not os.path.exists(filename):
                    os.mknod(filename)

                with open(filename, "w", encoding='utf-8') as chunk_file:

                    for k,v in block.items():

                        chunk_file.write(k + " " + " ".join([ str(el[0]) + ":" + str(el[1]) for el in v]) + "\n" )

                chunk_keys = list(block.keys())
                initial_token = chunk_keys[0]
                num_tokens = len(chunk_keys)
                num_postings = sum([len(postings) for postings in block.values()])

                metadata.append([initial_token, self.block_counter, num_tokens, num_postings])
                metadata.sort(key = lambda x : x[0])    # sort by initial token
                print(metadata)
                self.write_metadata(folder, metadata)
                break


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

            print(f"NUM OF BLOCKS IS {num_blocks}")

            chunk_length = math.floor(len(terms) / num_blocks)

            for i in range(num_blocks):

                chunk_terms = terms[i*chunk_length:(i+1)*chunk_length]

                chunk_index = { term : index[term] for term in chunk_terms  }

                blocks.append(chunk_index)
        
        else:

            print("num blocks -> 1")

            blocks.append(index)
        
        return blocks

    def load_metadata(self, folder):

        metadata = []

        with open(folder.replace("/","") + "/metadata.txt", "w+", encoding='utf-8') as meta_file:
            
            lines = meta_file.readlines()
            print(lines)

            for line in lines:

                data = line.split()
                metadata.append([data[0]] + [int(element) for element in data[1:]])

        meta_file.close()

        return metadata
    
    def write_metadata(self, folder, metadata):

        with open(folder.replace("/","") + "/metadata.txt", "w", encoding='utf-8') as meta_file:
            
            meta_file.truncate(0)
 
            print()

            for line in metadata:

                meta_file.write(" ".join([str(el) for el in line]) + '\n')

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
        if (self._posting_threshold and len(self.posting_list) > self._posting_threshold) or (len(self.posting_list) > self.BLOCK_TERMS_LIMIT):
            if 'index_output_folder' not in kwargs: # or 'filename' not in kwargs:
                raise ValueError("index_output_folder and filename are required in kwargs in order to store the index on disk")

            self.write_to_disk_v2(kwargs['index_output_folder']) #, kwargs['filename'])
            self.clean_index()

        term_count = args[0]

        # term: [doc_id1, doc_id2, doc_id3, ...]
        if term not in self.posting_list:
            self.posting_list[term] = { doc_id : term_count }
        else:
            self.posting_list[term][doc_id] = term_count

    @classmethod
    def load_from_disk(cls, path_to_folder:str):
        raise NotImplementedError()
        # index = cls(posting_threshold, **kwargs)
        # index.posting_list = ... Adicionar os postings do ficheiro
        # esta classe tem de retornar um InvertedIndex
    
    def print_statistics(self):
        print("Print some stats about this index.. This should be implemented by the base classes")
    
    