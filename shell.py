# shell.py


from prompt_toolkit import prompt
from eng1neer import load_all_definitions, respond
from new_natural_code_engine import NaturalCodeEngine

def main():
    defs = load_all_definitions()
    code_engine = NaturalCodeEngine('data')

    while True:
        try:
            text = prompt("#%@!> ")
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not text.strip():
            continue

        # If the prompt looks like a code generation request, use the code engine
        if any(word in text.lower() for word in ["code", "generate", "python", "loop", "function", "print", "if", "while", "for", "define", "create"]):
            code = code_engine.generate_code(text)
            print(code)
        else:
            print(respond(defs, text))

if __name__ == "__main__":
    main()
