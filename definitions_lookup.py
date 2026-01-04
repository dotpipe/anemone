import json

def lookup_coding_word(word, definitions_path='data/wikipedia_defs.json', depth=1, seen=None):
    """
    Look up a coding word in definitions.json, returning its type, definition, and related concepts.
    Optionally, follow related concepts recursively up to 'depth' levels.
    """
    if seen is None:
        seen = set()
    with open(definitions_path, 'r', encoding='utf-8') as f:
        definitions = json.load(f)
    result = {}
    entry = definitions.get(word)
    if not entry:
        return None
    result['word'] = word
    result['definition'] = entry.get('definition')
    result['type'] = entry.get('type')
    result['usage'] = entry.get('usage')
    result['related'] = []
    seen.add(word)
    # Recursively follow related concepts if present
    related = entry.get('related', [])
    if depth > 0 and related:
        for rel_word in related:
            if rel_word not in seen:
                rel_entry = lookup_coding_word(rel_word, definitions_path, depth-1, seen)
                if rel_entry:
                    result['related'].append(rel_entry)
    else:
        result['related'] = related
    return result

if __name__ == '__main__':
    # Example usage:
    word = input('Enter coding word to look up: ')
    info = lookup_coding_word(word, depth=2)
    if info:
        print(json.dumps(info, indent=2, ensure_ascii=False))
    else:
        print('Word not found in wikipedia_defs.json')
