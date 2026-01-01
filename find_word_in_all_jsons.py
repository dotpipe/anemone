import os
import json

def find_word_in_all_jsons(word, data_dir='data'):
    """
    Return a list of all JSON files in data_dir where the word appears as a key.
    """
    found_in = []
    for fname in os.listdir(data_dir):
        if fname.endswith('.json'):
            fpath = os.path.join(data_dir, fname)
            try:
                with open(fpath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if word in data:
                        found_in.append(fname)
            except Exception:
                pass
    return found_in

if __name__ == '__main__':
    word = input('Enter word to search for: ')
    files = find_word_in_all_jsons(word)
    if files:
        print(f'Word "{word}" found in:')
        for fname in files:
            print('  ', fname)
    else:
        print(f'Word "{word}" not found in any JSON file in data/.')
