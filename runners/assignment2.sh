#!/bin/bash

# bash commands to solve the assignment 2

# tfidf
python3 main.py indexer collections/pubmed_2022_tiny.jsonl.gz indexes/pubmedSPIMIindexTiny --tk.minL 2 --tk.stemmer potterNLTK --indexer.token_threshold 30000 --indexer.tfidf.cache_in_disk --indexer.tfidf.smart lnc.ltc 
python3 main.py indexer collections/pubmed_2022_small.jsonl.gz indexes/pubmedSPIMIindexSmall --tk.minL 2 --tk.stemmer potterNLTK --indexer.token_threshold 30000 --indexer.tfidf.cache_in_disk --indexer.tfidf.smart lnc.ltc
python3 main.py indexer collections/pubmed_2022_medium.jsonl.gz indexes/pubmedSPIMIindexMedium --tk.minL 2 --tk.stemmer potterNLTK --indexer.token_threshold 30000 --indexer.tfidf.cache_in_disk --indexer.tfidf.smart lnc.ltc
python3 main.py indexer collections/pubmed_2022_large.jsonl.gz indexes/pubmedSPIMIindexLarge --tk.minL 2 --tk.stemmer potterNLTK --indexer.token_threshold 30000 --indexer.tfidf.cache_in_disk --indexer.tfidf.smart lnc.ltc