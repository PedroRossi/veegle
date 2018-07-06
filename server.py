from flask import Flask, jsonify, make_response, request
from flask_cors import CORS
from string import punctuation
from copy import deepcopy
import numpy as np
import nltk
import json
import os

nltk.download('stopwords')
nltk.download('rslp')

class QueryProcessor:

    def __init__(self, documents, index_dictionary):
        self.documents = documents
        self.index_dictionary = index_dictionary
        self.attributes_list = []
        for key in self.index_dictionary:
            self.attributes_list.append(key)
        self.__process_documents()

    def __process_documents(self):
        self.original_documents = deepcopy(self.documents)
        documents = self.documents
        for doc in documents:
            for attr in self.attributes_list:
                doc[attr] = QueryProcessor.clean_string(doc[attr])
        self.documents = documents

    @staticmethod
    def clean_string(st):
        stemmer = nltk.stem.RSLPStemmer()
        punctuation_list = list(punctuation)
        dictionary = punctuation_list + list(nltk.corpus.stopwords.words('portuguese'))
        st = ''.join([i for i in st if not i.isdigit() and i not in punctuation_list])
        st = st.split()
        st = [stemmer.stem(t) for t in st if t not in dictionary]
        return st

    def simple_search(self, query, tfidf_enabled = False):
        query = QueryProcessor.clean_string(query)
        documents_to_get = []
        for attr in self.attributes_list:
            for q in query:
                comp = attr + '.' + q
                if comp in self.index_dictionary[attr]:
                    documents_to_get += list(self.index_dictionary[attr][comp])
        documents_to_get = np.unique(documents_to_get)
        a = []
        results = []
        for q in query:
            a.append(1)
        for i in documents_to_get:
            i = int(i)
            aux = []
            for attr in self.attributes_list:
                aux += self.documents[i][attr]
            b = []
            for q in query:
                # TODO
                if tfidf_enabled:
                    pass
                else:
                    b.append(1 if q in aux else 0)
            ret = np.dot(a, b)/(np.linalg.norm(a)*np.linalg.norm(b))
            results.append([ret, self.original_documents[i]])
        results = sorted(results, key=lambda x: x[0], reverse=True)
        results = [i[1] for i in results]
        return results

    def advanced_search(self, query, tfidf_enabled):
        for attr in self.attributes_list:
            if attr in query:
                query[attr] = self.clean_string(query[attr])
        documents_to_get = []
        for key in query:
            for q in query[key]:
                comp = key + '.' + q
                if comp in self.index_dictionary[key]:
                    documents_to_get += list(self.index_dictionary[key][comp])
        documents_to_get = np.unique(documents_to_get)
        a = []
        results = []
        for key in query:
            for q in query[key]:
                a.append(1)
        for i in documents_to_get:
            i = int(i)
            b = []
            for key in query:
                for q in query[key]:
                    if tfidf_enabled:
                        comp = key + '.' + q
                        aux = (0 if i not in self.index_dictionary[key][comp] else self.index_dictionary[key][comp][i]) * np.log10(len(self.documents)/len(self.index_dictionary[key][comp]))
                        b.append(aux)
                    else:
                        b.append(1 if q in self.documents[i][key] else 0)
            ret = np.dot(a, b)/(np.linalg.norm(a)*np.linalg.norm(b))
            results.append([ret, self.original_documents[i]])
        results = sorted(results, key=lambda x: x[0], reverse=True)
        results = [i[1] for i in results]
        return results

def load_from_json(path):
    f = open(path, 'r')
    ret = f.read()
    f.close()
    ret = json.loads(ret)
    return ret

def load_query_processor():
    documents = load_from_json('./out.json')
    index_names = load_from_json('./name.json')
    index_ingredients = load_from_json('./ingredients.json')
    index_steps = load_from_json('./steps.json')
    d = {
        'name': index_names,
        'ingredients': index_ingredients,
        'steps': index_steps
    }
    qp = QueryProcessor(documents, d)
    return qp

def create_app(query_processor):
    # create and configure the app
    app = Flask(__name__)
    # a simple page that says hello
    @app.route('/search', methods=['POST'])
    def search():
        data = request.json
        results = []
        if 'general' in data:
            results = query_processor.simple_search(data['general'])
        elif 'name' in data or 'ingredients' in data or 'steps' in data:
            results = query_processor.advanced_search(data)
        for r in results:
            r['steps'] = r['steps'][:500]
        return jsonify(results)

    @app.errorhandler(405)
    @app.errorhandler(404)
    def not_found(error):
        return make_response(jsonify({'error': 'Not found'}), 404)
        
    @app.errorhandler(500)
    def internal_error(error):
        return make_response(jsonify({'error': 'Server internal error'}), 500)

    return app

def main():
    qp = load_query_processor()
    app = create_app(qp)
    CORS(app)
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
    
if __name__ == '__main__':
    main()