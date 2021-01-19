#!/usr/bin/env python
# coding: utf-8

# In[1]:


import urllib.request
import urllib.response
import urllib.parse
import urllib.error
import json, requests, xmltodict, lxml, sys
from collections import OrderedDict
from lxml import etree
from io import BytesIO


# In[ ]:


get_ipython().system('pip install xmltodict')


# In[2]:


def getAPIprefix() -> str:
  """
  Detect functioning DBpedia lookup API
  DBpedia error codes:
  CODES = {}
  CODES = 
  CODES[481]= "Authentification credentials were missing or authentification failed"
  CODES[484]
  """
  prefixes = ["https://lookup.dbpedia.org/api/search/PrefixSearch?QueryString=",
  "http://lookup.dbpedia.org/api/search/PrefixSearch?QueryString=",
  "https://lookup.dbpedia.org/api/prefix?query=",
  "http://lookup.dbpedia.org/api/prefix?query=",
  "http://akswnc7.informatik.uni-leipzig.de/lookup/api/search?query="]
  for prefix in prefixes:
      with urllib.request.urlopen(prefix + "Antwerp") as test:
          if test.status == 200:
              return prefix
  sys.exit("No functioning DBpedia lookup API found!")
DBPEDIA_PREFIX = getAPIprefix()


# In[3]:


def clean(string: str) -> str:
  """Clean input string and URL encode"""
  string = string.strip()
  string = string.casefold()
  string = urllib.parse.quote(string)
  return string


# In[4]:


def query_dbpedia (search):
  """
  Query DBpedia API, return response or exit with errorcode
  The API response, see e.g. {prefix}mockingbird, will be XML which refers to the ontology of each result.
  For books look for http://dbpedia.org/ontology/Book
  """
  search = clean(search)
  url= DBPEDIA_PREFIX+ search
  try:
    with urllib.request.urlopen(url) as query:
      return query.read() 
  except urllib.error.HTTPError as HTTPerr:
    exit(CODES.get(HTTPerr.code))
  except urllib.error.URLError as URLerr:
    exit(URLerr)


# In[5]:



def transform_dbpedia_response_to_list(xml_input):
  """
  Filter the given xml input and only select the results that are tagged within the /onthology/Book category
  Parses the XML response and extracts the result. If there are several, 
  we allow the user to pick one before continuing to the resource itself (i.e. XML to JSON)
  """
  tree = lxml.etree.fromstring(xml_input)
  results = tree.iter("Result")
  book_uris = []
  for result in results:
    children = result.getchildren()
    uri = ''
    for child in children:
      if child.tag == 'URI':
        uri = child.text
      elif child.tag == 'Classes':
        classes = child.getchildren()
        for item in classes:
          child_uri = item.find('URI').text
          if child_uri == 'http://dbpedia.org/ontology/Book':
            # http://dbpedia.org/resource/search' to http://dbpedia.org/data/search'
            book_uris.append(uri.replace("/resource/", "/data/")+".json")
  return book_uris


# In[6]:


def extract_book_data_from_json(json):
  book_data = {
      "name": "",
      "author": "",
      "publisher": "",
      "published_when": None,
      "abstract": "",
      "pages": 0,
      "genre": ""
  }
  for global_key, val in json.items():
    for key, metadata in val.items():
      if key == 'http://xmlns.com/foaf/0.1/name':
        book_data["name"] = metadata[0]["value"]
      elif key == 'http://purl.org/dc/elements/1.1/publisher':
        book_data["publisher"] = metadata[0]["value"].replace("http://purl.org/dc/elements/1.1/publisher", "").replace("_", " "),metadata[0]["value"]
      elif key == 'http://dbpedia.org/property/publisher':
        book_data["publisher"] = metadata[0]["value"].replace("http://dbpedia.org/property/publisher", "").replace("_", " "),metadata[0]["value"]
      elif key == 'http://dbpedia.org/ontology/publisher':
        book_data["publisher"] = metadata[0]["value"].replace("http://dbpedia.org/ontology/publisher", "").replace("_", " "),metadata[0]["value"]
      elif key == 'http://dbpedia.org/property/pages':
        book_data["pages"] = metadata[0]["value"]
      elif key == 'http://dbpedia.org/property/author':
        book_data["author"] = metadata[0]["value"].replace("http://dbpedia.org/resource/", "").replace("_", " ")
      elif key == 'http://dbpedia.org/ontology/author':
        book_data["author"] = metadata[0]["value"].replace("http://dbpedia.org/resource/", "").replace("_", " "),metadata[0]["value"]
      elif key == 'http://dbpedia.org/property/genre':
        book_data["genre"] = metadata[0]["value"].replace("http://dbpedia.org/resource/", "").replace("_", " "),metadata[0]["value"]
      elif key == 'http://dbpedia.org/ontology/abstract':
        for item in metadata:
          for subkey,subvalue in item.items():
            if subvalue == 'en':
              book_data["abstract"] = item["value"]
        #book_data["abstract"] = metadata
         #for subkey, subvalue in metadata.items():
          #  if subvalue == 'en':
           #   book_data["abstract"] = metadata["value"]
      elif key == 'http://dbpedia.org/property/published':
        book_data["published_when"] = metadata[0]["value"]  
  return book_data


# In[10]:


#MAIN


def main():
  query = input("What book do you want to search for?")
  xml_response = query_dbpedia(query)
  list_of_uris = transform_dbpedia_response_to_list(xml_response)
  
  if len(list_of_uris) == 0:
    print("No books found, Please try to specify")
    sys.exit()
#Make selection from multiple books
  the_book = list_of_uris[0]
  if len(list_of_uris) > 1:
    print("Multiple books have been found:")
    print(list_of_uris)
    book_number = input("Please type the number of the the book you searched for (1-" + str(len(list_of_uris)) + ")")
    if int(book_number) > len(list_of_uris):
      book_number = 1
    the_book = list_of_uris[int(book_number) - 1]
  
  # Retrieve the book JSON
  with urllib.request.urlopen(the_book) as file:
    file = file.read()
    file = json.loads(file)
  
  book_data = extract_book_data_from_json(file)
  print("\n")
  for key, val in book_data.items():
    print(key + ": " + str(val))
    print("\n")


# In[ ]:




