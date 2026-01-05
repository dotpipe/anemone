"""
new_natural_code_engine.py
Engine that generates code (loops, quantifiers, math relationships) from English concepts, chaining associations to build a ready-to-use program.
"""

import json
import os
import re
import threading


class NaturalCodeEngine:
    # Mapping of common programming-related words to template names
    PROGRAMMING_WORDS = {
        'do': 'for_loop',
        'get': 'function_definition',
        'make': 'function_definition',
        'run': 'function_definition',
        'set': 'assignment',
        'have': 'assignment',
        'create': 'function_definition',
        'function': 'function_definition',
        'loop': 'for_loop',
        'if': 'if_statement',
        'print': 'print_statement',
        'output': 'print_statement',
        'input': 'input_statement',
        'process': 'function_definition',
        'execute': 'function_definition',
        'calculate': 'function_definition',
        'find': 'for_loop',
        'return': 'function_definition',
        'call': 'function_definition',
        'define': 'function_definition',
        'assign': 'assignment',
        'compare': 'if_statement',
        'test': 'if_statement',
        'check': 'if_statement',
        'repeat': 'while_loop',
        'sum': 'list_comprehension',
        'sort': 'function_definition',
        'filter': 'list_comprehension',
        'show': 'print_statement',
        'display': 'print_statement',
        'program': 'function_definition',
        'code': 'function_definition',
        'add': 'assignment',
        'subtract': 'assignment',
        'multiply': 'assignment',
        'divide': 'assignment',
        'increment': 'assignment',
        'decrement': 'assignment',
        'list': 'list_comprehension',
        'array': 'list_comprehension',
        'dict': 'assignment',
        'dictionary': 'assignment',
        'class': 'class_definition',
        'object': 'class_definition',
        'exception': 'try_except',
        'error': 'try_except',
        'file': 'with_statement',
        'read': 'with_statement',
        'write': 'with_statement',
        'import': 'import_statement',
        'module': 'import_statement',
        'open': 'with_statement',
        'close': 'with_statement',
        'main': 'function_definition',
        'exit': 'function_definition',
        'return': 'function_definition',
        'value': 'assignment',
        'variable': 'assignment',
        'parameter': 'function_definition',
        'argument': 'function_definition',
        'index': 'for_loop',
        'element': 'for_loop',
        'item': 'for_loop',
        'sum': 'list_comprehension',
        'average': 'list_comprehension',
        'mean': 'list_comprehension',
        'max': 'list_comprehension',
        'min': 'list_comprehension',
        'length': 'assignment',
        'size': 'assignment',
        'count': 'list_comprehension',
        'remove': 'assignment',
        'delete': 'assignment',
        'append': 'assignment',
        'extend': 'assignment',
        'pop': 'assignment',
        'insert': 'assignment',
        'replace': 'assignment',
        'update': 'assignment',
        'clear': 'assignment',
        'copy': 'assignment',
        'sort': 'assignment',
        'reverse': 'assignment',
        'join': 'assignment',
        'split': 'assignment',
        'strip': 'assignment',
        'find': 'for_loop',
        'search': 'for_loop',
        'match': 'if_statement',
        'case': 'if_statement',
        'switch': 'if_statement',
        'try': 'try_except',
        'except': 'try_except',
        'finally': 'try_except',
        'raise': 'try_except',
        'assert': 'if_statement',
        'with': 'with_statement',
        'as': 'with_statement',
        'from': 'import_statement',
        'pass': 'function_definition',
        'continue': 'for_loop',
        'break': 'for_loop',
        'yield': 'function_definition',
        'lambda': 'function_definition',
        'generator': 'function_definition',
        'comprehension': 'list_comprehension',
        'tuple': 'assignment',
        'set': 'assignment',
        'frozenset': 'assignment',
        'bool': 'assignment',
        'int': 'assignment',
        'float': 'assignment',
        'str': 'assignment',
        'bytes': 'assignment',
        'bytearray': 'assignment',
        'memoryview': 'assignment',
        'complex': 'assignment',
        'super': 'class_definition',
        'self': 'class_definition',
        'staticmethod': 'class_definition',
        'classmethod': 'class_definition',
        'property': 'class_definition',
        'del': 'assignment',
        'global': 'assignment',
        'nonlocal': 'assignment',
        'assert': 'if_statement',
        'async': 'function_definition',
        'await': 'function_definition',
        'True': 'assignment',
        'False': 'assignment',
        'None': 'assignment'
    }
    """
    Template Placeholder Reference (used in python_command_templates.json):
        {item}         - The variable representing a single element in a loop or comprehension
        {iterable}     - The collection or sequence to iterate over (e.g., a list, tuple)
        {condition}    - A boolean expression controlling flow (e.g., in if/while/comp)
        {function_name}- The name of a function being defined or called
        {params}       - The parameters for a function definition (comma-separated)
        {return_value} - The value returned by a function
        {module}       - The name of a module to import
        {object}       - The object or symbol imported from a module
        {filename}     - The name of a file (for file operations)
        {ClassName}    - The name of a class being defined
        {exception}    - The exception type to catch in try/except
        {value}        - The value or expression to print or use
    All templates use 4 spaces for indentation in code blocks.
    """
    """
    Generates code (loops, quantifiers, math relationships) from English prompts, using definitions.json for general answers and math.json for math code, with verbal cues.
    """


    def __init__(self, data_dir='data', template_path='python_command_templates.json', code_rel_path='code_relationships.json'):
        self.data_dir = data_dir
        self.knowledge = self._load_english_concepts()
        # Prefer the derived Wikipedia definitions as the primary source for natural-language concepts
        wiki_defs = self._load_json_file('wikipedia_defs.json')
        # Use wikipedia-derived definitions only; do not fall back to legacy definitions.json
        self.definitions = wiki_defs or {}
        self.math = self._load_json_file('math.json')
        self.templates = self._load_templates(template_path)
        self.code_relationships = self._load_code_relationships(code_rel_path)
        self.inquiry_cache = set()
        self.inquiry_lock = threading.Lock()
        self.inquiry_thread = None

    def _load_code_relationships(self, code_rel_path):
        if not os.path.exists(code_rel_path):
            return []
        with open(code_rel_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('code_relationships', [])

    def start_inquiry_thread(self, word):
        if self.inquiry_thread and self.inquiry_thread.is_alive():
            return
        self.inquiry_thread = threading.Thread(target=self._track_inquiry_word, args=(word,))
        self.inquiry_thread.daemon = True
        self.inquiry_thread.start()

    def _track_inquiry_word(self, word):
        with self.inquiry_lock:
            if word in self.inquiry_cache:
                return
            self.inquiry_cache.add(word)
            # Search code_relationships for related terms
            for entry in self.code_relationships:
                if word == entry['term'] or word in entry.get('related_terms', []):
                    # Already present, skip
                    return
            # If not found, add to related_terms of closest match
            for entry in self.code_relationships:
                if word in entry['description'] or word in entry['example']:
                    entry.setdefault('related_terms', []).append(word)
                    break
            # Optionally, persist changes (not implemented here)
            # with open('code_relationships.json', 'w', encoding='utf-8') as f:
            #     json.dump({'code_relationships': self.code_relationships}, f, indent=4)

    def _load_templates(self, template_path):
        if not os.path.exists(template_path):
            return []
        with open(template_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _load_english_concepts(self):
        concepts = {}
        for fname in os.listdir(self.data_dir):
            if fname.endswith('.json'):
                with open(os.path.join(self.data_dir, fname), 'r', encoding='utf-8') as f:
                    try:
                        data = json.load(f)
                        if isinstance(data, dict):
                            for k, v in data.items():
                                concepts[k.lower()] = v
                        elif isinstance(data, list):
                            for entry in data:
                                if isinstance(entry, dict):
                                    for k, v in entry.items():
                                        concepts[k.lower()] = v
                    except Exception:
                        continue
        return concepts

    def _load_json_file(self, filename):
        path = os.path.join(self.data_dir, filename)
        if not os.path.exists(path):
            return {}
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def generate_code(self, prompt: str):
        # DEBUG: Extract and print prompt pieces for analysis
        import importlib.util, sys, os
        gct_path = os.path.join(os.path.dirname(__file__), 'generate_code_templates.py')
        if os.path.exists(gct_path):
            spec = importlib.util.spec_from_file_location('generate_code_templates', gct_path)
            gct = importlib.util.module_from_spec(spec)
            sys.modules['generate_code_templates'] = gct
            spec.loader.exec_module(gct)
            if hasattr(gct, 'extract_prompt_pieces'):
                gct.extract_prompt_pieces(prompt)
        """
        Answers coding prompts using definitions.json for general answers and math.json for math code, with a verbal cue for the math operation. Now supports inequalities and code comments.
        Uses the masterkey logic from generate_code_templates.py for loop/operation prompts.
        If the prompt suggests a function, wraps the generated code in a function definition.
        """
        import importlib.util
        import sys
        masterkey_path = os.path.join(os.path.dirname(__file__), 'generate_code_templates.py')
        # Detect if prompt suggests a function
        lower_prompt = prompt.lower()
        function_words = [
            'function', 'define', 'create', 'make', 'build', 'write', 'implement', 'procedure', 'method', 'routine', 'wrap', 'encapsulate', 'module', 'program', 'code', 'return'
        ]
        wants_function = any(word in lower_prompt for word in function_words)
        # Try to use masterkey logic from generate_code_templates.py if available
        if os.path.exists(masterkey_path):
            spec = importlib.util.spec_from_file_location('generate_code_templates', masterkey_path)
            gct = importlib.util.module_from_spec(spec)
            sys.modules['generate_code_templates'] = gct
            spec.loader.exec_module(gct)
            code = gct.generate_code(prompt)
            if code and not code.startswith('# No matching'):
                # If function requested and code is not already a function, wrap it
                if wants_function and not code.strip().startswith('def '):
                    # Try to extract a function name from the prompt
                    import re
                    match = re.search(r'(?:function|define|create|make|build|write|implement) (\w+)', lower_prompt)
                    func_name = match.group(1) if match else 'generated_function'
                    # Find parameters (very basic: look for 'with X and Y' or 'parameters X, Y')
                    params = ''
                    param_match = re.search(r'(?:with|parameters?) ([\w, ]+)', lower_prompt)
                    if param_match:
                        params = ', '.join([p.strip() for p in re.split(r',|and', param_match.group(1)) if p.strip()])
                    code_lines = code.splitlines()
                    indented_code = '\n'.join('    ' + line if line.strip() else '' for line in code_lines)
                    code = f"def {func_name}({params}):\n{indented_code}\n"
                return code
        # Fallback to original logic if masterkey doesn't match
        import re
        words = re.findall(r'\w+', lower_prompt)
        for word in words:
            self.start_inquiry_thread(word)

            # Fallback heuristic: try to synthesize simple loop/increment code when masterkey doesn't match
            try:
                import re
                lp = lower_prompt
                # find loop count (first integer that looks like a repeat count)
                loop_match = re.search(r'(?:loop|loops|repeat|repetition|repetitions|times|rounds?)\s*(?:of|with|that|:)?\s*(\d+)', lp)
                if not loop_match:
                    loop_match = re.search(r'(\d+)\s*(?:times|repetitions|rounds)', lp)
                count = int(loop_match.group(1)) if loop_match else None

                # find variable to increment (e.g., 's' in 'increment s' or 'add 2 to s')
                var_match = re.search(r'increment(?:s)?\s+([a-zA-Z_][a-zA-Z0-9_]*)', lp)
                if not var_match:
                    var_match = re.search(r'add\s+\d+\s+to\s+([a-zA-Z_][a-zA-Z0-9_]*)', lp)
                var = var_match.group(1) if var_match else None

                # find increment amount
                inc_match = re.search(r'by\s+(\d+)', lp)
                if not inc_match:
                    # look for patterns like 'add 2 to s' or 'increment s by 2' handled above
                    inc_match = re.search(r'add\s+(\d+)', lp)
                inc = int(inc_match.group(1)) if inc_match else 1

                # if we detected a loop count and an increment action, generate code
                if count is not None and var is not None:
                    # starter value default 0
                    starter = 0
                    func_name = 'generated_function'
                    if wants_function:
                        # attempt to pick a function name from prompt
                        mfn = re.search(r'(?:function|define|create|write|make)\s+(?:a\s+)?([a-zA-Z_][a-zA-Z0-9_]*)', lp)
                        if mfn:
                            func_name = mfn.group(1)
                    body = []
                    body.append(f"{var} = {starter}")
                    body.append(f"for _ in range({count}):")
                    body.append(f"    {var} += {inc}")
                    if wants_function:
                        # wrap in function
                        params = ''
                        indented = '\n'.join('    ' + line for line in body)
                        code = f"def {func_name}({params}):\n{indented}\n    return {var}\n"
                    else:
                        code = '\n'.join(body) + f"\nprint({var})\n"
                    return code
            except Exception:
                pass

            return "# No actionable code structure detected from prompt."

# Example usage:

def main():
    engine = NaturalCodeEngine('data')
    edge_cases_path = 'edge_cases.txt'
    if os.path.exists(edge_cases_path):
        with open(edge_cases_path, 'r', encoding='utf-8') as f:
            edge_cases = [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]
    else:
        edge_cases = [
            "Increment y 0 times during a 5 repetition loop if y > 10",
            "Subtract 1 from counter 1000 times when counter is -50",
            "Add 3 to value in 'score' every time in a 7 repetition loop if score is even",
            "Decrement z 2 times inside a 1 repetition loop if z < 0",
            "Print 'Done' 0 times",
            "Code a loop that prints 'Edge' -5 times",
            "Add 1 to x 10 times during a 0 repetition loop",
            "Increment a 1 time during a 1 repetition loop if a == 1 and a < 2",
            "Subtract 2 from b 3 times in a 2 repetition loop if b != 0",
            "Add 1 to x 5 times if x is not None, during a 3 repetition loop"
        ]
    for prompt in edge_cases:
        print(f"\nPrompt: {prompt}\n")
        code = engine.generate_code(prompt)
        print("Generated code:")
        print(code)
        print("-" * 40)

if __name__ == "__main__":
    main()
