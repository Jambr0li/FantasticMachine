import requests
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode
from collections import deque
from bs4 import BeautifulSoup as bs
import pickle
from tqdm import tqdm
from pathlib import Path
import os

## =================================================
## vvv FUNCTIONS vvv 

# Function that determines what links we will accept on each web page
def parse_url(url):
    return str(url).startswith("/") or str(url).startswith("https://coppermind.net") 

# Function that gets the index associated with each URL
# to allow interaction with the adjacency matrix.
# If the url doesn't exist, it adds it to the dictionary
# and the adjacency matrix
def get_url_index(url):
    if url not in url_to_index:
        index = len(url_to_index)
        url_to_index[url] = index
        for row in adjacency_matrix:
            row.append(0)
        adjacency_matrix.append([0] * (len(url_to_index)))
        adjacency_matrix[url_to_index[url]][url_to_index[url]] = 1 # automatically set diagonal to 1
    return url_to_index[url]

# This function removes paramaters from the url so that the urls that are stored are unique
def normalize_url(url):
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query) # Get the parameters
    query_params.pop('mobileaction', None) # Remove these parameters
    query_params.pop('returnto', None)
    query_params.pop('returntoquery', None)
    query_params.pop('?title', None)
    query_params.pop('redlink', None)
    normalized_query = urlencode(query_params, doseq=True) # Rebuild the URL without these parameters
    normalized_url = urlunparse(parsed_url._replace(query=normalized_query))
    return normalized_url

# This function takes in a url and crawls the page.
# It retrieves every viable link from the page and records it. 
def crawl_page(url):
    response = requests.get(url) # Get the info from the page
    soup = bs(response.text, 'html.parser') # Parse the html
    links = soup.find_all('a',href=parse_url) # Find all <a> links 
    current_index = get_url_index(url) # Get current index in order to interact with adjacency matrix
    for link in links: # Loop over each link found
        href = str(link.get('href')) # Convert the url to a string
        if href.startswith("/"): # Check if it is relative
            href = "https://coppermind.net" + href  # add base domain if it is relative
        href = normalize_url(href)
        if href.startswith("https://coppermind.net") and is_allowed(href,rules):
            if href.startswith("https://coppermind.net/wiki/Special:"):
                print(f"{href} got through!! How!!!")
            target_index = get_url_index(href) # get index of link found on current page
            adjacency_matrix[current_index][target_index] = 1 # Update adjacency matrix
            if href not in visited_pages:
                visited_pages.add(href)  # Add to visited pages
                link_queue.append(href)  # Add new link to the queue
    file_name = url.replace("/", "_")  # Replace slashes with underscores in the URL
    file_path = f"./html_files/{file_name}.html"  # Specify the file path with .html extension
    if (not Path(file_path).exists()): # Check if file is already stored
        with open(file_path, "w") as file:
            file.write(response.text)  # Write the HTML content to the file
    if count % pickling_save_rate == 0: # Save variables to pickle for every 100 files
        data = (visited_pages, link_queue, adjacency_matrix, url_to_index,count)
        with open('data.pickle', 'wb') as file:
            pickle.dump(data,file)

# Parse robots.txt
def parse_robots_txt(content):
    rules = [] # this list will store what pages cannot be crawled
    rules.append("https://coppermind.net/wiki/?title=Special:")
    for line in content.splitlines(): # Get each line of robots.txt
        line = line.strip()
        if line.startswith('Disallow:'): # If it is disallowed then add it do the list
            path = line.split(':', 1)[1].strip()
            if path.endswith('*'):
                path = path[:-1]
            path = "https://coppermind.net" + path
            rules.append(path)
    return rules

# Custom function to check if a URL is allowed
# It compares if the current url matches any of the disallowed pages
def is_allowed(url, rules):
    for rule in rules:
        if url.startswith(rule):
            return False
    return True

## ^^^ FUNCTIONS ^^^
## ================================================= 

# Get robots.txt content
response = requests.get("https://coppermind.net/robots.txt")
robots_content = response.text
rules = parse_robots_txt(robots_content)


# Initialize variables 
max_count = 5000 # Change this variable to adjust how many pages the program collects
pickling_save_rate = 100 # Change this variable to adjust how frequently the data is saved to 'data.pickle'
visited_pages =  set()
link_queue = deque()
adjacency_matrix = []
url_to_index = {}
count = 0
# seed_url = 'https://www.17thshard.com/'
# seed_url = 'https://www.nps.gov/index.htm'
seed_url = 'https://coppermind.net/wiki/Coppermind:Welcome'
# Create html_files directory if it doesn't exist
os.makedirs('html_files',exist_ok=True)

# Check if data exists in pickle file
pickle_file = Path('data.pickle')
if pickle_file.exists(): # If pickle file exists then load the stored data
    with open(pickle_file, 'rb') as file:
        visited_pages, link_queue, adjacency_matrix, url_to_index, count = pickle.load(file)
else: # otherwise initialize the program with the seed_url
    link_queue.append(seed_url)
    visited_pages.add(seed_url)

# Crawl until we reach max page count or queue is empty
# Use tqdm to visualize progress
with tqdm(total=max_count, initial=count) as pbar:
    while(count < max_count and len(link_queue) > 0):
        page = link_queue.pop() # Get next page from queue
        crawl_page(page)
        count += 1 # Increment count of crawled pages
        pbar.update(1)
        print(f"Link queue size is {len(link_queue)}")
        print(f"Currently crawling {page}")
