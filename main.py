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
    ret = json.dumps(recipes, indent=True, ensure_ascii=False)
    return ret

def index_attributes(names, ingredients, steps):
    # names
    i = Indexer(names)
    index_names = i.get_index('name')
    dump_to_json('names', index_names)
    # ingredients
    i = Indexer(ingredients)
    index_ingredients = i.get_index('ingredients')
    dump_to_json('ingredients', index_ingredients)
    # steps
    i = Indexer(steps)
    index_steps = i.get_index('steps')
    dump_to_json('steps', index_steps)

def load_query_processor():
    documents = load_from_json('./extractor/out.json')
    index_names = load_from_json('./indexer/name.json')
    index_ingredients = load_from_json('./indexer/ingredients.json')
    index_steps = load_from_json('./indexer/steps.json')
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
    # classifier = Classifier('naive_bayes', False)
    qp = load_query_processor()
    app = create_app(qp)
    CORS(app)
    app.run(host='0.0.0.0', port=5000)
    
if __name__ == '__main__':
    main()