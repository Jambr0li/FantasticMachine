import os

# Parsing
import base64
from bs4 import BeautifulSoup
from urllib.parse import urlparse

# Processing
import tqdm
import numpy as np
import cupy as cp
import scipy.sparse as sp

# Indexing
from whoosh import index
from whoosh.fields import Schema, TEXT, NUMERIC
from whoosh.qparser import QueryParser

"""
Pulled - and slightly modified - from Project 1 to complete links and remove unnecessary elements.
"""
def complete_link(link):

    # If this link is a site resource, don't use it
    if "/w/" in link or "/mw/" in link or "/wiki/Special:" in link: return None

    # Parse the link and remove any unnecessary elements (fragments and queries)
    url = urlparse(link)
    url = url._replace(fragment='', query='')

    # If the url has a netlocation that is not the root, don't use it.
    if url.netloc and url.netloc != "www.coppermind.net": return None

    # All other urls are relative to the root domain
    url = url._replace(scheme="https", netloc="www.coppermind.net")
    
    # Get the final url, stripping any trailing "/"
    final_link = url.geturl().rstrip("/")

    # Dont return empty links or disallowed links
    return final_link


"""
Generates a dictionary of URL indices from the filenames in the "sites" directory,
where the key is the urlsafe decoded URL and the value is the index.
"""
def get_url_indices():
    # Create a dictionary to store the URL indices
    return {base64.urlsafe_b64decode(document.encode()).decode(): i for i, document in enumerate(os.listdir("sites"))}

"""
Creates a sparse adjacency matrix from the HTML files in the "sites" directory.
"""
def create_adj_matrix(url_index):
    # Memmap the adjacency matrix, so it can be stored on disk
    adj_matrix = np.zeros(shape=(len(url_index), len(url_index)), dtype=np.int8)
    for document in tqdm.tqdm(os.listdir("sites"), desc="Filling adjacency matrix..."):
        try:
            # Decode the filename from base64 to get the original URL
            url = base64.urlsafe_b64decode(document.encode()).decode()

            # Read the content of the HTML file
            with open(os.path.join("sites", document), "r", encoding="utf-8") as file:
                content = file.read()

                # Parse the HTML content with BeautifulSoup
                soup = BeautifulSoup(content, "html.parser")

                # Check all hrefs in the page
                for tag in soup.find_all(href=True):
                    # If it is a valid and full link...
                    full_link = complete_link(tag["href"])
                    if full_link and full_link in url_index:
                        if url == full_link: continue
                        #...add it to the adjacency matrix
                        adj_matrix[url_index[url]][url_index[full_link]] += 1

        except Exception as e:
            print(f"Error processing file {document}: {e}")

    # Save the adjacency matrix to disk as a sparse matrix
    sp.save_npz("adj_mat.npz", sp.csr_matrix(adj_matrix))

"""
Calculates the PageRank of the URLs in the adjacency matrix,
using the iterative algorithm described in the project description.
"""
def page_rank(adj_matrix):
    page_count = adj_matrix.shape[0]

    link_counts = [np.sum(row) for row in tqdm.tqdm(adj_matrix, desc="Counting links...")]
    
    print("Initializing link probabilities...")
    transition_matrix = np.zeros(shape=(page_count, page_count), dtype=np.float16)

    for row in tqdm.tqdm(range(page_count), desc="Calculating link probabilities..."):
        if link_counts[row] == 0: continue 

        # Convert the sparse row to a dense array (required for adding the leap probability)
        dense_row = adj_matrix[row, :].toarray().flatten()

        # Calculate the link probabilities, and add the leap probability
        transition_matrix[row, :] = (dense_row / link_counts[row] * 0.9) + 0.1/page_count

        # Remove the dense row from memory
        del dense_row

    # Remove adj_matrix from memory
    del adj_matrix

    # Convert the transition matrix to a GPU array
    tran_mat_gpu = cp.asarray(transition_matrix)

    # Initialize the ranks
    ranks = cp.array([1/page_count] * page_count, dtype=cp.float16)

    # Perform the PageRank iterations
    for _ in tqdm.tqdm(range(20), desc="Iterating PageRank..."):
        ranks = cp.dot(ranks, tran_mat_gpu)

    # Save the PageRanks to disk
    with open("pageranks.dat", "wb") as file:
        cp.save(file, ranks)

    return ranks


"""
Creates an index of the HTML files in the "sites" directory
"""
def create_index(url_index, ranks):
    # Pagerank is stored as a NUMERIC field, so it can be used for sorting
    schema = Schema(url = TEXT(stored=True), content = TEXT, pagerank = NUMERIC(stored=True))

    if not os.path.exists("indexdir"):
        os.mkdir("indexdir")

    ix = index.create_in("indexdir", schema)

    writer = ix.writer()

    for document in tqdm.tqdm(os.listdir("sites"), desc="Indexing documents..."):
        try:
            # Decode the filename from base64 to get the original URL
            url = base64.urlsafe_b64decode(document.encode()).decode()

            # Read the content of the HTML file
            with open(os.path.join("sites", document), "r", encoding="utf-8") as file:
                content = file.read()

                writer.add_document(url=url, content=content, pagerank=ranks[url_index[url]])

        except Exception as e:
            print(f"Error processing file {document}: {e}")

    writer.commit()

def search(query_str):
    # Open the index
    ix = index.open_dir("indexdir")

    # Create a searcher
    with ix.searcher() as searcher:
        # Parse the query
        query = QueryParser("content", ix.schema).parse(query_str)

        # Search the index
        results = searcher.search(query, limit=None)

        # Sort results by PageRank
        sorted_results = sorted(results, key=lambda x: x['pagerank'], reverse=True)

        # Print the results
        for result in sorted_results[:10]:
            print(f"{result['url']}, {result['pagerank']}")
        
        # Print a separator
        print("-"*50)