import json

def add_subjects_to_glossary(def_path, assoc_path):
    with open(def_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    with open(assoc_path, 'r', encoding='utf-8') as f:
        assoc = json.load(f)
    glossary = data.get('glossary', [])
    # For each word in glossary, add a 'subjects' key if subjects exist
    for word in glossary:
        if word in data and isinstance(data[word], dict):
            subjects = assoc.get(word, None)
            if subjects:
                data[word]['subjects'] = subjects
    with open(def_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Added subjects to {sum(1 for w in glossary if w in assoc)} glossary terms in {def_path}.")

if __name__ == '__main__':
    add_subjects_to_glossary('data/definitions.json', 'thesaurus_assoc.json')
