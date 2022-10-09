from ossaudiodev import SNDCTL_COPR_WCODE
from utils import dynamically_init_class
import nltk

from os.path import exists

def dynamically_init_tokenizer(**kwargs):
    return dynamically_init_class(__name__, **kwargs)
    

class Tokenizer:
    
    def __init__(self, **kwargs):
        super().__init__()
    
    def tokenize(self, terms):

        # If there's an established mininum lenght for word filtering
        #if self.minL:
        #    data = [el for el in data if len(el) < self.minL]

        # [Ricardo]
        # Depois de correr o stemmer pode haver mais tokens que fiquem com menos que minL, 
        # por isso, acho que podemos correr isto no final.
        # Talvez o mais correto até seja correr aqui voltar a correr depois do stemmer

        # Stopword filter (specified or default)
        if self.stopwords_path and exists(self.stopwords_path):
            stopwords_file = open(self.stopwords_path, 'r')
            stopwords = [word.strip() for word in stopwords_file.readlines()]
            stopwords_file.close()
        elif self.stopwords_path and not exists(self.stopwords_path): 
            # o ficheiro especificado não existe (mas não é None)
            raise FileNotFoundError(f"Stopwords file not found: {self.stopwords_path}")       
        else:
            # [Ricardo] Acho que se não for especificado um ficheiro de stopwords, então não devemos aplicar nenhum filtro
            stopwords = set([]) #set(nltk.corpus.stopwords.words("english"))

        ret = {}
        #Stemming and Filtering
        if self.stemmer:
            stemmer_obj = self.get_stemmer(self.stemmer)
            
        for t in terms:
            stem_t = stemmer_obj.stem(t.lower()) if self.stemmer else t.lower()
            if stem_t not in stopwords and (len(stem_t) > self.minL): # aqui é o t ou o stem_t?
                if stem_t not in ret:
                    ret[stem_t] = set([])

                ret[stem_t].update(terms[t])

        # falta filtrar melhores or termos

        return ret

    def get_stemmer(self, stemmer_name):
        # This function is used to get the stemmer object
        # Disclaimer: This function was not written by us

        if stemmer_name == "porterNLTK":
            return nltk.stem.PorterStemmer()
        elif stemmer_name == "snowballNLTK":
            return nltk.stem.SnowballStemmer("english")
        elif stemmer_name == "lancasterNLTK":
            return nltk.stem.LancasterStemmer()
        else:
            return None

        
class PubMedTokenizer(Tokenizer):
    
    def __init__(self, 
                 minL, 
                 stopwords_path, 
                 stemmer, 
                 *args, 
                 **kwargs):
        
        super().__init__(**kwargs)
        self.minL = minL
        self.stopwords_path = stopwords_path
        self.stemmer = stemmer
        print("init PubMedTokenizer|", f"{minL=}, {stopwords_path=}, {stemmer=}")
        
