import os
from helpers import *
import scipy.sparse as sp

# Create the adjacency matrix, if necessary
if not os.path.exists("adj_mat.npz"): 
    # Get the indices of each URL
    url_index = get_url_indices()

    create_adj_matrix(url_index)

# Load the adjacency matrix
adj_matrix = sp.load_npz("adj_mat.npz")

# Calculate the PageRank of each URL, if necessary
if not os.path.exists("pageranks.dat"): 
    page_rank(adj_matrix)
