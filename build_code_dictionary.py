import json

# Load definitions.json and build a code dictionary of synonyms and antonyms for code understanding

def build_code_dictionary(definitions_path):
    with open(definitions_path, 'r', encoding='utf-8') as f:
        defs = json.load(f)
    code_dict = {}
    for word, entry in defs.items():
        code_dict[word] = {
            'synonyms': set(entry.get('synonyms', [])),
            'antonyms': set(entry.get('antonyms', []))
        }
        # Add reverse mapping for synonyms
        for syn in entry.get('synonyms', []):
            if syn not in code_dict:
                code_dict[syn] = {'synonyms': set(), 'antonyms': set()}
            code_dict[syn]['synonyms'].add(word)
        # Add reverse mapping for antonyms
        for ant in entry.get('antonyms', []):
            if ant not in code_dict:
                code_dict[ant] = {'synonyms': set(), 'antonyms': set()}
            code_dict[ant]['antonyms'].add(word)
    # Convert sets to lists for JSON serialization
    for k in code_dict:
        code_dict[k]['synonyms'] = list(code_dict[k]['synonyms'])
        code_dict[k]['antonyms'] = list(code_dict[k]['antonyms'])
    return code_dict

if __name__ == "__main__":
    code_dict = build_code_dictionary("data/definitions.json")
    with open("data/code_dictionary.json", "w", encoding="utf-8") as f:
        json.dump(code_dict, f, indent=2, ensure_ascii=False)
    print("Code dictionary written to data/code_dictionary.json")
