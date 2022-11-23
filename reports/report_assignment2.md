# SPIMI Index - RI Assignment 2

The purpose of the 2nd assignment is to add term weighting to our indexing system and implement two ranked retrieval models, using the same datasets as the 1st assignment (medical publications). 

The two different ranked retrieval models are:
- Vector space ranking with **tf-idf** weights. We need to implement the *lnc.ltc* indexing schema as default and at least one alternative schema (we chose *lnu.ltu*). The indexing schema to use should be passed as a parameter, using the SMART notation.
- BM25ranking. The default values for the parameters are k1=1.2 and b=0.75 but we allow the specification of other values through command line arguments.

Additionally, we need to implement the search component of the retrieval system. This Searcher should read a previously created index – following one of the ranked retrieval models mentioned above – and process queries,returning a paginator with the best results (10 per page). The program starts the search mechanism and continually (in a loop) accepts user queries from the command line and presents the top 10 results, including the document scores.

## TFIDF

### Indexing

### Searching

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