from flask import Flask, render_template, request
import time
import os
import nltk
import re
from nltk.stem import PorterStemmer
from natsort import natsorted
import string


def clean_document(s):
    # cleaning documents
    s = re.sub('  ', ' ', s)
    s = re.sub(r"won't", "will not", s)
    s = re.sub(r"can\'t", "can not", s)
    s = re.sub(r"n\'t", " not", s)
    s = re.sub(r"\'re", " are", s)
    s = re.sub(r"\'s", " is", s)
    s = re.sub(r"\'d", " would", s)
    s = re.sub(r"\'ll", " will", s)
    s = re.sub(r"\'t", " not", s)
    s = re.sub(r"\'ve", " have", s)
    s = re.sub(r"\'m", " am", s)
    s = re.sub(r'[0-9]+', '', s)
    s = re.sub(r'[^\w\s]', ' ', s)
    return s


def inverted_index():  # Returns the cleaned document and inverted index
    ps = PorterStemmer()
    f = open("Stopword-List.txt")
    stop_words = f.read().replace('\n', ' ')
    stop_words = stop_words.split()
    doc_no = 0
    dictionary = {}
    documents = {}
    folder = "ShortStories"
    file_names = natsorted(os.listdir("ShortStories"))
    for file in file_names:
        doc_no = int(file.replace(".txt", ""))
        # returns the document of file
        print("\nDocument No", file, "\n")
        f = open(folder+"/"+file, "r", encoding="utf-8")
        s = f.read().replace('\n', ' ')
        s = clean_document(s)
        key = str(file.replace(".txt", ""))
        documents.setdefault(key, [])
        documents[key].append(s)

        #  lowercase
        s = s.lower()
        # Tokenization and removing of stopwords
        s = [
            words if words not in stop_words else '' for words in s.split(' ')]
        doc = []
        # s ='', 'kalashnikov', 'greeted', 'him', '', '',
        doc = list(filter(None, s))  # 'kalashnikov', 'greeted', 'him',

        # stemming
        stemmed = []
        for i in doc:
            stemmed.append(ps.stem(i))  # word=stemmed_word(word)

        # creating posting list
        for x in stemmed:
            key = x
            dictionary.setdefault(key, [])
            dictionary[key].append(doc_no)
            # 'hors': [1,2,3,4,6,7,8,9], 'stealer': [1], 'hospit': [1,2,3,4,7],

        # removing duplicates
        dictionary = {a: list(set(b)) for a, b in dictionary.items()}

    # dictionary='hors': [0], 'stealer': [0], 'hospit': [0],
    # documents=THE HORSE STEALERS A HOSPITAL
    return dictionary, documents
# End of Inverted Index Function


def positional_index():  # Returns the cleaned document and positional index
    ps = PorterStemmer()
    dictionary = {}
    documents = {}
    folder = "ShortStories"
    file_names = natsorted(os.listdir("ShortStories"))
    for file in file_names:
        # returns the document of file
        doc_no = int(file.replace(".txt", ""))
        print("\nDocument No", file, "\n")
        f = open(folder+"/"+file, "r", encoding="utf-8")
        s = f.read().replace('\n', ' ')
        s = clean_document(s)
        key = str(file.replace(".txt", ""))
        documents.setdefault(key, [])
        documents[key].append(s)

        #  lowercase
        s = s.lower()
        s = s.split(' ')
        doc = []
        doc = list(filter(None, s))
        temp_dict = {}
        stemmed = []

        # stemming
        for i in doc:
            stemmed.append(ps.stem(i))
        # creating positional index posting lists
        a = 0
        for x in stemmed:
            key = x
            temp_dict.setdefault(key, [])
            temp_dict[key].append(a)
            a += 1
        # dict of dict to store the positions of the word corresponding to the document id’s.
        for x in temp_dict:
            if dictionary.get(x):
                dictionary[x][doc_no] = temp_dict.get(x)
            else:
                key = x
                dictionary.setdefault(key, [])
                dictionary[key] = {}
                dictionary[x][doc_no] = temp_dict.get(x)
    return dictionary, documents


