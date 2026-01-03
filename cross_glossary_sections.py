import os
import json
from collections import defaultdict

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')

def load_glossaries():
    files = [f for f in os.listdir(DATA_DIR) if f.endswith('.json')]
    glossaries = {}
    for fname in files:
        path = os.path.join(DATA_DIR, fname)
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            glossary = data.get('glossary', [])
            if isinstance(glossary, list):
                glossaries[fname] = set(glossary)
            else:
                glossaries[fname] = set()
        except Exception as e:
            print(f"Error loading {fname}: {e}")
    return glossaries

def cross_check_glossaries(glossaries):
    shared_terms = defaultdict(dict)
    files = list(glossaries.keys())
    for i, f1 in enumerate(files):
        for j, f2 in enumerate(files):
            if i >= j:
                continue
            shared = glossaries[f1] & glossaries[f2]
            if shared:
                shared_terms[f1][f2] = shared
    return shared_terms

def generate_sections(shared_terms):
    sections = []
    for f1, pairs in shared_terms.items():
        for f2, terms in pairs.items():
            section = {
                "files": [f1, f2],
                "shared_terms": sorted(list(terms)),
                "expedited_answer": f"Shared terms between {f1} and {f2}: {', '.join(sorted(list(terms)))}"
            }
            sections.append(section)
    return sections

def main():
    glossaries = load_glossaries()
    shared_terms = cross_check_glossaries(glossaries)
    sections = generate_sections(shared_terms)
    out_path = os.path.join(os.path.dirname(__file__), 'cross_glossary_sections.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(sections, f, indent=2, ensure_ascii=False)
    print(f"Generated {len(sections)} cross-glossary sections. See cross_glossary_sections.json.")

if __name__ == "__main__":
    main()