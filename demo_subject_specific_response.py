from eng1neer import respond_subject_specific

if __name__ == '__main__':
    while True:
        try:
            prompt = input('Enter your query (or "quit" to exit): ').strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not prompt or prompt.lower() in {'quit', 'exit'}:
            break
        print('\n' + respond_subject_specific(prompt) + '\n')
