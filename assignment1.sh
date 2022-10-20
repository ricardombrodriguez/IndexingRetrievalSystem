#!/bin/bash

# bash command to solve the assignment 1
python main.py indexer collections/pubmed_2022_tiny.jsonl.gz pubmedSPIMIindexTiny --tk.minL 2 --tk.stemmer potterNLTK --indexer.token_threshold 30000
python main.py indexer collections/pubmed_2022_small.jsonl.gz pubmedSPIMIindexSmall --tk.minL 2 --tk.stemmer potterNLTK --indexer.token_threshold 30000
python main.py indexer collections/pubmed_2022_medium.jsonl.gz pubmedSPIMIindexMedium --tk.minL 2 --tk.stemmer potterNLTK --indexer.token_threshold 30000
python main.py indexer collections/pubmed_2022_large.jsonl.gz pubmedSPIMIindexLarge --tk.minL 2 --tk.stemmer potterNLTK --indexer.token_threshold 30000