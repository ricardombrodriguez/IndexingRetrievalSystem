# RI-2022 practical assignment (IR-system)

This repository contains the started code to build a fully functional IR system, it was projected to serve as guidelines to the RI students during their class assignments. Here, the students will find a definition of a generic enough API, that they should complete with the most adequated IR methods learned during the classes.

## Program Overview

The file `main.py` corresponds to the main entry point of the system that has two modes of operation the **indexer mode** and the **searcher mode**

- **indexer** mode: Responsible for the creation of indexes for a specific document collection. The index is a special data structure that enables fast searching over an enormous amount of data (text).
- **searcher** mode: Responsible for searching and ranking the documents given a specific question. The searcher presupposes that an index was previously built.

The `main.py` also contains the CLI (command line interface) that exposes the correct options/ways to run the IR system, further extension is possible by the students, however, they should not change the main structure of the CLI. Furthermore, the students **should not** change the `main.py` file, and in the case that they want to specify additional options, they should implement the functions `add_more_options_to_*` in the file `core.py`, which exposes the argparser that is being used in the `main.py` file.

The `core.py` corresponds to the first student entry point, meaning that here is where the students can start to make changes to the code to solve the proposed assignments. As a recommendation, we already offer a well-defined high-level API that the students can follow to implement the missing IR functionalities.

## How to run

Here we will show some normal utilization commands, we encourage to try out these commands to better understand the code.

Example of command to run the indexer:
```bash
python main.py indexer collections/pubmed_tiny.jsonl pubmedSPIMIindex --tk.minL 2 --tk.stopwords stopw.txt --tk.stemmer potterNLTK
```

Here, the program should index the documents present on `pubmed_tiny.jsonl` file and save the resulting index to the folder pubmedSPIMIindex, we also specified special options that are sent to the tokenizer (tk), for instance, we said to use the stopword file `stopw.txt`.

Example of command to run the searcher:
```
Will be update before the second assignment
```

The program also has a built-in help menu of each of the modes that specified all of the supported arguments, try:
```bash
python main.py -h
```

```bash
python main.py indexer -h
```

```bash
python main.py searcher -h
```

## High-level API overview

Our high-level API follows the main modules of an IR system (indexer, tokenizer, reader, searcher), and uses a plugin-like architecture to initialize each module, which offers a high degree of modularity and eases the addition of future functionality. The name of the classes that should be initialized are specified as CLI arguments (see the `main.py` file for more detail) 

The remainder of the files can be freely adapted by the students, however, we recommend sticking with this already defined API.

### Reader API

High-level abstraction on how the documents are read from an input stream (like a disk) to a continuous stream of text. Its code resides in the `reader.py` file, the base class is the `Reader` class that only holds the path to the collection that the program should read. The students should complete this API by implementing the missing functionality to read the documents stored on disk over a specific format. Besides the base class, we also created a PubMedReader that extends the previous one and should be responsible to read the pubmed.jsonl files that are required for the first assignment.

### Tokenizer API

High-level abstraction on how the text should be processed and split into individual tokens. Its code resides in the `tokenizer.py` file, the base class is the `Tokenizer` class that exposes the high-level method `_.tokenize(document)_` that should be implemented by its base classes. The students should complete this API by implementing the missing functionality. Besides the base class, we also created a `PubMedTokenizer` that extends the previous one and should be responsible for the tokenization of pubmed articles.

Note that here `PubMedTokenizer` may not be the best name to give, since the tokenizer may be generic enough to be used with other types of documents, so the student should consider this aspect of the code as well.

### Indexer API

High-level abstraction on how the tokens (from documents) should be indexed by the engine. Its code resides in the `indexer.py` file, the base class is the `Indexer` class that exposes the high-level method `_.build_index(reader, tokenizer, index_output_folder)_` that should be implemented by its base classes. The students should complete this API by implementing the missing functionality. Besides the base class, we also created a `SPIMIIndexer` that extends the previous one and should be responsible for the implementation of the SPIMI algorithm. Here, we also specified a basic index abstraction called BaseIndex, which holds some high-level functionality that an index must have.

Tip: May be worth it to think of the BaseIndex not as the final index but as an abstract index manager so that it eases the coordinate a group of index piece that holds part of the overall index.

