# SPIMI Index - RI Assignment 1

This assigment's objective was to code a document indexer using the SPIMI strategy. We decided to develop our indexer in a way that it would be easy to search a term in the future. In order to achieve that we did not merge all the blocks of terms into a single file. Instead, we created several blocks of terms and wrote an index file so we know in which block file a specific term is.

## Our Approach

In this section we will describe how we solved all the steps of this assignment.

### Reading the file

### Creating tokens

### Indexing

### Merging

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

| File Size | Total Indexing Time | Index Size on Disk | Number of Temporary Files | Number of Terms |
|---|---|---|---|---|
| Tiny (134,4 MB) | 00:06:46 | 8.17426586151123 MB | 51 | 388222 |
| Small (1,4 GB) | | | | |
| Medium (4,4 GB) | | | | |
| Large (9,5 GB) | | | | |