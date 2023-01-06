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

