from flask import Flask, render_template, request
from whoosh_search.whoosh import Whoosh_Search
from ai_search.searcher import AISearcher
from gensim.models import Word2Vec
import string

app = Flask(__name__)
search = Whoosh_Search()
ai = AISearcher()

model = Word2Vec.load("word2vec/model/word2vec.model")
print(model)

@app.route("/", methods=["GET","POST"])
def home():
    if request.method == "POST":
        query = request.form.get("query", "")
        inquire = request.form.get("inquire", "")
        page = int(request.form.get("page", 1))

        query = query.translate(str.maketrans('', '', string.punctuation))

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

            per_page_count = 10
            regular_total_page_count = len(regular_results)
            related_total_page_count = len(related_results)
            regular_pages = (regular_total_page_count - 1) // per_page_count + 1
            related_pages = (related_total_page_count - 1) // per_page_count + 1

            paginated_regular_results = regular_results[(page - 1) * per_page_count : page * per_page_count]
            paginated_related_results= related_results[(page - 1) * per_page_count : page * per_page_count]

            return render_template(
                "home.html",
                regular_results=paginated_regular_results,
                related_results=paginated_related_results,
                related_words=similar_words, 
                page=page,
                regular_pages=regular_pages,
                related_pages=related_pages,
                query=query)
        
        elif inquire:
            print("inquiry")
            ai_results = ai.search(inquire)
            return render_template("home.html", ai_response=ai_results, inquire=inquire)
        
    return render_template("home.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000, debug=True)