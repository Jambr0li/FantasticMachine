import tqdm
import os
from bs4 import BeautifulSoup
import base64
import re

count = 0

for document in tqdm.tqdm(os.listdir("../sites"), desc="Cleaning & Filtering sites..."):
    try:
        # Decode the filename from base64 to get the original URL
        url = base64.urlsafe_b64decode(document.encode()).decode()

        # Read the content of the HTML file
        with open(os.path.join("../sites", document), "r", encoding="utf-8") as file:
            # Parse the HTML content
            soup = BeautifulSoup(file.read(), "html.parser")

            content = soup.get_text()

            content = re.sub(r"[^a-zA-Z0-9\s]", "", content)
            content = re.sub(r"\s+", " ", content)

            # Split the content into words
            words = content.split()

            # Group words into chunks of 20 and join with newlines
            lines = [' '.join(words[i:i+20]) for i in range(0, len(words), 20)]
            content = '\n'.join(lines)

            if len(content) > 1500:
                with open(f"data/sites/{document}.txt", "w+", encoding="utf-8") as out:
                    out.write(content)
                count += 1

    except Exception as e:
        print(f"Error processing file {document}: {e}")

print(f"Found {count} files with less than 1500 characters.")