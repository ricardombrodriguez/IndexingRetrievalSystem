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

Duringf the merge process, whenwe already know how many documents exist in the collection, we calculate every term's weight (tf * idf). tf has already been calculated before, idf is calculated before calculating the weight. Our index's final blocks contain an inverted index, but the posting list besides having the document id also stores the term's weight for that document.

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
