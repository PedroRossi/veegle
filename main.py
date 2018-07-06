from classifier.classifier import Classifier
from extractor.extractor import Extractor
from indexer.indexer import Indexer
from query.query import QueryProcessor
from flask import Flask, request, make_response, jsonify, current_app
from flask_cors import CORS
import nltk
import json
import os

def dump_to_json(key, val):
    ret = json.dumps(val, ensure_ascii=False)
    f = open(key+'.json', 'w')
    f.write(ret)
    f.close()

def load_from_json(path):
    f = open(path, 'r')
    ret = f.read()
    f.close()
    ret = json.loads(ret)
    return ret

def extract():
    path = './classifier/pages/positivos'
    recipes = []
    for filename in os.listdir(path):
        full_path = os.path.join(path, filename)
        if full_path.endswith('.html'):
            try:
                e = Extractor(full_path)
                recipe = e.to_dicitonary()
                recipes.append(recipe)
            except:
                print('error in file: ' + filename + '\n')
    return recipes

def index_attributes(names, ingredients, steps):
    # all
    i = Indexer(names + ingredients + steps)
    index_names = i.get_index()
    dump_to_json('all', index_names)
    # names
    i = Indexer(names)
    index_names = i.get_index('name')
    dump_to_json('name', index_names)
    # ingredients
    i = Indexer(ingredients)
    index_ingredients = i.get_index('ingredients')
    dump_to_json('ingredients', index_ingredients)
    # steps
    i = Indexer(steps)
    index_steps = i.get_index('steps')
    dump_to_json('steps', index_steps)

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

def test_query_processor(q):
    qp = load_query_processor()
    arr = qp.advanced_search({'name': q}, False)[:10]
    print('Boolean')
    for a in arr:
        print(a['name'])
    arr = qp.advanced_search({'name': q}, True)[:10]
    print('TF-IDF')
    for a in arr:
        print(a['name'])

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
    app.run(host='0.0.0.0', port=5000)
    
if __name__ == '__main__':
    main()