import gzip

with gzip.open('pubmedSPIMIindexTiny/final_block_1.txt','rb') as f:
    for line in f:
        print(line)