def process_query(q, dictionary_inverted):  # Parse Inverted Index Query
    check_not = False
    not_anded = False
    if("not" in q):
        check_not = True
        q = q.replace("not", "")
    if("and" not in q and "or" not in q and "not" not in q):
        q = q+" and"
    q = q.split(' ')
    query = []
    q = list(filter(None, q))
    print(q)
    ps = PorterStemmer()
    for i in q:
        query.append(ps.stem(i))
    for i in range(0, len(query)):
        if (query[i] == 'and' or query[i] == 'or' or query[i] == 'not'):
            query[i] = query[i].upper()
    results_stack = []

    # evaluating query expression
    for word in query:  # Find and store query words in stack
        if (word != 'AND' and word != 'OR' and word != 'NOT'):
            print("W:", word, "\n")
            word = dictionary_inverted.get(word)
            results_stack.append(word)
            print("Found In:", word, "\n")

    for word in query:  # Find and Query operations
        if (word == 'AND'):
            a = results_stack.pop()
            try:
                b = results_stack.pop()
            except:
                b = a
            results_stack.append(intersection(a, b))
            if(check_not):
                not_anded = True
            # print("R:", results_stack)
        if (word == 'OR'):
            a = results_stack.pop()
            b = results_stack.pop()
            results_stack.append(union(a, b))

        # if query has not operation
        if (not_anded and check_not):
            a = results_stack.pop()
            doc_ids = []
            for i in range(1, 51):
                doc_ids.append(i)
            results_stack.append(NOT_op(a, doc_ids))
            not_anded = False
        print("W:", word)

    result = results_stack.pop()
    try:
        result.sort()
    except:
        pass
    return result


# Parse and Find Positional index phrase query
def process_positional_query(q, dictionary_positional):
    ps = PorterStemmer()
    q = re.sub(r"and", "", q)
    q = re.sub(r"AND", "", q)
    q = re.sub(r"  ", " ", q)
    q = q.split(' ')
    query = []

    for word in q:
        query.append(ps.stem(word))  # Stem before searching in the dictionary

    word1 = dictionary_positional.get(query[0])
    word2 = dictionary_positional.get(query[1])
    intersected = intersection(word1, word2)  # Interaction of query words

    query[2] = re.sub(r"/", "", query[2])
    answer = []
    w_distance = int(query[2]) + 1
    for i in intersected:
        word1_pos = dictionary_positional.get(query[0])[i]
        word2_pos = dictionary_positional.get(query[1])[i]
        len1 = len(word1_pos)
        len2 = len(word2_pos)
        j = k = 0

        # Check distance and match words
        while j != len1:
            while k != len2:
                if (abs(word1_pos[j] - word2_pos[k]) == w_distance):
                    answer.append(i)
                elif word2_pos[k] > word1_pos[j]:
                    break
                k += 1
            j += 1
    result = list(dict.fromkeys(answer))
    return result


# Function to Perform Intersection
def intersection(lst1, lst2):
    try:
        x = list(set(lst1).intersection(lst2))
        return x
    except:
        return None

# Function to Perform Union


def union(lst1, lst2):
    try:
        x = list(set(lst1).union(lst2))
        return x
    except:
        return None

# Function to Perform Not Operation


def NOT_op(a, doc_ids):
    try:
        x = list(set(doc_ids).symmetric_difference(a))
        if(x == None):
            x = doc_ids
        return x
    except:
        return None


# def main():

#     # Testing
#     query = "not strange and not land and not play"

#     query = query.lower().strip()
#     if('/' not in query):
#         Inverted_Dictionary, Document = inverted_index()
#         # Document= Cleaned Orignal Document
#         result = process_query(query, Inverted_Dictionary)
#     else:
#         # print(Positional_Dictionary)
#         Positional_Dictionary, Document = positional_index()
#         result = process_positional_query(query, Positional_Dictionary)
#     print(result)


app = Flask(__name__)  # start app in the website

# Getting inverted_index and positional_index
Inverted_Dictionary, Document = inverted_index()
Positional_Dictionary, Document = positional_index()

# Returning Relevant document retrieved


def Retrive_Docs(result):

    documents = {}
    if(result):
        for i in result:
            file_name = str(i)
            documents.setdefault(file_name, [])
            documents[file_name].append(Document.get(file_name))
    else:
        documents = {}
    return documents


# Default page display/home_page
@app.route('/')
def dictionary():
    return render_template('index.html')

# Funtion will invoke whenever a query is posted


@app.route("/query", methods=['POST'])
def upload():
    # query processing start time
    start = time.time()
    # getting query from the HTML form
    query = request.form['query']
    # Checking for boolean,proximity and phrase queries
    if('/' not in query):
        # Document= Cleaned Orignal Document
        result = process_query(query, Inverted_Dictionary)
    else:
        # print(Positional_Dictionary)
        result = process_positional_query(query, Positional_Dictionary)

    documents = Retrive_Docs(result)
    print(result)
    end = time.time()
    # total time to process query
    times = end - start
    return render_template('dict.html', dictionary=documents, num_docs=len(documents), time=str(times) + " " + "seconds")


if __name__ == "__main__":
    app.run()
