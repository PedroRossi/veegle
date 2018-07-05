from classifier.classifier import Classifier
from extractor.extractor import Extractor
from indexer.indexer import Indexer
import os
import nltk
import json

def dump_to_json(key, val):
    ret = json.dumps(val, ensure_ascii=False)
    f = open(key+'.json', 'w')
    f.write(ret)
    f.close()

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

def main():
    # classifier = Classifier('naive_bayes', False)
    
    pass    
    
if __name__ == '__main__':
    main()