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

        # If the user asks for date operations, forward to date_calculator
        if line.lower().startswith('date '):
            # format: date <subcmd> [args...]
            parts = line.split()[1:]
            try:
                from date_calculator import cli as date_cli
                ret = date_cli(parts)
                # cli prints output; return code printed as needed
            except Exception as e:
                print('Date command failed:', e)
            continue

        # verify <termA> <termB> -- compare definitions across dictionaries
        if line.lower().startswith('verify '):
            parts = line.split()[1:]
            try:
                from equality_verifier import cli as verify_cli
                verify_cli(parts)
            except Exception as e:
                print('Verify command failed:', e)
            continue

        # If the prompt starts with 'code:' force the code engine to return code-only output.
        if line.lower().startswith('code:') or line.lower().startswith('generate code'):
            raw = line.split(':', 1)[1].strip() if ':' in line else line
            # support an optional leading file specification: "file <name.py> <rest of prompt>"
            fname = None
            rest = raw
            try:
                import re
                m = re.match(r'file[: ]+(\S+)\s*(.*)', raw, re.I)
                if m:
                    fname = m.group(1)
                    rest = m.group(2) or ''
            except Exception:
                pass

            # Build a directive to the code engine to return code only
            directive = f"Generate only Python code, no explanation. {rest}".strip()
            # Lazy-load code engine only if needed
            if 'code_engine' not in globals():
                from new_natural_code_engine import NaturalCodeEngine
                globals()['code_engine'] = NaturalCodeEngine('data')
            try:
                code = globals()['code_engine'].generate_code(directive)
            except Exception as e:
                print('Code engine error:', e)
                continue
            # print and optionally save to examples/<fname>
            print(code)
            if fname:
                try:
                    from pathlib import Path
                    p = Path('examples')
                    p.mkdir(parents=True, exist_ok=True)
                    outp = p / fname
                    outp.write_text(code, encoding='utf-8')
                    print('Wrote', str(outp))
                except Exception as e:
                    print('Failed to write file:', e)
            continue
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
