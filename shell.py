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
        # If the prompt looks like an algebraic equation, solve for variables
        elif '=' in line:
            try:
                from sympy import symbols, Eq, solve, sympify
                # Split on '=' and build equations
                eqs = [eq.strip() for eq in line.split(',') if '=' in eq]
                if len(eqs) > 10:
                    print("... (truncated to 10 equations)")
                    eqs = eqs[:10]
                sympy_eqs = []
                all_vars = set()
                for eq in eqs:
                    left, right = eq.split('=', 1)
                    left_expr = sympify(left)
                    right_expr = sympify(right)
                    sympy_eqs.append(Eq(left_expr, right_expr))
                    all_vars.update(left_expr.free_symbols)
                    all_vars.update(right_expr.free_symbols)
                if not sympy_eqs:
                    raise ValueError
                sol = solve(sympy_eqs, list(all_vars), dict=True)
                if sol:
                    for s in sol:
                        out = ', '.join(f"{str(k)} = {v}" for k, v in s.items())
                        if len(s) > 10:
                            out = ', '.join(list(out.split(', ')[:10])) + ', ...'
                        print(out)
                else:
                    print("No solution found.")
            except Exception as e:
                print(f"Could not solve equation(s): {e}")
        # If the prompt looks like a math expression, evaluate it
        elif any(c in line for c in '+-*/^()') and any(ch.isdigit() for ch in line):
            from eng1neer import try_eval_expression
            result = try_eval_expression(line)
            if result is not None:
                print(result)
            else:
                print("Invalid math expression.")
        else:
            # Use subject-specific response, loading subject files only as needed
            print(respond_subject_specific(line, assoc_path=assoc_path, data_dir='data'))
