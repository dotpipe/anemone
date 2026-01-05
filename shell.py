# shell.py


from eng1neer import respond_subject_specific

if __name__ == "__main__":
    # Only load the thesaurus association file at startup
    import json
    assoc_path = 'thesaurus_assoc.json'
    with open(assoc_path, 'r', encoding='utf-8') as f:
        thesaurus_assoc = json.load(f)

    # lightweight terminal spinner to show progress during code generation
    class Spinner:
        def __init__(self, msg=''):
            import sys, threading, itertools, time
            self.msg = msg
            self._stop = threading.Event()
            self._thread = threading.Thread(target=self._spin, daemon=True)
            self._sys = sys
            self._itertools = itertools
            self._time = time

        def _spin(self):
            for ch in self._itertools.cycle('|/-\\'):
                if self._stop.is_set():
                    break
                self._sys.stdout.write('\r' + (self.msg + ' ' if self.msg else '') + ch)
                self._sys.stdout.flush()
                self._time.sleep(0.08)
            # clear
            self._sys.stdout.write('\r' + (' ' * (len(self.msg) + 2)) + '\r')
            self._sys.stdout.flush()

        def start(self):
            self._thread.start()

        def stop(self):
            self._stop.set()
            self._thread.join()

    while True:
        try:
            line = input("@#!$ > ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if not line:
            continue

        # Quick code-intent check and suggestion via cross-referencer
        try:
            import importlib.util
            import time
            from pathlib import Path
            # use a unique module name each time to avoid any cached version
            unique_name = f'cross_reference_prompt_{int(time.time()*1000)}'
            spec = importlib.util.spec_from_file_location(unique_name, str(Path('scripts') / 'cross_reference_prompt.py'))
            cr = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(cr)
            if cr.is_code_request(line):
                try:
                    index = cr.load_index()
                    items, shorthand, params = cr.cross_reference(line, index)
                    sugg = cr.suggest_function_signature(items, params, line)
                    # show a concise one-line suggestion instead of full JSON
                    sig = sugg.get('signature') or sugg.get('name') or ''
                    if sig:
                        print(f"Code intent detected — suggested: {sig}")
                    else:
                        print('Code intent detected — suggested function')
                    # Automatically generate code from the suggestion (original behavior)
                    directive = f"Generate only Python code, no explanation. {line}"
                    if 'code_engine' not in globals():
                        from new_natural_code_engine import NaturalCodeEngine
                        globals()['code_engine'] = NaturalCodeEngine('data')
                    try:
                        spinner = Spinner('Generating code...')
                        spinner.start()
                        code = globals()['code_engine'].generate_code(directive)
                        spinner.stop()
                        # if the engine returns an empty or placeholder result, synthesize a simple fallback
                        if not code or 'No actionable' in code or len(code.strip()) < 40:
                            # synthesize from suggestion or prompt: simple loop/print template
                            try:
                                prompt = line.lower()
                                import re
                                m = re.search(r'from\s*(\d+)\s*to\s*(\d+)', prompt)
                                if m:
                                    a = int(m.group(1)); b = int(m.group(2))
                                    name = sugg.get('name') or 'generated_fn'
                                    fname = name if name.endswith('.py') else name + '.py'
                                    code = (f"def {name}():\n"
                                            f"    for i in range({a},{b}+1):\n"
                                            f"        print(i)\n\n"
                                            f"if __name__ == '__main__':\n"
                                            f"    {name}()\n")
                                else:
                                    # generic fallback: if prompt contains 'count' and two numbers, find numbers
                                    nums = re.findall(r"\d+", prompt)
                                    if len(nums) >= 2:
                                        a = int(nums[0]); b = int(nums[1])
                                        name = sugg.get('name') or 'generated_fn'
                                        fname = name if name.endswith('.py') else name + '.py'
                                        code = (f"def {name}():\n"
                                                f"    for i in range({a},{b}+1):\n"
                                                f"        print(i)\n\n"
                                                f"if __name__ == '__main__':\n"
                                                f"    {name}()\n")
                                    else:
                                        # last-resort: use suggested skeleton if available
                                        sk = (sugg.get('skeletons') or [])
                                        if sk:
                                            code = sk[0]
                                        else:
                                            code = '# No actionable code structure detected from prompt.\n'
                            except Exception:
                                code = '# No actionable code structure detected from prompt.\n'
                        print(code)
                        # save to examples/<name>.py when suggestion provides a name
                        try:
                            name = sugg.get('name') or None
                            if name:
                                from pathlib import Path
                                p = Path('examples')
                                p.mkdir(parents=True, exist_ok=True)
                                fname = name if name.endswith('.py') else name + '.py'
                                outp = p / fname
                                outp.write_text(code, encoding='utf-8')
                                print('Wrote', str(outp))
                        except Exception:
                            pass
                    except Exception as e:
                        print('Code engine error:', e)
                    continue
                except Exception as e:
                    print('Cross-referencer error:', e)
        except Exception:
            # fail silently; cross-referencer is optional
            pass

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
                spinner = Spinner('Generating code...')
                spinner.start()
                code = globals()['code_engine'].generate_code(directive)
                spinner.stop()
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
