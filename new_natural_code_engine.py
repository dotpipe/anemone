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
        self.definitions = self._load_json_file('definitions.json')
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
        """
        Answers coding prompts using definitions.json for general answers and math.json for math code, with a verbal cue for the math operation. Now supports inequalities and code comments.
        """

        # If prompt contains 'program' or 'code', bias toward generating code using templates
        # If prompt contains a programming-related word, bias toward code generation
        lower_prompt = prompt.lower()
        # Start thread to track inquiry word
        words = re.findall(r'\w+', lower_prompt)
        for word in words:
            self.start_inquiry_thread(word)
        # Prioritize print/display/output/show actions in prompt
        for action in ['print', 'show', 'display', 'output', 'say', 'sys']:
            if action in lower_prompt:
                # Try to extract quoted text first
                match = re.search(r'"([^"]+)"|\'([^\']+)\'', prompt)
                value = None
                if match:
                    value = match.group(1) or match.group(2)
                if not value:
                    # Find the subject phrase (noun or phrase) after the action word
                    subject_match = re.search(r'(?:code|make|display|print|show|output|say|sys)[^\w]*([A-Z][a-zA-Z0-9 !?]+)', prompt)
                    if subject_match:
                        value = subject_match.group(1).strip()
                    else:
                        # Fallback: extract everything after the action word
                        after_action = re.split(rf'{action}\s+', prompt, maxsplit=1)
                        if len(after_action) > 1:
                            value = after_action[1].strip()
                            value = re.sub(r'( to the \w+.*|\.|!|\?)$', '', value)
                            value = value.strip().capitalize()
                if not value or value == '':
                    value = 'Hello World'
                # Check for a count (e.g., '10 times', '5 times', etc.)
                count_match = re.search(r'(\d+)\s+times?', lower_prompt)
                if count_match:
                    count = count_match.group(1)
                    # Generate a for loop that prints the string N times
                    for template in self.templates:
                        if template['name'] == 'for_loop':
                            code = template['template']
                            code = code.replace('{item}', '_').replace('{iterable}', f'range({count})')
                            # Replace the print line with the correct string
                            code_lines = code.split('\n')
                            for i, line in enumerate(code_lines):
                                if 'print' in line:
                                    code_lines[i] = f'    print("{value}")'
                            code = '\n'.join(code_lines)
                            comment = f"# This program prints: {value} {count} times"
                            print(comment)
                            print(code)
                            return f"{comment}\n{code}"
                # Otherwise, just print once
                for template in self.templates:
                    if template['name'] == 'print_statement':
                        code = template['template'].replace('{value}', f'"{value}"')
                        comment = f"# This program prints: {value}"
                        print(comment)
                        print(code)
                        return f"{comment}\n{code}"

        for word, template_name in self.PROGRAMMING_WORDS.items():
            if word in lower_prompt:
                for template in self.templates:
                    if template['name'] == template_name:
                        code = template['template']
                        # Improved: Extract loop parameters (range, subject, action) from prompt
                        if template_name == 'for_loop':
                            # Enhanced: support nested/conditional increments/decrements/adds/subtracts in English
                            # Example: 'increment z 3 times during a 1000 repetition loop if z % 5 == 0'
                            nested_match = re.search(r'(increment|decrement|add|subtract|plus|minus) ([a-zA-Z_][a-zA-Z0-9_]*) (\d+) times? (?:during|within|inside|in|every time in) a (\d+) repetition loop(?: if (.+))?', lower_prompt)
                            if nested_match:
                                op_word = nested_match.group(1)
                                var_name = nested_match.group(2)
                                inner_count = nested_match.group(3)
                                outer_count = nested_match.group(4)
                                condition = nested_match.group(5)
                                op_symbol = '+='
                                op_value = '1'
                                if op_word in ['decrement', 'subtract', 'minus']:
                                    op_symbol = '-='
                                if op_word in ['add', 'plus', 'increment']:
                                    op_symbol = '+='
                                code = f"{var_name} = 0\nfor _ in range({outer_count}):"
                                if condition:
                                    code += f"\n    if {condition}:"
                                    code += f"\n        for _ in range({inner_count}):\n            {var_name} {op_symbol} {op_value}"
                                    code += f"\n    else:\n        pass"
                                else:
                                    code += f"\n    for _ in range({inner_count}):\n        {var_name} {op_symbol} {op_value}"
                                code += f"\n    print({var_name})"
                                comment = f"# This program {op_word}s {inner_count} to {var_name} during each of {outer_count} repetitions{' if ' + condition if condition else ''}."
                                print(comment)
                                print(code)
                                return f"{comment}\n{code}"
                            # Handle 'Add 1 to x 5 times if x is not None, during a 3 repetition loop' and 'Subtract 2 from b 3 times in a 2 repetition loop if b != 0'
                            addval_match = re.search(r'(add|subtract|plus|minus) (\d+) (?:to|from) (?:value in )?([a-zA-Z_][a-zA-Z0-9_]*)(?: (?:every time in|in))?(?: if ([^,]+))?(?:,? ?(?:during|in|inside|within|over|through|for) a (\d+) repetition loop)?', lower_prompt)
                            if addval_match:
                                op_word = addval_match.group(1)
                                op_value = addval_match.group(2)
                                var_name = addval_match.group(3)
                                condition = addval_match.group(4)
                                outer_count = addval_match.group(5) if addval_match.group(5) else '1'
                                op_symbol = '+='
                                if op_word in ['subtract', 'minus']:
                                    op_symbol = '-='
                                code = f"{var_name} = 0\nfor _ in range({outer_count}):"
                                if condition:
                                    code += f"\n    if {condition.strip()}:"
                                    code += f"\n        for _ in range({op_value}):\n            {var_name} {op_symbol} 1"
                                    code += f"\n    else:\n        pass"
                                else:
                                    code += f"\n    for _ in range({op_value}):\n        {var_name} {op_symbol} 1"
                                code += f"\n    print({var_name})"
                                comment = f"# This program {op_word}s 1 to {var_name} {op_value} times in each of {outer_count} repetitions{' if ' + condition.strip() if condition else ''}."
                                print(comment)
                                print(code)
                                return f"{comment}\n{code}"
                            # Handle 'Subtract 1 from counter 1000 times when counter is -50'
                            sub_match = re.search(r'(subtract|minus) (\d+) from ([a-zA-Z_][a-zA-Z0-9_]*) (\d+) times? when \3 is (-?\d+)', lower_prompt)
                            if sub_match:
                                op_word = sub_match.group(1)
                                op_value = sub_match.group(2)
                                var_name = sub_match.group(3)
                                loop_range = sub_match.group(4)
                                var_init = sub_match.group(5)
                                op_symbol = '-='
                                code = f"{var_name} = {var_init}\nfor _ in range({loop_range}):\n    {var_name} {op_symbol} {op_value}\n    print({var_name})"
                                comment = f"# This program {op_word}s {op_value} from {var_name} {loop_range} times, starting from {var_init}."
                                print(comment)
                                print(code)
                                return f"{comment}\n{code}"
                            # Factory for increment/decrement/add/subtract/minus/plus in English phrasing
                            op_match = re.search(r'(?:do|perform|make|do|repeat|code|write|show|print)?\s*(\d+)\s*(additions?|increments?|decrements?|subtractions?|plus|minus|adds?|subtracts?|times? (add|plus|increment|subtract|minus|decrement))\s*(to|from)?\s*(?:the number in|variable|value|of)?\s*["\']?(\w+)["\']?(?:\s*(?:when|starting at|set to|is|equals)\s*["\']?(\d+)["\']?)?', lower_prompt)
                            if op_match:
                                loop_range = op_match.group(1)
                                op_word = op_match.group(2)
                                var_name = op_match.group(5)
                                var_init = op_match.group(6) if op_match.group(6) else '0'
                                # Determine operation
                                if any(w in op_word for w in ['add', 'plus', 'increment']):
                                    op_symbol = '+='
                                    op_value = '1'
                                elif any(w in op_word for w in ['subtract', 'minus', 'decrement']):
                                    op_symbol = '-='
                                    op_value = '1'
                                else:
                                    op_symbol = '+='
                                    op_value = '1'
                                code = f"{var_name} = {var_init}\nfor _ in range({loop_range}):\n    {var_name} {op_symbol} {op_value}\n    print({var_name})"
                                comment = f"# This program {op_word} 1 to {var_name} {loop_range} times, starting from {var_init}."
                                print(comment)
                                print(code)
                                return f"{comment}\n{code}"
                            # Flexible regex for nested add/subtract loop patterns
                            add_loop_match = re.search(r'add (\d+) to ([a-zA-Z_][a-zA-Z0-9_]*) (\d+) times?(?: (?:during|in|inside|within|over|through|for) a (\d+) repetition loop)?', lower_prompt)
                            if add_loop_match:
                                op_value = add_loop_match.group(1)
                                var_name = add_loop_match.group(2)
                                inner_count = add_loop_match.group(3)
                                outer_count = add_loop_match.group(4) if add_loop_match.group(4) else '1'
                                code = f"{var_name} = 0\nfor _ in range({outer_count}):\n    for _ in range({inner_count}):\n        {var_name} += {op_value}\n    print({var_name})"
                                comment = f"# This program adds {op_value} to {var_name} {inner_count} times during each of {outer_count} repetitions."
                                print(comment)
                                print(code)
                                return f"{comment}\n{code}"
                                    # Learning: If a word is not in the top ten of definitions, check if it's a valid math term and add to related_terms
                                    # words = re.findall(r'\w+', prompt.lower())
                                    # top_ten_defs = set(list(self.definitions.keys())[:10])
                                    # for word in words:
                                    #     if word not in top_ten_defs and word not in self.definitions:
                                    #         # Check if it's a valid math term (in self.math)
                                    #         if word in self.math:
                                    #             # Add to related_terms in code_relationships if not already present
                                    #             for entry in self.code_relationships:
                                    #                 if 'related_terms' in entry and word not in entry['related_terms']:
                                    #                     entry['related_terms'].append(word)
                                    #                     break
                            # Fallback generic for-loop logic
                            loop_var = None
                            loop_range = None
                            loop_action = None
                            num_match = re.search(r'(\d+)', prompt)
                            if num_match:
                                loop_range = num_match.group(1)
                            subj_match = re.search(r'(?:loop|for|do|repeat)\s+(\w+)', lower_prompt)
                            if subj_match:
                                loop_var = subj_match.group(1)
                            for act in ['print', 'display', 'show']:
                                if act in lower_prompt:
                                    loop_action = f'print({loop_var if loop_var else 'variable'})'
                            if not loop_var:
                                loop_var = input("Enter the loop variable (single quotes for variable): ")
                                if not loop_var:
                                    loop_var = 'variable'
                            if not loop_range:
                                loop_range = input("Enter the loop range (number or variable in single quotes): ")
                                if not loop_range:
                                    loop_range = '10'
                            if not loop_action:
                                loop_action = f'print({loop_var})'
                            if '{item}' in code:
                                code = code.replace('{item}', loop_var)
                            if '{iterable}' in code:
                                code = code.replace('{iterable}', f'range({loop_range})')
                            if 'for ' in code and ':' in code and '\n' in code:
                                code_lines = code.split('\n')
                                if len(code_lines) == 2 and code_lines[1].strip() == 'pass':
                                    code_lines[1] = f'    {loop_action}'
                                    code = '\n'.join(code_lines)
                            comment = f"# This program demonstrates: {template['description']}"
                            print(comment)
                            print(code)
                            return f"{comment}\n{code}"
                        # Default for other templates
                        condition = 'x > 0'
                        if '{condition}' in code:
                            match = re.search(r'(less than|greater than|equal to|not equal to)\s+(\d+)', prompt, re.IGNORECASE)
                            if match:
                                op = match.group(1).lower()
                                num = match.group(2)
                                if op == 'less than':
                                    condition = f"x < {num}"
                                elif op == 'greater than':
                                    condition = f"x > {num}"
                                elif op == 'equal to':
                                    condition = f"x == {num}"
                                elif op == 'not equal to':
                                    condition = f"x != {num}"
                            code = code.replace('{condition}', condition)
                        code = code.replace('{item}', 'item').replace('{iterable}', 'my_list').replace('{function_name}', 'my_func').replace('{params}', '').replace('{return_value}', 'None').replace('{module}', 'os').replace('{object}', 'path').replace('{filename}', 'file.txt').replace('{ClassName}', 'MyClass').replace('{exception}', 'Exception').replace('{value}', '42')
                        comment = f"# This program demonstrates: {template['description']}"
                        print(comment)
                        print(code)
                        return f"{comment}\n{code}"
        # If prompt contains 'program' or 'code', bias toward generating code using templates
        if any(word in lower_prompt for word in ['program', 'code']):
            # Look for print/show/display/output and quoted or clear text
            for action in ['print', 'show', 'display', 'output']:
                if action in prompt.lower():
                    match = re.search(r'"([^"]+)"|\'([^\']+)\'|\b(?:print|show|display|output)\b.*?(\w+)$', prompt, re.IGNORECASE)
                    value = 'Hello World'
                    if match:
                        if match.group(1):
                            value = match.group(1)
                        elif match.group(2):
                            value = match.group(2)
                        elif match.group(3):
                            value = match.group(3)
                    for template in self.templates:
                        if template['name'] == 'print_statement':
                            code = template['template'].replace('{value}', f'"{value}"')
                            comment = f"# This program prints: {value}"
                            print(comment)
                            print(code)
                            return f"{comment}\n{code}"
            # Try to match a specific construct requested in the prompt
            for template in self.templates:
                if template['name'] in prompt.lower().replace(' ', '_') or template['name'].replace('_', ' ') in prompt.lower():
                    code = template['template']
                    # Try to extract a condition from the prompt
                    condition = 'x > 0'
                    match = re.search(r'(less than|greater than|equal to|not equal to)\s+(\d+)', prompt, re.IGNORECASE)
                    if match:
                        op = match.group(1).lower()
                        num = match.group(2)
                        if op == 'less than':
                            condition = f"x < {num}"
                        elif op == 'greater than':
                            condition = f"x > {num}"
                        elif op == 'equal to':
                            condition = f"x == {num}"
                        elif op == 'not equal to':
                            condition = f"x != {num}"
                    code = code.replace('{condition}', condition)
                    code = code.replace('{item}', 'item').replace('{iterable}', 'my_list').replace('{function_name}', 'my_func').replace('{params}', '').replace('{return_value}', 'None').replace('{module}', 'os').replace('{object}', 'path').replace('{filename}', 'file.txt').replace('{ClassName}', 'MyClass').replace('{exception}', 'Exception').replace('{value}', '42')
                    comment = f"# This program demonstrates: {template['description']}"
                    print(comment)
                    print(code)
                    return f"{comment}\n{code}"
            # If no specific construct, fall back to function definition
            for template in self.templates:
                if template['name'] == 'function_definition':
                    code = template['template'].replace('{function_name}', 'main').replace('{params}', '').replace('{return_value}', 'None')
                    comment = f"# This program defines a main function."
                    print(comment)
                    print(code)
                    return f"{comment}\n{code}"

        # Try to find a math operation in the prompt
        for op, entries in self.math.items():
            if op in prompt.lower():
                entry = entries[0] if entries else None
                if entry:
                    gloss = entry.get('gloss', '')
                    formula = entry.get('formula', '')
                    exec_code = entry.get('exec', '')
                    comment = f"# This code performs {gloss}."
                    print(comment)
                    print(f"# Formula: {formula}")
                    print(f"# Example code: {exec_code}")
                    return f"{comment}\n# Formula: {formula}\nresult = {formula}"

        # Handle inequalities
        inequalities = {
            'greater than or equal to': '>=',
            'less than or equal to': '<=',
            'greater than': '>',
            'less than': '<',
            'not equal to': '!=',
            'equal to': '=='
        }
        for phrase, symbol in inequalities.items():
            if phrase in prompt.lower():
                # Try to extract variable names and numbers
                words = prompt.lower().split()
                var = None
                num = None
                for i, w in enumerate(words):
                    if w in ['than', 'to'] and i > 0 and i < len(words) - 1:
                        var = words[i-1]
                        try:
                            num = int(words[i+1])
                        except Exception:
                            num = words[i+1]
                        break
                if var and num is not None:
                    cue = f"# Checks if {var} {phrase} {num}"
                    comment = f"# This code checks the condition: {var} {symbol} {num}."
                    code = f"if {var} {symbol} {num}:\n    print('{var} {symbol} {num}')"
                    print(cue)
                    print(comment)
                    print(code)
                    return f"{cue}\n{comment}\n{code}"

        # Otherwise, try to answer from definitions.json
        for word in re.findall(r'\w+', prompt.lower()):
            if word in self.definitions:
                answer = self.definitions[word]
                if isinstance(answer, list):
                    comment = f"# Definition of '{word}': {answer[0]}"
                    print(comment)
                    return comment
                else:
                    comment = f"# Definition of '{word}': {answer}"
                    print(comment)
                    return comment

        # Fallback: try to generate code as before
        found = []
        for k in self.knowledge:
            if re.search(r'\\b' + re.escape(k) + r'\\b', prompt, re.IGNORECASE):
                found.append((k, self.knowledge[k]))
        numbers = [int(s) for s in re.findall(r'\\b\\d+\\b', prompt)]
        code_lines = []
        if found and numbers:
            var_name = found[0][0].replace(' ', '_')
            n = numbers[0]
            code_lines.append(f"# Loop {n} times and print the index.")
            code_lines.append(f"for i in range({n}):")
            code_lines.append(f"    print(\"{var_name} number\", i)")
        elif any(word in prompt.lower() for word in ['sum', 'total', 'all', 'any', 'every']):
            arr = [v for _, v in found if isinstance(v, int)]
            if arr:
                code_lines.append(f"# Print the sum of the array.")
                code_lines.append(f"print('Sum:', sum({arr}))")
        elif any(word in prompt.lower() for word in ['relationship', 'pair', 'match']):
            if len(found) >= 2:
                a, b = found[0][0], found[1][0]
                code_lines.append(f"# Print all pairs between {a} and {b}.")
                code_lines.append(f"for {a}_item in {a}_list:")
                code_lines.append(f"    for {b}_item in {b}_list:")
                code_lines.append(f"        print({a}_item, {b}_item)")
        else:
            # If no code detected, treat as metaphor: get definition and try to match to a code template
            for word in re.findall(r'\w+', prompt.lower()):
                if word in self.definitions:
                    definition = self.definitions[word][0] if isinstance(self.definitions[word], list) else self.definitions[word]
                    # Try to match definition or word to a template description
                    for template in self.templates:
                        if word in template['description'].lower() or word in template['name'].lower() or word in definition.lower():
                            comment = f"# Metaphor: '{word}' means '{definition}'. Using template: {template['name']}"
                            code = template['template'].replace('{item}', word).replace('{iterable}', 'my_list').replace('{condition}', 'True').replace('{function_name}', 'my_func').replace('{params}', '').replace('{return_value}', 'None').replace('{module}', 'os').replace('{object}', 'path')
                            print(comment)
                            print(code)
                            return f"{comment}\n{code}"
                    # If no template found, just return the definition as a comment
                    comment = f"# Metaphor: '{word}' means '{definition}'. No code template found."
                    print(comment)
                    return comment
            code_lines.append("# No actionable code structure detected from prompt.")
        print('--- Generated Code ---')
        for line in code_lines:
            print(line)
        return '\n'.join(code_lines)

# Example usage:

def main():
    engine = NaturalCodeEngine('data')
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
