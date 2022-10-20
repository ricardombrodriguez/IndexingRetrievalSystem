#!/bin/bash

# bash command to solve the assignment 1
python main.py indexer collections/pubmed_tiny.jsonl pubmedSPIMIindexTiny --tk.minL 2 --tk.stemmer potterNLTK --indexer.token_threshold 30000
python main.py indexer collections/pubmed_small.jsonl pubmedSPIMIindexSmall --tk.minL 2 --tk.stemmer potterNLTK --indexer.token_threshold 30000
python main.py indexer collections/pubmed_medium pubmedSPIMIindexMedium --tk.minL 2 --tk.stemmer potterNLTK --indexer.token_threshold 30000
python main.py indexer collections/pubmed_large pubmedSPIMIindexLarge --tk.minL 2 --tk.stemmer potterNLTK --indexer.token_threshold 30000