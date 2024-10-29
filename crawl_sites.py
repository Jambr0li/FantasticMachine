## Noah Denley
## CS 454
## Washington State University
## Ben McCamish
import requests
from hashlib import sha256
import base64
from bs4 import BeautifulSoup
from collections import deque
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser
import numpy as np
import pickle
import os

START_NEW = False

class Crawler(object):

    def __init__(self, root_scheme, root_host, save_freq = 50, scan_target = 5000):

        # Domain-related variables
        self.root_scheme = "https"
        self.root_host = "www.nps.gov"
        self.root_url = f"{root_scheme}://{root_host}"

        # Robots parser
        self.rp = RobotFileParser()
        self.rp.set_url(f"{self.root_url}/robots.txt")
        self.rp.read()
        
        # Save-related variables
        self.save_freq = save_freq
        self.scan_target = scan_target

        # START_NEW allows the crawl to be restarted, if set to true.
        if START_NEW:
            self.outgoing_links = {self.root_url: []}
            self.queue = deque([self.root_url])
            self.links_scanned = 0
        else:
            self.load_crawl()

    # Saves the outgoing links dictionary as a adjacency matrix    
    def save_crawl(self):
        # Create index lookup table for indexing the matrix
        url_index = {url: i for i, url in enumerate(list(self.outgoing_links.keys()))}

        # Create empty adjacency matrix
        n = len(self.outgoing_links)
        adj_matrix = np.zeros((n, n), dtype=int)

        # Fill the matrix
        for source, targets in self.outgoing_links.items():
            source_i = url_index[source]
            adj_matrix[source_i][source_i] = 1
            for target in targets:
                target_i = url_index[target]
                adj_matrix[source_i][target_i] = 1

        if not os.path.exists("crawler_pkls"):
            os.mkdir("crawler_pkls")

        # Adjacency Matrix
        with open("crawler_pkls/adj_matrix.pkl", "wb") as f: pickle.dump(adj_matrix, f)
        # Index Lookup
        with open("crawler_pkls/url_index.pkl", "wb") as f: pickle.dump(url_index, f)
        # Queue
        with open("crawler_pkls/url_queue.pkl", "wb") as f: pickle.dump(self.queue, f)
        # Scan Count
        with open("crawler_pkls/scan_count.pkl", "wb") as f: pickle.dump(self.links_scanned, f)

    def load_crawl(self):
        
        try:
            # Adjacency Matrix
            with open("crawler_pkls/adj_matrix.pkl", "rb") as f: adj_matrix = pickle.load(f)
            # Index Lookup
            with open("crawler_pkls/url_index.pkl", "rb") as f: url_index = pickle.load(f)
            # Queue
            with open("crawler_pkls/url_queue.pkl", "rb") as f: self.queue = pickle.load(f)
            # Scan Count
            with open("crawler_pkls/scan_count.pkl", "rb") as f: self.links_scanned = pickle.load(f)
        
            # Flip the lookup table to access indices by url
            index_url = {i: url for url, i in url_index.items()}

            # Build dictionary keys
            self.outgoing_links = {index_url[i]: [] for i in range(len(index_url))}

            for i in range(len(adj_matrix)):
                for j in range(len(adj_matrix[i])):
                    if adj_matrix[i][j] == 1:
                        self.outgoing_links[index_url[i]].append(index_url[j])

        # If a pkl file is not found, just start a new crawl.
        except FileNotFoundError as e:
            print("No existing objects found, starting a new crawl!")
            self.outgoing_links = {self.root_url:[]}
            self.queue = deque([self.root_url])
            self.links_scanned = 0
        

    def begin_crawl(self):
        while self.queue:
            # Pop URL L from front of queue (left side)
            link = self.queue.popleft()

            try:
                print(f"Scanning {link:100} Pages Seen: {len(self.outgoing_links)} | Pages Left To Scan: {len(self.queue) + 1} | Total Pages Scanned: {self.links_scanned}")
                # If L is not an HTML Page
                response = requests.get(link)
                
                # Skip non-html files
                if not "text/html" in response.headers["content-type"]: continue
                
                # Parse page with soup
                soup = BeautifulSoup(response.content, "html.parser")    # Save content or continue loop

                if not os.path.exists("sites"):
                    os.mkdir("sites")

                # Encode and hash the link name for easy file storage, then write the page content to it.
                with open(f"./sites/{base64.urlsafe_b64encode(link.encode()).decode()}", "w+", encoding="utf-8") as f:
                    f.write(soup.prettify())

                # Check all hrefs in the page
                for tag in soup.find_all(href=True):
                    # If it is a valid and full link...
                    full_link = self.complete_link(tag["href"])
                    if full_link and full_link not in self.outgoing_links:
                        #...add it to the dictionary with no outgoing links, add it to the outgoing links from the source, and add it to the queue.
                        self.outgoing_links[full_link] = []
                        self.outgoing_links[link].append(full_link)
                        self.queue.append(full_link)
                
                # Keep track of how many links we scanned for saving
                self.links_scanned += 1
                if self.links_scanned % self.save_freq == 0:
                    self.save_crawl()
                    print("Crawl saved!")
                if self.links_scanned >= self.scan_target:
                    print("Crawl complete!")
                    return

            # Not the best error handling, but it works well enough.
            except Exception as e:
                print(f"[!] Error accessing \'{link}\ - {e}'")

    def complete_link(self, link):

        # If this link is a site resource, don't use it
        if "/common/" in link or "/commonspot/" in link or "./" in link or '/planyourvisit/' in link: return None

        # Parse the link and remove any unnecessary elements (fragments and queries)
        url = urlparse(link)
        url = url._replace(fragment='', query='')

        # If the url has a netlocation that is not the root, don't use it.
        if url.netloc and url.netloc != self.root_host: return None

        # All other urls are relative to the root domain
        url = url._replace(scheme=self.root_scheme, netloc=self.root_host)
        
        # Get the final url, stripping any trailing "/"
        final_link = url.geturl().rstrip("/")

        # Dont return empty links or disallowed links
        return final_link if (final_link and self.rp.can_fetch("*", final_link)) else None


if __name__ == "__main__":
    crawler = Crawler("https", "www.nps.gov", scan_target=3000)
    crawler.begin_crawl()