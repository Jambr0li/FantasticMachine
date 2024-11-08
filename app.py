from flask import Flask, render_template, request
from whoosh_search.whoosh import Whoosh_Search

app = Flask(__name__)
search = Whoosh_Search()

@app.route("/", methods=["GET","POST"])
def home():
    if request.method == "POST":
        query = request.form.get("query", "")
        results = search.retrieve(query)
        return render_template("home.html", results=results)
    return render_template("home.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000, debug=True)