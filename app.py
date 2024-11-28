from flask import Flask, render_template, request
from whoosh_search.whoosh import Whoosh_Search
from ai_search.searcher import AISearcher
from gensim.models import Word2Vec

app = Flask(__name__)
search = Whoosh_Search()
ai = AISearcher()

model = Word2Vec.load("word2vec/model/word2vec.model")

@app.route("/", methods=["GET","POST"])
def home():
    if request.method == "POST":
        query = request.form.get("query", "")
        inquire = request.form.get("inquire", "")

        if query:
            print("query")
            regular_results = search.retrieve(query)

            # get the related words from my word2vec model
            query_words = query.lower().split()
            related_words = []
            for word in query_words:
                if word in model.wv.key_to_index:
                    similar = [w for w, _ in model.wv.most_similar(word, topn=5)]
                    related_words.extend(similar)
                
            # remove duplicates
            similar_words = list(set(related_words) - set(query_words))

            extended_query = ' '.join(related_words)

            related_results = search.retrieve(extended_query) if extended_query else []

            return render_template(
                "home.html",
                regular_results=regular_results,
                related_results=related_results,
                related_words=similar_words, 
                query=query)
        
        elif inquire:
            print("inquiry")
            ai_results = ai.search(inquire)
            return render_template("home.html", ai_response=ai_results, inquire=inquire)
        
    return render_template("home.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000, debug=True)