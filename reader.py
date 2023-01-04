"""
Authors:
Gonçalo Leal - 98008
Ricardo Rodriguez - 98388
"""

import os
import gzip
import json
from time import time
from utils import dynamically_init_class


def dynamically_init_reader(**kwargs):
    return dynamically_init_class(__name__, **kwargs)


class Reader:
    """
    Top-level Reader class
    
    This loosly defines a class over the concept of 
    a reader.
    
    Since there are multiple ways for implementing
    this class, we did not defined any specific method 
    in this started code.
    """
    def __init__(self, 
                 path_to_collection:str, 
                 **kwargs):
        super().__init__()
        self.path_to_collection = path_to_collection
        
    
class PubMedReader(Reader):
    
    def __init__(self, 
                 path_to_collection:str,
                 **kwargs):
        super().__init__(path_to_collection, **kwargs)
        print("init PubMedReader|", f"{self.path_to_collection=}")
        if kwargs:
            print(f"{self.__class__.__name__} also caught the following additional arguments {kwargs}")

        self.extract_file()

    def read_next_pub(self, fields="*"):

        line = self.file.readline()
        if not line:
            return None, None # fim do ficheiro

        pub_json = json.loads(line)
        pmid = pub_json['pmid']

        if fields == "*":
            return pmid, pub_json
        elif isinstance(fields, list):
            ret = {}
            for key in fields:
                if key not in pub_json:
                    raise KeyError(
                        f"{key} not found"
                    )

                ret[key] = pub_json[key]

            return pmid, ret
        else:
            raise ValueError(
                "fields must be '*' meaning that all key-value pairs should be returned \
                or a list of keys"
            )

        # pub_json = json.loads(line)
        # pmid = pub_json['pmid']
        # pub_terms = pub_json['title'].split() + pub_json['abstract'].split()
        # return pmid, pub_terms

    def extract_file(self):
        self.file = gzip.open(self.path_to_collection, mode="rt")

    def close_file(self):
        self.file.close()

class QuestionsReader(Reader):
    """
    This class will read and provide every query to the searcher function
    """

    def __init__(
        self,
        path_to_questions:str,
        **kwargs
    ):
        super().__init__(path_to_questions, **kwargs)
        # I do not want to refactor Reader and here path_to_collection does not make any sense.
        # So consider using self.path_to_questions instead
        # (but both variables point to the same thing, it just to not break old code)
        self.path_to_questions = self.path_to_collection
        print("init QuestionsReader|", f"{self.path_to_questions=}")
        if kwargs:
            print(
                f"{self.__class__.__name__} also caught the following additional arguments {kwargs}"
            )
        self.open_file()
        self.id = 0

    def read_next_question(self):
        """
        Read next query/question from questions file
        Returns the id of the question (incremental starting in 1) and
        a list with all the words on the query
        """
        line = self.questions_file.readline()
        if not line:
            self.questions_file.close()
            return None # end of file

        self.id += 1
        return self.id, line.strip().split(" ")

    def open_file(self):
        """
        Check if file exists and open it
        """
        if self.path_to_questions == "":
            return
        if not os.path.exists(self.path_to_questions):
            raise FileNotFoundError
        if not os.path.isfile(self.path_to_questions):
            raise IsADirectoryError
        if os.path.splitext(self.path_to_questions)[1] != ".txt":
            raise Exception("only txt files allowed")

        self.questions_file = open(self.path_to_questions, "r")
class GsQuestionsReader(Reader):
    """
    This class will read and provide every query to the searcher function
    """

    def __init__(
        self,
        path_to_questions:str,
        **kwargs
    ):
        super().__init__(path_to_questions, **kwargs)
        # I do not want to refactor Reader and here path_to_collection does not make any sense.
        # So consider using self.path_to_questions instead
        # (but both variables point to the same thing, it just to not break old code)
        self.path_to_questions = self.path_to_collection
        print("init GsQuestionsReader|", f"{self.path_to_questions=}")
        if kwargs:
            print(
                f"{self.__class__.__name__} also caught the following additional arguments {kwargs}"
            )
        self.open_file()

    def read_next_question(self):
        """
        Read next query/question from questions file
        Returns the question id and a list with all the words on the query
        """
        line = self.questions_file.readline()
        if not line:
            self.questions_file.close()
            return None # end of file

        return 1, line.strip().split(" ")

    def read_next_result(self):
        """
        Read the results from the next query from questions file
        Returns the question id and a list with all the results
        """
        line = self.questions_file.readline()
        if not line:
            self.questions_file.close()
            return None

        return line.strip().split(" ")

    def open_file(self):
        """
        Check if file exists and open it
        """
        if self.path_to_questions == "":
            return
        if not os.path.exists(self.path_to_questions):
            raise FileNotFoundError
        if not os.path.isfile(self.path_to_questions):
            raise IsADirectoryError
        if os.path.splitext(self.path_to_questions)[1] != ".txt":
            raise Exception("only txt files allowed")

        self.questions_file = open(self.path_to_questions, "r")
