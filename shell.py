# shell.py


from eng1neer import respond_subject_specific

if __name__ == "__main__":
    # Only load the thesaurus association file at startup
    import json
    assoc_path = 'thesaurus_assoc.json'
    with open(assoc_path, 'r', encoding='utf-8') as f:
        thesaurus_assoc = json.load(f)

    while True:
        try:
            line = input("@#!$ > ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if not line:
            continue

        if line.lower() in {"quit", "exit"}:
            break

        # If the prompt looks like a code generation request, use the code engine
        if any(word in line.lower() for word in ["code", "generate", "python", "loop", "function", "print", "if", "while", "for", "define", "create"]):
            # Lazy-load code engine only if needed
            if 'code_engine' not in globals():
                from new_natural_code_engine import NaturalCodeEngine
                globals()['code_engine'] = NaturalCodeEngine('data')
            code = globals()['code_engine'].generate_code(line)
            print(code)
        else:
            # Use subject-specific response, loading subject files only as needed
            print(respond_subject_specific(line, assoc_path=assoc_path, data_dir='data'))
