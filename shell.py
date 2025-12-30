# shell.py

from prompt_toolkit import prompt
from eng1neer import load_definitions, respond

def main():
    defs = load_definitions()

    while True:
        try:
            text = prompt("> ")
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not text.strip():
            continue

        print(respond(defs, text))

if __name__ == "__main__":
    main()
