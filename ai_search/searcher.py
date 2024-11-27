import base64
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

CHROMA_PATH = "chroma"

PROMPT_TEMPLATE = """
Answer the question based only on the following context:

{context}

---

Answer the question based on the above context: {question}

In your response, do not start with "based on the context..." or similar phrases, simply answer the question with confidence.
"""

class AISearcher:
    def __init__(self) -> None:
        
        # Prepare the DB.
        embedding_function = OpenAIEmbeddings()
        self.db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_function)

    def search(self, query_text):
        # Search the DB.
        results = self.db.similarity_search_with_relevance_scores(query_text, k=3)

        # If no results are found, or the best result has a low similarity score, print a message and continue to the next query.
        if len(results) == 0 or results[0][1] < 0.7:
            return f"No response could be made for the inquiry {query_text}.", []

        # Print the context text for the top results.
        context_text = "\n\n---\n\n".join([doc.page_content for doc, _score in results])
        prompt_template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
        prompt = prompt_template.format(context=context_text, question=query_text)

        # Use the OpenAI model to generate a response to the query.
        model = ChatOpenAI()
        response_text = model.invoke(prompt).content

        # Print the response text, as well as the sources of the context documents.
        sources = set([doc.metadata.get("source", None).replace("data\\sites\\", "").rstrip(".txt") for doc, _score in results])
        sources = [base64.urlsafe_b64decode(doc.encode()).decode() for doc in sources]
        print(response_text)
        return response_text, sources

def main():
    
    # Prepare the DB.
    embedding_function = OpenAIEmbeddings()
    db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_function)

    # Search the DB.
    
    while True:
        # Request a query from the user.
        query_text = input("Enter a query, or 'exit' to quit: ")

        if query_text.lower() == "exit":
            exit()
        
        # Search the DB for documents relevant to the query.
        results = db.similarity_search_with_relevance_scores(query_text, k=3)

        # If no results are found, or the best result has a low similarity score, print a message and continue to the next query.
        if len(results) == 0 or results[0][1] < 0.7:
            print(f"Unable to find matching results.")
            print("---")
            continue

        # Print the context text for the top results.
        context_text = "\n\n---\n\n".join([doc.page_content for doc, _score in results])
        print(context_text)
        prompt_template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
        prompt = prompt_template.format(context=context_text, question=query_text)

        # Use the OpenAI model to generate a response to the query.
        model = ChatOpenAI()
        response_text = model.invoke(prompt).content

        # Print the response text, as well as the sources of the context documents.
        print(f"\nResponse: \n  {response_text}\n")
        sources = set([doc.metadata.get("source", None) for doc, _score in results])
        print("Sources:")
        for doc in sources:
            url = doc.replace("data\\sites\\", "").rstrip(".txt")
            url = base64.urlsafe_b64decode(url.encode()).decode()
            print(f"   - {url}")
        print("---")


if __name__ == "__main__":
    main()
