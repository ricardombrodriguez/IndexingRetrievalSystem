#!/bin/bash

cd ..

echo "Index Tiny file"

echo "--------Tiny--------" >> stats.txt
echo "TFIDF - lnc.ltc" >> stats.txt
python3 main.py indexer collections/pubmed_2022_tiny.jsonl.gz indexes/lnc_ltc/pubmedSPIMIindexTiny \
--tk.minL 2 \
--tk.stemmer potterNLTK \
--indexer.token_threshold 30000 \
--indexer.tfidf.cache_in_disk \
--indexer.tfidf.smart lnc.ltc

echo "TFIDF - lnu.ltu" >> stats.txt
python3 main.py indexer collections/pubmed_2022_tiny.jsonl.gz indexes/lnu_ltu/pubmedSPIMIindexTiny \
--tk.minL 2 \
--tk.stemmer potterNLTK \
--indexer.token_threshold 30000 \
--indexer.tfidf.cache_in_disk \
--indexer.tfidf.smart lnu.ltu

echo "BM25" >> stats.txt
python3 main.py indexer collections/pubmed_2022_tiny.jsonl.gz indexes/bm25/pubmedSPIMIindexTiny \
--tk.minL 2 \
--tk.stemmer potterNLTK \
--indexer.token_threshold 30000 \
--indexer.bm25.cache_in_disk

echo "Index Small file"

echo "--------Small--------" >> stats.txt
echo "TFIDF - lnc.ltc" >> stats.txt
python3 main.py indexer collections/pubmed_2022_small.jsonl.gz indexes/lnc_ltc/pubmedSPIMIindexSmall \
--tk.minL 2 \
--tk.stemmer potterNLTK \
--indexer.token_threshold 30000 \
--indexer.tfidf.cache_in_disk \
--indexer.tfidf.smart lnc.ltc

echo "TFIDF - lnu.ltu" >> stats.txt
python3 main.py indexer collections/pubmed_2022_small.jsonl.gz indexes/lnu_ltu/pubmedSPIMIindexSmall \
--tk.minL 2 \
--tk.stemmer potterNLTK \
--indexer.token_threshold 30000 \
--indexer.tfidf.cache_in_disk \
--indexer.tfidf.smart lnu.ltu

echo "BM25" >> stats.txt
python3 main.py indexer collections/pubmed_2022_small.jsonl.gz indexes/bm25/pubmedSPIMIindexSmall \
--tk.minL 2 \
--tk.stemmer potterNLTK \
--indexer.token_threshold 30000 \
--indexer.bm25.cache_in_disk

echo "Index Medium file"

echo "--------Medium--------" >> stats.txt
echo "TFIDF - lnc.ltc" >> stats.txt
python3 main.py indexer collections/pubmed_2022_medium.jsonl.gz indexes/lnc_ltc/pubmedSPIMIindexMedium \
--tk.minL 2 \
--indexer.token_threshold 30000 \
--indexer.tfidf.cache_in_disk \
--indexer.tfidf.smart lnc.ltc

echo "TFIDF - lnu.ltu" >> stats.txt
python3 main.py indexer collections/pubmed_2022_medium.jsonl.gz indexes/lnu_ltu/pubmedSPIMIindexMedium \
--tk.minL 2 \
--indexer.token_threshold 30000 \
--indexer.tfidf.cache_in_disk \
--indexer.tfidf.smart lnu.ltu

echo "BM25" >> stats.txt
python3 main.py indexer collections/pubmed_2022_medium.jsonl.gz indexes/bm25/pubmedSPIMIindexMedium \
--tk.minL 2 \
--indexer.token_threshold 30000 \
--indexer.bm25.cache_in_disk