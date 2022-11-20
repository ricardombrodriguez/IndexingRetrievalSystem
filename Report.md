# SPIMI Index - RI Assignment 1

This assigment's objective was to code a document indexer using the SPIMI strategy. We decided to develop our indexer in a way that it would be easy to search a term in the future. In order to achieve that we did not merge all the blocks of terms into a single file. Instead, we created several blocks of terms and wrote an index file so we know in which block file a specific term is.

## Our Approach

In this section we will describe how we solved all the steps of this assignment.

### Reading the file

The read_next_pub() method in the PubMedReader class is responsible for reading the collection publication by publication until there are none left. It only reads terms in the *title* and *abstract* sections and each term is mapped to the current publication identifier (*pmid*) and the number of times it appears in the publication, serving as a temporary index only for the publication.

### Creating tokens

After receiving the temporary index from the last read publication, the tokenizer is responsible for filtering the terms according to the parameters introduced in the command line when executing the program. The steps of the tokenization are the following:
1. Term is transformed into its lowercase version
2. Term is filtered by the regular expression '[^a-zA-Z\d\s-]' which removes all the set of non-alphanumeric characters, for the exception of the hiphen *-*.
3. All terms starting with one or more consecutive hiphens have them removed
4. Terms and their count are merged into the temporary index data structure (*e.g.* if *block.* and *block* are both terms that appear one time in the publication, the tokenizer knows they're reffering to the same term and merge them, removing the term *block.* from the index and adding one unit to the *block* counter)
5. If there's a minimum token lenght parameter, remove all the terms with less characters than the established value
6. If there's a stopword file, remove all the terms that appear in it
7. If there's a specified stemmer (potterNLTK, snowballNLTK, lancasterNLTK), stem the word
8. Return filtered tokens

### Indexing

To improve the performance of the SPIMI indexer, it's important to store the current index in a temporary file when the memory, number of tokens or number of postings reach their limit, so that it can be cleaned and we can continue reading other publications and store it in memory. 

The build_index() method is the main method of the *index.py* file, responsible for invoking the reader and tokenizer methods to get the publication terms and tokenize them, respectively. After that, all the publication tokens and their postings list are added to the Inverted Index data structure. In the InvertedIndex add_term() method, the term is only being added to the index if the number of tokens or postings are not exceeded. If that's the case, the in-memory index needs to be written to disk.

The *write_to_disk()* function starts by sorting the index by its terms and each term and its postings list is written line by line in a temporary block file in a sorted way. The *block_counter* variable is responsible for giving each temporary index file a unique name, being incremented each time a new index needs to be written on disk.

After this process, the index data structure can be clean so it can receive new terms and postings list from the next publications.

### Merging

Our merging process was adapted from [External Sort](https://en.algorithmica.org/hpc/external-memory/sorting/). Since we had a list of temporary blocks writen in disk and already sorted individually it became easy to apply a Merge Sort algorithm to them. 

We create a list of terms with all the first terms in each block. Then we choose the smallest one and write it (including posting list and counter) to a final block file. Everytime we write a term to the final block we read the next one from that temporary block until the file ends. Everytime the final block reaches the term threshold we close it and create a new one. 

In order to keep track of every final block file and the terms writen in it we have an index file which contains:
```
file_path first_term last_term
```

This way we can easily find a postings list for a specific term. In the worst case we have to load the index file to disk, which is very light, and loop through its lines until we find the final block that contains the term we are looking for. However, this process would be much faster if we use any type of searching algorithm like binary search.

## Usage

This section will give examples and describe the changes made to the initial `main.py` file.

### Parameters

You can use `python main.py -h` to get a list of all the parameter and a description of each one of them.

We added:
- Memory Threshold in percentage (this was more of a change rather than a add up)
- Token Threshold - maximum number of tokens per block

### Usage Examples

- Use all default values   
`python main.py indexer collections/pubmed_2022_tiny.jsonl.gz pubmedSPIMIindexTiny`

- Minimum length = 2 and use PotterStemmer   
`python main.py indexer collections/pubmed_2022_tiny.jsonl.gz pubmedSPIMIindexTiny --tk.minL 2 --tk.stemmer potterNLTK`

- Stopwords file and Term limit per block   
`python main.py indexer collections/pubmed_2022_tiny.jsonl.gz pubmedSPIMIindexTiny --tk.minL 2 --tl.stopwords_path stopwrds.txt --tk.stemmer potterNLTK --indexer.token_threshold 30000`

## Results

These results were achieved running [./assignment1.sh](./assignment1.sh)

On Gonçalo's pc (with stemm):
| File Size | Total Indexing Time | Index Size on Disk | Number of Temporary Files | Number of Terms | Index File Size | Merging Time (Approximate) |
|---|:---:|---|:---:|:---:|:---:|---:|
| Tiny (134,4 MB) | 00:06:03 | 8.17426586151123 MB | 51 | 388222 | 750 bytes | 38 seconds |
| Small (1,4 GB) | 01:36:46 | 38.461055755615234 MB | 511 | 1883845 | 4.0 kb | 2344 seconds |
| Medium (4,4 GB) | 10:11:58 | 83.68341255187988 MB | 1657 | 4237009 | 9.2 kb | 14823 seconds |
| Large (9,5 GB) | 1 day 13:47:54 | 139.10469245910645 MB | 3582 | 7173541 | 0.015 MB | 110967 seconds |

On Ricardo'd pc (tiny, small and medium ran in suspended mode - tiny usually takes 7 minutes normally):
| File Size | Total Indexing Time | Index Size on Disk | Number of Temporary Files | Number of Terms |
|---|:---:|---|:---:|:---:|
| Tiny (134,4 MB) | 00:24:17 | 8.17426586151123 MB | 51 | 388222 |
| Small (1,4 GB) | 02:15:42 | 38.461055755615234 MB | 511 | 1883845 |
| Medium (4,4 GB) | 10:17:25 | 83.68341255187988 MB | 1657 | 4237009 |
| Large (9,5 GB) | 20:50:45 | 169.94720077514648 MB | 2410 | 7872453 | 

