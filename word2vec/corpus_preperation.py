import os
import string
import pickle
from bs4 import BeautifulSoup
import tqdm

def clean_text(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    text = soup.get_text()
    translator = str.maketrans('', '', string.punctuation)
    text = text.translate(translator)
    text = text.lower()
    tokens = text.split()
    return tokens

def get_corpus():
    corpus_file = 'word2vec/corpus.pkl'
    if os.path.exists(corpus_file):
        # Load the preprocessed corpus from disk
        with open(corpus_file, 'rb') as f:
            corpus = pickle.load(f)
        print("Loaded corpus from disk.")
    else:
        # Process and clean the corpus
        corpus = []
        html_directory = "sites"
        for file_name in tqdm.tqdm(os.listdir(html_directory), desc="Tokenizing corpus..."):
            file_path = os.path.join(html_directory, file_name)
            with open(file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
                tokens = clean_text(html_content)
                corpus.append(tokens)
        # Save the corpus to disk
        with open(corpus_file, 'wb') as f:
            pickle.dump(corpus, f)
        print("Processed and saved corpus to disk.")
    return corpus

get_corpus()