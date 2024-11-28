from gensim.models import Word2Vec
from corpus_preperation import get_corpus

def train_model():
    corpus = get_corpus()
    print("Got the word2vec cleaned data")
    model = Word2Vec(sentences=corpus, vector_size=100, window=5, min_count=2, workers=4)
    model.save("word2vec/model/word2vec.model")
    print("Word2Vec model trained and saved.")

if __name__ == "__main__":
    train_model()