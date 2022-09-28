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



