import os
import string
from whoosh.index import create_in, open_dir
from whoosh import index
from whoosh.fields import Schema, TEXT, ID
from whoosh.qparser import QueryParser, AndGroup, OrGroup
from bs4 import BeautifulSoup
import base64
import tqdm

class Whoosh_Search:
    # intializes data and builds the index
    def __init__(self): 
        self.return_count = 10
        schema = Schema(file_name=ID(stored=True, unique=True), cleaned_content=TEXT(stored=True))
        indexdir = "indexdir"
        self.indexed = False
        self.and_group = True
        if not os.path.exists(indexdir): # Check if index exists already
            os.mkdir(indexdir)
            self.ix = create_in(indexdir, schema)
            self.write()
        else:
            self.ix = open_dir(indexdir)
            self.indexed = True

    # Creates a cleaned version of the content in each file
    def clean_text(self, html_content):
        # remove HTML 
        soup = BeautifulSoup(html_content, 'html.parser')
        text = soup.get_text()
        # remove punctuation
        translator = str.maketrans('', '', string.punctuation)
        text = text.translate(translator)
        # remove whitespace
        text = ' '.join(text.split())
        return text.lower()  # make all  lowercase 
    
    # loads data into the whoosh index
    def write(self):
        writer = self.ix.writer()
        html_directory = "sites" # This is the name of the directory with the content we want to parse
        if self.indexed: # If already indexed then we skip 
            doc_count = self.ix.doc_count()
            print(f"The index contains {doc_count} documents.")
            return

        for file_name in tqdm.tqdm(os.listdir(html_directory), desc="Indexing files..."):
            file_path = os.path.join(html_directory,file_name)
            # check if file is already in the index
            with self.ix.searcher() as searcher:
                query = QueryParser("file_name", self.ix.schema).parse(f'"{file_name}"')
                results = searcher.search(query, limit=10)
                if results:
                    continue

            try:
                with open(file_path, 'r', encoding='utf-8') as f: # load in the data
                    html_content = f.read()
                    cleaned_content = self.clean_text(html_content)
                    writer.add_document(
                        file_name=file_name,
                        cleaned_content=cleaned_content
                    )
            except Exception as e:
                print(f"Error with file {file_name}: {e}")
        writer.commit()
        doc_count = self.ix.doc_count()
        self.indexed = True
        print(f"The index contains {doc_count} documents.")

    # performs the search
    def retrieve(self,query_string):
        with self.ix.searcher() as searcher:
            query = QueryParser("cleaned_content", self.ix.schema,group=AndGroup).parse(query_string) if self.and_group else QueryParser("cleaned_content", self.ix.schema,group=OrGroup).parse(query_string)
            results = searcher.search(query,limit=self.return_count)
            print(f"Found {len(results)} results for query: {query_string}")
            count = min(self.return_count, len(results))
            # count = self.return_count if len(results) >= self.return_count else len(results)
            if count == 0:
                print("No results found for query: {query_string}")
                return [] 
            else: 
                print(f"First {count} result:")
                result_items = []
                for result in results[:count]:
                    file_name = result['file_name']
                    content_snippet = result['cleaned_content'][:200]
                    # result_items.append({
                        # 'file_name': file_name,
                        # 'content_snippet': content_snippet
                    # })
                    result_items.append((base64.urlsafe_b64decode(file_name.encode()).decode(), content_snippet))
                return result_items
                # for i in range(count):
                    # print(file_names[i])
                # return file_names 

    # rebuilds the index by setting the indexed flag to false and calling write()
    def rebuild(self):
        self.indexed = False
        self.write()

    # returns the number of tuples in the index
    def get_tuple_count(self):
        return self.ix.doc_count()

    # updates the maximum return count value 
    def set_return_count(self, count):
        self.return_count = count

searcher = Whoosh_Search()