## Code Overview and Tips

<h3 name="more-options">
How to add more options to the program (correct way according to the CLI)
</h3>

In order to expand the CLI options without changing the `main.py` file, we expose the argparser object in the [_add_more_options_to_indexer_](https://github.com/detiuaveiro/RI-2022/blob/master/core.py#L5) function.


### Dynamic loading of classes

Following the plugin-like architecture, each of the main modules is dynamically initialized by specifying its class name as a string for each main module. For that, each of the main modules has a _dynamically_init_* _ function that automatically initializes any class that belongs to each module. 

For instance, consider the Reader module (reader.py), at the beginning of the file we can the _dynamically_init_reader_ function that should be used to dynamically initialize any class that resides inside that file, which means that we can initialize the class PubMedReader at runtime by calling the previous function with the class name (_dynamically_init_reader("PubMedReader")_). Note that by default the program sets a CLI argument (_reader.class_) as "PubMedReader", which turns up to be the default reader that will be loaded by the program.

At this point, it should be clear that for adding new functionality the only thing that it is required to do is to implement a new class in the reader.py file that holds the code for a new type of reader. For instance, if we want to read XML files, we can build an XMLReader that extends Reader and when running the program we specified that this class should be used, like so:

```bash
python main.py indexer collections/pubmed_tiny.xml pubmedSPIMIindex --reader.class XMLReader
```

If your class needs extra arguments this is also easily achievable, just add the extra arguments to the CLI by extending the argparser (exposed by the [add_more_options_to_indexer](https://github.com/detiuaveiro/RI-2022/blob/master/core.py#L5) function). Note that the added arguments must be optional and under the _reader._ namespace, as an example consider:

```python
def add_more_options_to_indexer(indexer_parser, indexer_settings_parser, indexer_doc_parser):
    
    # adding option to the indexer_doc_parser that was set up under the "Indexer document processing settings" group
    # however, this will also work if it was added to the other exposed parsers.
    indexer_doc_parser.add_argument('--reader.xml_in_memory_limit', 
                                    type=float, 
                                    default=0.5,
                                    help='Fraction of the available RAM that the XMLReader will use. (default=0.5).')
```

After changing this function in the `core.py` file the argument _xml_in_memory_limit_ is automatically passed to the reader class, that in this case will be the XMLReader. For more information on how this mechanism works check [this](#more-options).

#### Code TIP

Consider the implementation of a manager class that can handles multiple type of files, for instance a ReaderManager that instantiates other types of readers like, PubMedReader, JsonReader, XMLReader. Although during this assignment a reader that can read a jsonl file is enough, its consider a good programming practice to build modular and easly expandible solutions.  




# Reports

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

# SPIMI Index - RI Assignment 2

The purpose of the 2nd assignment is to add term weighting to our indexing system and implement two ranked retrieval models, using the same datasets as the 1st assignment (medical publications). 

The two different ranked retrieval models are:
- Vector space ranking with **tf-idf** weights. We need to implement the *lnc.ltc* indexing schema as default and at least one alternative schema (we chose *lnu.ltu*). The indexing schema to use should be passed as a parameter, using the SMART notation.
- BM25ranking. The default values for the parameters are k1=1.2 and b=0.75 but we allow the specification of other values through command line arguments.

Additionally, we need to implement the search component of the retrieval system. This Searcher should read a previously created index – following one of the ranked retrieval models mentioned above – and process queries,returning a paginator with the best results (10 per page). The program starts the search mechanism and continually (in a loop) accepts user queries from the command line and presents the top 10 results, including the document scores.

## TFIDF

The **term frequency-inverse document frequency** is used in information retrieval as a numerical statistic that reflects the importance of a word to a document in a collection. It is often used as a weighting factor for information retrieval searches.
The value of tfidf increases with the number of times a word appears in the document, but is offset by the number of documents in the collection that contain the word. This helps adjusting for the fact that some words are more usual in documents than others. There are several variations of this weighting scheme and, even though we will only present two of them (lnc.ltc and lnu.ltu) our code base also supports other variations and we can easily develop other term frequency or inverse document frequency schemes.

### Indexing

To build an index with some pre-calculated tfidf values, we only need to know which variation we are using in SMART notation. After tokenizing a document's terms we calculate the term frequency for every term according to the chosen variation (the term frequency variation is given by the first letter in the SMART notation).

During the merge process, when we already know how many documents exist in the collection, we calculate every term's weight (tf * idf). tf has already been calculated before, idf is calculated before calculating the weight. Our index's final blocks contain an inverted index, but the posting list besides having the document id also stores the term's weight for that document.

- Cosine

If the normalization method is cosine we create a normal index (not inverted) and during the merge process we map each document's id to the sum of the square of each token's weight (if present in the said document). After finishing merge we write the index to a txt file, but while writing line by line we calculate the square root of the previously calculated sum for each document.

- Pivoted Unique

The Pivoted Unique normalization works very similarly to Cosine. During the merge process we build a normal index where we map every doc-id to the respective count of unique terms. In the end we write this dictionary to a file so we can read and use it during the search.

### Searching

After reading and tokenizing the query we calculate the tf and idf accordingly to the SMART notation an then the token's weight (tf * idf). Then we search for that token in the index, since we have several blocks with the index we search first the index.txt file using binary search so we know which block may contain that token.

```
index.txt

first_token last_token path_to_final_block_0
first_token last_token path_to_final_block_1
first_token last_token path_to_final_block_2
first_token last_token path_to_final_block_3
```

After finding the path to the final block that may contain the token we are looking for (first_token >= token >= last_token), we read that block and use binary search to find the token. 
Now we read the normalization files (doc_norms.txt for cosine or doc_unique_counts.txt for pivoted unique) and calculate the final weight of the document for that query:

For a given document d and a query q we sum the product of each token's weight in document and in query (weight(token, doc_id) * weight(token, query)) and we divide the value by the product of the normalizarion value of the document with the normalization value of the query.

### Results

#### Indexing

- lnc.ltc

| File Size | Total Indexing Time | Merging Time | Index Size on Disk | Index File Size | Number of Temporary Files | Number of Terms |
|---|:---:|---|:---:|:---:|:---:|---:|
| Tiny (134,4 MB) | 00:06:07 | 44s | 67.32154750823975 MB | 0.0009365081787109375 MB | 51 | 388103 |
| Small (1,4 GB) | 01:06:27 | 601s | 610.2258224487305 MB | 0.00469970703125 MB | 508 | 1883692 |

- lnu.ltu

| File Size | Total Indexing Time | Merging Time | Index Size on Disk | Index File Size | Number of Temporary Files | Number of Terms |
|---|:---:|---|:---:|:---:|:---:|---:|
| Tiny (134,4 MB) | 00:06:06 | 40.59485197067261 | 67.32154750823975 MB | 0.0009365081787109375 MB | 51 | 388103 |
| Small (1,4 GB) | 01:08:16 | 574.1285059452057 | 610.2258224487305 MB | 0.00469970703125 MB | 508 | 1883692 |

- bm25

| File Size | Total Indexing Time | Merging Time | Index Size on Disk | Index File Size | Number of Temporary Files | Number of Terms |
|---|:---:|---|:---:|:---:|:---:|---:|
| Tiny (134,4 MB) | 00:05:41 | 26.31964349746704 | 61.458309173583984 MB | 0.0008993148803710938 MB | 51 | 388103 |
| Small (1,4 GB) | 01:17:27 | 399.9907560348511 | 556.2714080810547 MB | 0.004519462585449219 MB | 508 | 1883692 |

## BM25

The **Okapi BM25** ranking function is a successor to the **TF-IDF** method explained above. It's main advantage over TF-IDF is giving importance to document lenght. For example, if document A and B both have 300 words but document A mentions 'medicine' one time and document B mentions 'medicine' five times, we consider document B has being the more relevant one since document length is equal but the term 'medicine' appears more times in document B than in document A. However, if document A still has 300 words but document B has 10000 words (an abnormal number of terms), document B would be less relevant than document A for the term 'medicine'. This is because although 'medicine' appears more times in document B, it still has a much bigger document length than document A, being more likely to contain more 'medicine' terms. Thus, 3 'medicine' terms in a 300 word document is more relevant than 5 'medicine' terms in a 10000 word document.

### Indexing

To build the BM25 suitable index, we only need to add some variables. After the tokenization of publications terms, if the ranking method is BM25, the program is going to sum the *tokens* term frequency of each filtered token to *self.pub_total_tokens*, a variable that is going to store the total number of tokens in all publications. Moreover, the dictionary *self.pub_length* is updated after each publication is tokenized with the publication id as the key and publication length (number of tokens) as the value.

After reading all publications, the *self.pub_length* dictionary containing the publication id and its respective lenght is written in the file *{index_output_folder}/pubs_length.txt*, each line representing a key-value pair ready to be read for the search mechanism. Another important variable for the search component is , The *self.pub_avg_length* variable is also calculated in this moment, which computes the average length of the publications according to the total number of processed tokens (*self.pub_total_tokens*) and the number of publications (*self.n_documents*), and is stored in the *index.txt* file as metadata.

### Searching

The equation which computes the BM25 score of a document given a certain query is depicted in the figure below:

![BM25 equation](bm25_equation.png)

Equation analysis:
- Q*i* --> Q*i* is the the *i*th query term.
- IDF(q*i*) --> Inversed document frequency of the *i*th query term. The *calculate_idf()* method computes the IDF of a token according to its document frequency (calculated using the term's postings list) and the total number of document/publications.
- f(Qi,D) --> Q*i* term frequency in document *D*.
- k1 --> Variable that limits how much a query term can affect the score of a given document.
- b --> Variable that controls how much influence the length of a document compared to the average document length has. When *b* is bigger, the lenght ratio is amplified.
- *fieldLen*/*avgFieldLen* --> Ratio between document *D* length (current document) and the average document length (*avg_pub_length*). The ratio will be bigger than 1 if document *D* has a bigger than average length and smaller than 1 if it has a smaller than average length.

In order to calculate this formula to each document and for each query, the program starts analysing a single query term. It retrieves the token's postings list (if it exists), and starts calculating the IDF of the token. After that, the program will iterate through the term's postings list and calculate the score of the document given a token and add the result to the publication score stored in the *pub_scores* variable. If the current query token is repeated 2 times, the BM25 result of the term will be multiplied by 2 and then added to the publication score.

In the end, the publications scores are established and the program is ready to sort the *pub_scores* dictionary by decreasing order using the heap queue algorithm (*heapq*) and retrieves the *top-k* publication id's. Then, the *search()* method returns a dictionary containing the *top-k* publications with their id's as keys and their BM25 scores as values.


### Results

## How to use

### Indexer

- TFIDF

```bash
python3 main.py indexer <path_to_collection> <output_folder> \
--tk.minL <min_length> \
--tk.stemmer <stemmer> \
--indexer.posting_threshold <threshold> \
--indexer.token_threshold <threshold> \
--indexer.tfidf.cache_in_disk \
--indexer.tfidf.smart <smart_notation>
```

Example:
```bash
python3 main.py indexer collections/pubmed_2022_tiny.jsonl.gz indexes/lnc_ltc/pubmedSPIMIindexTiny \
--tk.minL 2 \
--tk.stemmer potterNLTK \
--indexer.posting_threshold 30000 \
--indexer.token_threshold 30000 \
--indexer.tfidf.cache_in_disk \
--indexer.tfidf.smart lnc.ltc
```

- BM25

```bash
python3 main.py indexer collections/pubmed_2022_tiny.jsonl.gz indexes/bm25/pubmedSPIMIindexTiny \
--tk.minL 2 \
--tk.stemmer potterNLTK \
--indexer.token_threshold 30000 \
--indexer.bm25.cache_in_disk
```

### Searcher

- TFIDF

```bash
python3 main.py searcher <index_file> \
--top_k <TOP_K> \
--path_to_questions questions/questions1.txt \
--output_file results.txt \
ranking.tfidf --ranking.tfidf.smart <smart_notation>
```

Example of running the searcher with query file input:

![Searcher in file input mode](lnc_ltc_results_file.png)


```bash
python3 main.py searcher <index_file>\
--top_k <TOP_K> \
--interactive \
ranking.tfidf --ranking.tfidf.smart <smart_notation>
```

Example of running the searcher in interactive mode (with pagination):

![Searcher in interactive mode](lnc_ltc_interactive.png)

In **interactive mode**, the user doesn't need to give the program a file containing all the queries. Instead, when using the ```bash --interactive``` argument, the program asks the user to insert the query manually and is presented with a paginator containing all the results (10 per page). The number of pages in the paginator depends on the value of the *top_k* argument and the user is allowed to go to the previous/next page, if it's in the defined limit.

- BM25

```bash
python3 main.py searcher pubmedSPIMIindexTiny \
--top_k <TOP_K> \
--interactive \
ranking.bm25 --ranking.bm25.k1 <k\1> --ranking.bm25.b <b>
```

# SPIMI Index - Assignment 3



## Introduction

The purpose of this assignment is to extend the previous indexing and retrieval system. For that, we need to update the indexer to support term positions storage. 

Besides that, we also need to update the retrieval system to allow the boost of documents' scores that contain all query terms according to the minimum window size. The minimum window size is a parameter that determines the smallest number of tokens that can be included in a sliding window as it is moved over the text being searched. It's important in information retrieval since the relevance of a document should be bigger when search terms are closer together. Thus, document A (contains all query terms) with a window size of 10 is more relevant than document B (contains all query terms) with a window size of 200 and, therefore, should have a bigger boost than document B. For large values of the window size, and when the document does not contain all search terms, the boost factor should be 1.



## Indexer

After receiving the filtered terms of a document from the tokenizer, the indexer iterates through ea ch token and stores the positions of itself on the last read document. All the other things are processed in the same way as they did. However, when writing to disk, the format follows the format ```term doc_id:term_weight:[pos1,pos2,pos3];doc_id:term_weight:[pos1,pos2,pos3]...``` instead of ```term doc_id:term_weight,doc_id:term_weight...```.



## Searcher

The searcher also works the same way as before, supporting both TFIDF and BM25 ranking methods and interactive or automatic search. In addition to this, searcher now supports document boosting for documents that contain all query terms. The difference between the boost factor of the documents that match these requirements is related to the minimum window size. As explained previously, the largest the window, the smallest the boost.

To calculate the minimum window size of a document according to the search terms, the program begins by calculating all possible combinations, iterates through each one of them and check if the distance between the maximum and minimum element of the combinations is less than the current minimum distance, updating the variable if that is the case.

The formula used to calculate the boost factor of document is:

```
boost_factor = boost ** (1/(min_window_size/2))
```

Since we are using natural language questions as queries, we only consider high IDF terms when finding the minimum window. For the question “Which phosphatase is inhibited by LB-100?”, for example, the terms considered when finding the minimum window would be “phosphatase inhibited LB-100”(assuming these terms have high IDF). If the number of query tokens is equal or less than 10, all tokens are considered for calculating the minimum window size. However, when the number of tokens is ]10,20], the 25% lowest IDF tokens are removed from the query and, when the number of tokens is bigger than 20, only half of the query tokens are considered (the ones with bigger IDF values as well).


## How to run (with boost)

### Batch Mode

#### TFIDF

```bash
python3 main.py searcher INDEX_FOLDER \
--top_k K \
--path_to_questions PATH_TO_QUESTIONS \
--reader.class GsQuestionsReader \
--output_file OUTPUT_FILE --boost BOOST \
ranking.tfidf --ranking.tfidf.smart <smart_notation>
```

#### BM25 

```bash
python3 main.py searcher INDEX_FOLDER \
--top_k K \
--path_to_questions PATH_TO_QUESTIONS \
--reader.class GsQuestionsReader \
--output_file OUTPUT_FILE --boost BOOST \
ranking.bm25 --ranking.bm25.k1 K --ranking.bm25.b B
```

### Interactive Mode

In **interactive mode**, the user doesn't need to give the program a file containing all the queries. Instead, when using the ```bash --interactive``` argument, the program asks the user to insert the query manually and is presented with a paginator containing all the results (10 per page). The number of pages in the paginator depends on the value of the *top_k* argument and the user is allowed to go to the previous/next page, if it's in the defined limit.

#### TFIDF

```bash
python3 main.py searcher INDEX_FOLDER \
--top_k K \
--interactive \
--boost B \
ranking.tfidf
```

#### BM25 

```bash
python3 main.py searcher INDEX_FOLDER \
--top_k K \
--interactive \
--boost BOOST \
ranking.bm25 --ranking.bm25.k1 K --ranking.bm25.b B
```


