from flask import Flask, render_template, request
from whoosh_search.whoosh import Whoosh_Search
from ai_search.searcher import AISearcher
import base64

app = Flask(__name__)
search = Whoosh_Search()
ai = AISearcher()

@app.route("/", methods=["GET","POST"])
def home():
    if request.method == "POST":
        query = request.form.get("query", "")
        inquire = request.form.get("inquire", "")

        if query:
            print("query")
            results = search.retrieve(query)
            return render_template("home.html", results=results, query=query)
        
        elif inquire:
            print("inquiry")
            ai_results = ai.search(inquire)
            return render_template("home.html", ai_response=ai_results, inquire=inquire)
        
    return render_template("home.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000, debug=True)