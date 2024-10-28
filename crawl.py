## Noah Denley
## CS 454
## Washington State University
## Ben McCamish
import re
import requests
from hashlib import sha256
from bs4 import BeautifulSoup
from collections import deque
from urllib.parse import urlparse, urljoin, quote
from tqdm import tqdm
import time

DEBUG = False
root_scheme = "https"
root_host = "www.nps.gov"
root_url = f"{root_scheme}://{root_host}"

def is_relative(url):
    return not url.scheme and not url.netloc and url.path.startswith("/")

def complete_link(link):

    # Parse the url
    url = urlparse(link)
    url = url._replace(fragment='', query='')
    if url.netloc and url.netloc != root_host: return None

    # If hostname matches root, it's absolute but within the root domain
    if url.hostname == root_host: url = url._replace(scheme=root_scheme)

    # If url has no scheme and no netloc, it's probably relative.
    if not url.scheme and not url.netloc:
        url = url._replace(scheme=root_scheme, netloc=root_host)
    
    return url.geturl().rstrip("/")

if __name__ == "__main__":
    
    start = time.time()
    outgoing_links = {}
    # # Initialize Q with set of URL links
    visited = set()
    visited.add(root_url)
    queue = deque([root_url])

    # Debug variables
    links_scanned = 0
    repeat_count = 0
    final = []


    while queue:
    #for i in tqdm(range(100), desc="Crawling..."):

        if DEBUG: input(f"Next link - [{queue[0]}]\nPress any key to continue...")

        # Pop URL L from front of queue (left side)
        link = queue.popleft()
        links_scanned += 1
        if link in outgoing_links: continue

        try:
            # If L is not an HTML Page
            response = requests.get(link)
            
            if not "text/html" in response.headers["content-type"]:
                if DEBUG: print("[!] Not HTML")
                continue
            
            # parse page with soup
            soup = BeautifulSoup(response.content, "html.parser")    # Save content or continue loop

            # Download page P for L(call requests.get())
            with open(f"./sites/{sha256(link.encode()).hexdigest()}", "w+", encoding="utf-8") as f:
                f.write(soup.prettify())
            print(f"Scanning {link}...")
            N=[]
            for tag in soup.find_all(href=True):
                full_link = complete_link(tag["href"])
                if full_link not in visited and full_link is not None:
                    visited.add(full_link)
                    N.append(full_link)
                    queue.append(full_link)
            
            if DEBUG:
                for link in N:
                    print(link)
            final.append(link)
            outgoing_links[link] = N
        
        except Exception as e:
            if e is KeyboardInterrupt: exit()
            print(f"[!] Error accessing {link}.")
        
    #final = [link for link in outgoing_links]
    #final.sort()
        
    end = time.time()
    hours, rem = divmod(end-start, 3600)
    minutes, seconds = divmod(rem, 60)
    print("Total crawl time: {:0>2}:{:0>2}:{:05.2f}".format(int(hours),int(minutes),seconds))
    print(f"Total Links Searched: {links_scanned}\nTotal Repeats: {repeat_count}")
    with open("links.txt", "w+") as f:
        for link in final:
            f.write(link+"\n")