import re

def universal_masterkey(prompt, depth=0, default_var='i'):
    import re
    opmap = {
        'add': '+=', 'plus': '+=', 'sum': '+=', 'increment': '+=', 'increase': '+=', 'raise': '+=',
        'subtract': '-=', 'minus': '-=', 'decrement': '-=', 'decrease': '-=', 'reduce': '-=',
        'multiply': '*=', 'times': '*=', 'product': '*=', 'double': '*=', 'triple': '*=',
        'divide': '/=', 'quotient': '/=', 'halve': '/=',
        'modulo': '%=', 'mod': '%=', 'remainder': '%=', '%': '%=',
        'power': '**=', 'raise_to': '**=', '**': '**=', '^': '**=', '//': '//=',
        'set': '=', 'assign': '=', 'initialize': '=', 'make': '=',
    }
    synonym_map = {
        'increase': 'add', 'raise': 'add', 'sum': 'add',
        'decrease': 'subtract', 'reduce': 'subtract',
        'double': 'multiply', 'triple': 'multiply',
        'halve': 'divide',
        'product': 'multiply', 'times': 'multiply',
        'quotient': 'divide',
        'remainder': 'modulo', 'mod': 'modulo',
        'power': 'power', 'raise_to': 'power',
        'assign': 'set', 'initialize': 'set', 'make': 'set',
    }
    antonym_map = {
        'add': 'subtract', 'increase': 'decrease', 'plus': 'minus', 'increment': 'decrement',
        'subtract': 'add', 'decrease': 'increase', 'minus': 'plus', 'decrement': 'increment',
        'multiply': 'divide', 'double': 'halve', 'divide': 'multiply', 'halve': 'double',
        'and': 'or', 'or': 'and', 'unless': 'if', 'if': 'unless', 'while': 'until', 'until': 'while',
    }
    def normalize_op_word(word):
        word = word.lower()
        return synonym_map.get(word, word)

    # Handle: Add 5 to total every time in a 4 repetition loop, unless total is over 20
    add_unless_match2 = re.search(r"add (\d+) to ([a-zA-Z_][a-zA-Z0-9_]*) every time in a (\d+) repetition loop, unless ([^,]+)", prompt, re.IGNORECASE)
    if add_unless_match2:
        op_value = add_unless_match2.group(1)
        var = add_unless_match2.group(2)
        count = add_unless_match2.group(3)
        cond = add_unless_match2.group(4)
        code = f"{var} = 0\nfor _ in range({count}):\n    if not ({cond}):\n        {var} += {op_value}\n    print({var})"
        return code

    # Handle: If x is less than 10, add 2 to x five times
    if_add_match2 = re.search(r"if ([^,]+),? (add|subtract|increment|decrement|increase|decrease|plus|minus) (\d+) to ([a-zA-Z_][a-zA-Z0-9_]*) (\d+) times", prompt, re.IGNORECASE)
    if if_add_match2:
        cond = if_add_match2.group(1)
        op_word = normalize_op_word(if_add_match2.group(2))
        op_value = if_add_match2.group(3)
        var = if_add_match2.group(4)
        count = if_add_match2.group(5)
        op = opmap.get(op_word, '+=')
        code = f"if {cond}:\n    for _ in range({count}):\n        {var} {op} {op_value}\n    print({var})"
        return code

    # Handle: Subtract 3 from score 7 times, but only if score is positive
    but_if_match = re.search(r"(add|subtract|increment|decrement|increase|decrease|plus|minus) (\d+) from ([a-zA-Z_][a-zA-Z0-9_]*) (\d+) times,? but only if ([^,]+)", prompt, re.IGNORECASE)
    if but_if_match:
        op_word = normalize_op_word(but_if_match.group(1))
        op_value = but_if_match.group(2)
        var = but_if_match.group(3)
        count = but_if_match.group(4)
        cond = but_if_match.group(5)
        op = opmap.get(op_word, '+=')
        code = f"for _ in range({count}):\n    if {cond}:\n        {var} {op} {op_value}\n    print({var})"
        return code

    # Handle: Double the value of a 6 times loop
    double_loop_match = re.search(r"double the value of a (\d+) times? loop", prompt, re.IGNORECASE)
    if double_loop_match:
        count = double_loop_match.group(1)
        code = f"value = 1\nfor _ in range({count}):\n    value *= 2\n    print(value)"
        return code

    # Handle: For 4 rounds, if n is odd, print n and subtract 1 from n
    for_if_and_match = re.search(r"for (\d+) rounds?, if ([^,]+), print ([a-zA-Z_][a-zA-Z0-9_]*) and subtract (\d+) from \\3", prompt, re.IGNORECASE)
    if for_if_and_match:
        rounds = for_if_and_match.group(1)
        cond = for_if_and_match.group(2)
        var = for_if_and_match.group(3)
        sub_val = for_if_and_match.group(4)
        code = f"for _ in range({rounds}):\n    if {cond}:\n        print({var})\n        {var} -= {sub_val}"
        return code
    import re
    # Smoothing and clarifying natural language
    def smooth_prompt(text):
        replacements = [
            (r"\bdo (\w+) (\d+) times\b", r"repeat \1 \2 times"),
            (r"\bfor every\b", "for each"),
            (r"\bfor all\b", "for each"),
            (r"\bprint out\b", "print"),
            (r"\bshow\b", "print"),
            (r"\bdisplay\b", "print"),
            (r"\boutput\b", "print"),
            (r"\bthe value of\b", ""),
            (r"\bthe number of\b", ""),
            (r"\bthe result of\b", ""),
            (r"\bthe sum of\b", "sum"),
            (r"\bthe product of\b", "product"),
            (r"\bthe quotient of\b", "quotient"),
            (r"\bthe remainder of\b", "remainder"),
            (r"\bthe square of\b", "square"),
            (r"\bthe cube of\b", "cube"),
            (r"\bthe double of\b", "double"),
            (r"\bthe triple of\b", "triple"),
            (r"\bthe half of\b", "halve"),
            (r"\bthe\b", ""),
            (r"\bto\b", "to"),
            (r"\bby\b", "by"),
            (r"\bfrom\b", "from"),
            (r"\bwith\b", "with"),
            (r"\busing\b", "using"),
            (r"\bif and only if\b", "if"),
            (r"\bwhen\b", "if"),
            (r"\bwhenever\b", "if"),
            (r"\bunless\b", "unless"),
            (r"\bbut only if\b", "if"),
            (r"\bbut if\b", "if"),
            (r"\bbut\b", "but"),
            (r"\bexcept if\b", "unless"),
            (r"\bexcept when\b", "unless"),
            (r"\bexcept\b", "unless"),
            (r"\bwhile\b", "while"),
            (r"\buntil\b", "until"),
            (r"\bfor (\d+) times\b", r"repeat \1 times"),
            (r"\bfor (\d+) repetitions?\b", r"repeat \1 times"),
            (r"\bfor (\d+) rounds?\b", r"repeat \1 times"),
        ]
        import re
        for pat, repl in replacements:
            text = re.sub(pat, repl, text, flags=re.IGNORECASE)
        return text.strip()

    prompt = smooth_prompt(prompt)
    # Pronoun mapping for third-person subject matter
    pronoun_map = {
        'it': default_var,
        'they': default_var,
        'he': default_var,
        'she': default_var,
        'him': default_var,
        'her': default_var,
        'them': default_var,
        'its': default_var,
        'their': default_var,
    }
    def replace_pronouns(text):
        words = text.split()
        return ' '.join([pronoun_map.get(w.lower(), w) for w in words])

    prompt = replace_pronouns(prompt)

    """
    Universal masterkey: Handles a wide range of English prompt patterns for code generation.
    Supports synonyms, antonyms, and logical connectors (but, unless, or, while, until, for each, etc).
    """
    import re
    opmap = {
        'add': '+=', 'plus': '+=', 'sum': '+=', 'increment': '+=', 'increase': '+=', 'raise': '+=',
        'subtract': '-=', 'minus': '-=', 'decrement': '-=', 'decrease': '-=', 'reduce': '-=',
        'multiply': '*=', 'times': '*=', 'product': '*=', 'double': '*=', 'triple': '*=',
        'divide': '/=', 'quotient': '/=', 'halve': '/=',
        'modulo': '%=', 'mod': '%=', 'remainder': '%=', '%': '%=',
        'power': '**=', 'raise_to': '**=', '**': '**=', '^': '**=', '//': '//=',
        'set': '=', 'assign': '=', 'initialize': '=', 'make': '=',
    }
    synonym_map = {
        'increase': 'add', 'raise': 'add', 'sum': 'add',
        'decrease': 'subtract', 'reduce': 'subtract',
        'double': 'multiply', 'triple': 'multiply',
        'halve': 'divide',
        'product': 'multiply', 'times': 'multiply',
        'quotient': 'divide',
        'remainder': 'modulo', 'mod': 'modulo',
        'power': 'power', 'raise_to': 'power',
        'assign': 'set', 'initialize': 'set', 'make': 'set',
    }
    antonym_map = {
        'add': 'subtract', 'increase': 'decrease', 'plus': 'minus', 'increment': 'decrement',
        'subtract': 'add', 'decrease': 'increase', 'minus': 'plus', 'decrement': 'increment',
        'multiply': 'divide', 'double': 'halve', 'divide': 'multiply', 'halve': 'double',
        'and': 'or', 'or': 'and', 'unless': 'if', 'if': 'unless', 'while': 'until', 'until': 'while',
    }

    def normalize_op_word(word):
        word = word.lower()
        return synonym_map.get(word, word)

    # Handle 'unless', 'but', 'or', 'while', 'until' as logical connectors
    # Example: Add 1 to x 5 times unless x is None
    unless_match = re.search(r"(.+?) unless (.+)", prompt, re.IGNORECASE)
    if unless_match:
        main, cond = unless_match.group(1), unless_match.group(2)
        # Convert 'unless' to 'if not'
        code = universal_masterkey(main, depth=depth, default_var=default_var)
        code = code.replace('if ', f'if not ({cond}) and ', 1) if 'if ' in code else code.replace(':', f' if not ({cond}):', 1)
        return code

    # Example: Do X but Y
    but_match = re.search(r"(.+?) but (.+)", prompt, re.IGNORECASE)
    if but_match:
        main, cond = but_match.group(1), but_match.group(2)
        code = universal_masterkey(main, depth=depth, default_var=default_var)
        # Add a conditional after the main action
        code += f"\n# But: {cond}"
        return code

    # Example: Do X or Y
    or_match = re.search(r"(.+?) or (.+)", prompt, re.IGNORECASE)
    if or_match:
        main, alt = or_match.group(1), or_match.group(2)
        code1 = universal_masterkey(main, depth=depth, default_var=default_var)
        code2 = universal_masterkey(alt, depth=depth, default_var=default_var)
        return code1 + "\n# OR\n" + code2

    # Example: Decrement counter by 1 until it reaches 0
    until_match = re.search(r"(increment|decrement|add|subtract|increase|decrease|plus|minus) ([a-zA-Z_][a-zA-Z0-9_]*) by (\d+) until (.+)", prompt, re.IGNORECASE)
    if until_match:
        op_word = normalize_op_word(until_match.group(1))
        var = until_match.group(2)
        op_value = until_match.group(3)
        cond = until_match.group(4)
        op = opmap.get(op_word, '+=')
        code = f"while not ({cond}):\n    {var} {op} {op_value}\n    print({var})"
        return code

    # Example: Print 'hello' for every even number from 0 to 8
    for_even_match = re.search(r"print ['\"]?([^'\"]+)['\"]? for every even number from (\d+) to (\d+)", prompt, re.IGNORECASE)
    if for_even_match:
        value = for_even_match.group(1)
        start = int(for_even_match.group(2))
        end = int(for_even_match.group(3))
        code = f"for n in range({start}, {end}+1):\n    if n % 2 == 0:\n        print('{value}')"
        return code

    # Example: Add 5 to total every time in a 4 repetition loop, unless total is over 20
    add_unless_match = re.search(r"add (\d+) to ([a-zA-Z_][a-zA-Z0-9_]*) every time in a (\d+) repetition loop, unless ([^,]+)", prompt, re.IGNORECASE)
    if add_unless_match:
        op_value = add_unless_match.group(1)
        var = add_unless_match.group(2)
        count = add_unless_match.group(3)
        cond = add_unless_match.group(4)
        code = f"{var} = 0\nfor _ in range({count}):\n    if not ({cond}):\n        {var} += {op_value}\n    print({var})"
        return code

    # Example: If x is less than 10, add 2 to x five times
    if_add_match = re.search(r"if ([^,]+),? (add|subtract|increment|decrement|increase|decrease|plus|minus) (\d+) to ([a-zA-Z_][a-zA-Z0-9_]*) (\d+) times", prompt, re.IGNORECASE)
    if if_add_match:
        cond = if_add_match.group(1)
        op_word = normalize_op_word(if_add_match.group(2))
        op_value = if_add_match.group(3)
        var = if_add_match.group(4)
        count = if_add_match.group(5)
        op = opmap.get(op_word, '+=')
        code = f"if {cond}:\n    for _ in range({count}):\n        {var} {op} {op_value}\n    print({var})"
        return code

    # Example: For 4 rounds, if n is odd, print n and subtract 1 from n
    for_if_match = re.search(r"for (\d+) rounds?, if ([^,]+), print ([a-zA-Z_][a-zA-Z0-9_]*) and subtract (\d+) from \3", prompt, re.IGNORECASE)
    if for_if_match:
        rounds = for_if_match.group(1)
        cond = for_if_match.group(2)
        var = for_if_match.group(3)
        sub_val = for_if_match.group(4)
        code = f"for _ in range({rounds}):\n    if {cond}:\n        print({var})\n        {var} -= {sub_val}"
        return code

    # Fallback: Try to extract any loop or print pattern
    generic_loop = re.search(r"for (\d+) times?,? (.+)", prompt, re.IGNORECASE)
    if generic_loop:
        count = generic_loop.group(1)
        action = generic_loop.group(2)
        code = f"for _ in range({count}):\n    # {action}"
        return code

    # Fallback: Try to extract any print pattern
    generic_print = re.search(r"print ['\"]?([^'\"]+)['\"]?", prompt, re.IGNORECASE)
    if generic_print:
        value = generic_print.group(1)
        code = f"print('{value}')"
        return code

    return "# No actionable code structure detected from prompt."
import re

def parse_loops_and_ops_v2(prompt, depth=0, default_var='i'):
    import re
    # Handle: Multiply y by 2 for each of 10 steps, starting from 1
    mult_steps_match = re.search(r"multiply ([a-zA-Z_][a-zA-Z0-9_]*) by (\d+) for each of (\d+) steps?, starting from (\d+)", prompt, re.IGNORECASE)
    if mult_steps_match:
        var = mult_steps_match.group(1)
        factor = mult_steps_match.group(2)
        steps = mult_steps_match.group(3)
        start = mult_steps_match.group(4)
        code = f"{var} = {start}\nfor _ in range({steps}):\n    {var} *= {factor}\n    print({var})"
        return code

    # Handle: For each number in range N, print the square
    for_each_range_square = re.search(r"for each number in range (\d+),? print (?:the )?square", prompt, re.IGNORECASE)
    if for_each_range_square:
        rng = for_each_range_square.group(1)
        code = f"for n in range({rng}):\n    print(n ** 2)"
        return code
    
    opmap = {
        'add': '+=', 'plus': '+=', 'sum': '+=', 'increment': '+=', 'increase': '+=', 'raise': '+=',
        'subtract': '-=', 'minus': '-=', 'decrement': '-=', 'decrease': '-=', 'reduce': '-=',
        'multiply': '*=', 'times': '*=', 'product': '*=', 'double': '*=', 'triple': '*=',
        'divide': '/=', 'quotient': '/=', 'halve': '/=',
        'modulo': '%=', 'mod': '%=', 'remainder': '%=', '%': '%=',
        'power': '**=', 'raise_to': '**=', '**': '**=', '^': '**=', '//': '//=',
        'set': '=', 'assign': '=', 'initialize': '=', 'make': '=',
    }
    # Synonym/related word mapping for normalization
    synonym_map = {
        'increase': 'add', 'raise': 'add', 'sum': 'add',
        'decrease': 'subtract', 'reduce': 'subtract',
        'double': 'multiply', 'triple': 'multiply',
        'halve': 'divide',
        'product': 'multiply', 'times': 'multiply',
        'quotient': 'divide',
        'remainder': 'modulo', 'mod': 'modulo',
        'power': 'power', 'raise_to': 'power',
        'assign': 'set', 'initialize': 'set', 'make': 'set',
    }

    def normalize_op_word(word):
        word = word.lower()
        return synonym_map.get(word, word)
    # Handle: Subtract 1 from counter 1000 times when counter is -50
    sub_when_match = re.search(r"(add|subtract|increment|decrement|plus|minus|increase|decrease|reduce|double|triple|halve|product|times|divide|quotient|modulo|mod|remainder|power|raise|raise_to|set|assign|initialize|make) (\d+) (?:to|from) ([a-zA-Z_][a-zA-Z0-9_]*) (\d+) times? when \\3 is (-?\d+)", prompt, re.IGNORECASE)
    if sub_when_match:
        op_word = normalize_op_word(sub_when_match.group(1))
        op_value = sub_when_match.group(2)
        var = sub_when_match.group(3)
        loop_count = sub_when_match.group(4)
        var_init = sub_when_match.group(5)
        op = opmap.get(op_word, '+=')
        code = f"{var} = {var_init}\nfor _ in range({loop_count}):\n    {var} {op} {op_value}\n    print({var})"
        return code

    # Handle: Add 3 to value in 'score' every time in a 7 repetition loop if score is even
    add_value_in_var_match = re.search(r"(add|subtract|increment|decrement|plus|minus|increase|decrease|reduce|double|triple|halve|product|times|divide|quotient|modulo|mod|remainder|power|raise|raise_to|set|assign|initialize|make) (\d+) to value in ['\"]?([a-zA-Z_][a-zA-Z0-9_]*)['\"]? every time in a (\d+) repetition loop(?: if ([^,]+))?", prompt, re.IGNORECASE)
    if add_value_in_var_match:
        op_word = normalize_op_word(add_value_in_var_match.group(1))
        op_value = add_value_in_var_match.group(2)
        var = add_value_in_var_match.group(3)
        outer_count = add_value_in_var_match.group(4)
        cond = add_value_in_var_match.group(5)
        op = opmap.get(op_word, '+=')
        code = f"{var} = 0\nfor _ in range({outer_count}):\n"
        if cond:
            code += f"    if {cond}:\n        {var} {op} {op_value}\n"
        else:
            code += f"    {var} {op} {op_value}\n"
        code += f"    print({var})"
        return code

    # Handle print 'X' N times or code a loop that prints 'X' N times
    print_match = re.search(r"print ['\"]?([^'\"]+)['\"]? (?:-|)(\d+) times", prompt, re.IGNORECASE)
    if not print_match:
        print_match = re.search(r"code a loop that prints ['\"]?([^'\"]+)['\"]? (?:-|)(\d+) times", prompt, re.IGNORECASE)
    if print_match:
        value = print_match.group(1)
        count = int(print_match.group(2))
        if count <= 0:
            return f"# Print '{value}' {count} times (no output)"
        return f"# Print '{value}' {count} times\nfor _ in range({count}):\n    print('{value}')"

    # Handle initialization: when X is Y
    init_match = re.search(r"when ([a-zA-Z_][a-zA-Z0-9_]*) is (-?\d+)", prompt)
    var_init = None
    var_name = None
    if init_match:
        var_name = init_match.group(1)
        var_init = init_match.group(2)

    # Handle: Add/Subtract/Increment/Decrement N to/from VAR every time in/inside/during a M repetition loop if ...
    loop_match = re.search(r"(add|subtract|increment|decrement|plus|minus) (\d+) (?:to|from)? ?(?:value in |)([a-zA-Z_][a-zA-Z0-9_']*) (\d+) times?(?: every time in| inside| during| in| within| over| through| for)? a (\d+) repetition loop(?: if ([^,]+))?", prompt, re.IGNORECASE)
    if loop_match:
        op_word = loop_match.group(1).lower()
        op_value = loop_match.group(2)
        var = loop_match.group(3).replace("'", "")
        inner_count = loop_match.group(4)
        outer_count = loop_match.group(5)
        cond = loop_match.group(6)
        op = opmap.get(op_word, '+=')
        code = ''
        if var_init is not None and var_name == var:
            code += f"{var} = {var_init}\n"
        else:
            code += f"{var} = 0\n"
        code += f"for _ in range({outer_count}):\n"
        code += f"    for _ in range({inner_count}):\n"
        if cond:
            code += f"        if {cond}:\n"
            code += f"            {var} {op} {op_value}\n"
        else:
            code += f"        {var} {op} {op_value}\n"
        code += f"    print({var})"
        return code

    # Handle: Decrement/Increment VAR N times inside a M repetition loop if ...
    decinc_match = re.search(r"(decrement|increment) ([a-zA-Z_][a-zA-Z0-9_]*) (\d+) times? (?:inside|during|in|within|over|through|for)? a (\d+) repetition loop(?: if ([^,]+))?", prompt, re.IGNORECASE)
    if decinc_match:
        op_word = decinc_match.group(1).lower()
        var = decinc_match.group(2)
        inner_count = decinc_match.group(3)
        outer_count = decinc_match.group(4)
        cond = decinc_match.group(5)
        op = opmap.get(op_word, '+=')
        code = f"{var} = 0\nfor _ in range({outer_count}):\n    for _ in range({inner_count}):\n"
        if cond:
            code += f"        if {cond}:\n            {var} {op} 1\n"
        else:
            code += f"        {var} {op} 1\n"
        code += f"    print({var})"
        return code

    # Fallback: nothing matched
    return ''
    """
    generate_code_templates.py
    -------------------------
    Recursively generates Python code for loops and operations from natural language prompts.
    Usage:
        - Import and call generate_code(prompt: str)
        - Or run as a script: python generate_code_templates.py "<your prompt>"
    """
    import re

def parse_loops_and_ops(prompt, depth=0, default_var='i'):
    # Recursively parse for loop/operation/conditional patterns
    opmap = {'add': '+=', 'plus': '+=', 'sum': '+=', 'increment': '+=',
             'subtract': '-=', 'minus': '-=', 'decrement': '-=',
             'multiply': '*=', 'times': '*=', 'product': '*=',
             'divide': '/=', 'quotient': '/=',
             'modulo': '%=', 'mod': '%=', 'remainder': '%=', '%': '%=',
             'power': '**=', 'raise': '**=', '**': '**=', '^': '**=', '//': '//='}
    # Pattern for: operation, value, variable, inner loop, optional condition, outer loop, optional between-loop condition
    pattern = re.compile(
        r"(?P<op_word>add|plus|sum|increment|subtract|minus|decrement|multiply|times|product|divide|quotient|modulo|mod|remainder|power|raise|\*\*|\^|//|%) "
        r"(?P<op_value>\d+) to (?P<var>[a-zA-Z_][a-zA-Z0-9_]*)"  # operation, value, variable
        r" (?P<inner_count>\d+) times"  # inner loop
        r"(?: if (?P<cond>[^,]+?))?"  # optional condition after inner_count
        r"(?:,?\s*)?"  # allow for optional comma and whitespace before outer loop phrase
        r"(?:during|in|inside|within|over|through|for)? ?a (?P<outer_count>\d+) repetition loop"  # outer loop
        r"(?:,? ?(?P<between_cond>if [^,]+?))?",  # optional between-loop condition at the end
        re.IGNORECASE
    )
    match = pattern.search(prompt)
    if not match:
        # Try to match initialization: when X is Y
        init_match = re.search(r"when ([a-zA-Z_][a-zA-Z0-9_]*) is (-?\d+)", prompt)
        if init_match:
            var_name = init_match.group(1)
            var_init = init_match.group(2)
            # Remove the initialization phrase from the prompt and try again
            prompt_wo_init = re.sub(r"when [a-zA-Z_][a-zA-Z0-9_]* is -?\d+", "", prompt).strip(', ') 
            code = f"{var_name} = {var_init}\n"
            rest_code = parse_loops_and_ops(prompt_wo_init, depth=depth, default_var=var_name)
            if rest_code:
                code += rest_code
            return code
        return ''

    # 1. Name variables meaningfully
    var = match.group('var') if match.group('var') else default_var
    op = opmap.get(match.group('op_word'), '+=')
    val = match.group('op_value')
    inner_count = match.group('inner_count')
    cond = match.group('cond')
    between_cond = match.group('between_cond')
    outer_count = match.group('outer_count') if match.group('outer_count') is not None else '1'
    indent = '    ' * depth

    # 2. Initialize variables at the top
    code = f"{indent}{var} = 0\n"

    # 3. Add recursion check or conditional (if needed)
    if between_cond:
        code += f"{indent}if {between_cond[3:]}:\n"  # strip 'if '
        indent += '    '

    # 4. Add the first (outer) loop
    code += f"{indent}for _ in range({outer_count}):\n"
    indent += '    '

    # 5. Add the inner loop
    code += f"{indent}for _ in range({inner_count}):\n"
    indent += '    '

    # 6. Add the conditional for the operation (if needed)
    if cond:
        code += f"{indent}if {cond}:\n"
        indent += '    '
        code += f"{indent}{var} {op} {val}\n"
        indent = indent[:-4]  # remove one indent after operation
    else:
        code += f"{indent}{var} {op} {val}\n"

    # 7. Print or return the result after the loops
    indent = '    ' * (depth + 1)
    code += f"{indent}print({var})\n"

    # 8. Repeat for additional operations/loops recursively
    rest = prompt[match.end():].lstrip(', and')
    if rest.strip():
        next_code = parse_loops_and_ops(rest, depth=depth, default_var=default_var)
        if next_code:
            code += '\n' + next_code
    return code

def generate_code(prompt: str):
    # Special pattern for recursive factorial
    import re
    rec_match = re.search(r"define a function (\w+) that returns (\d+) if (\w+) is (\d+), otherwise returns (\w+) times \1 of \3 minus (\d+)", prompt.lower())
    if rec_match:
        func = rec_match.group(1)
        base_val = rec_match.group(2)
        var = rec_match.group(3)
        base_case = rec_match.group(4)
        recur_var = rec_match.group(5)
        minus_val = rec_match.group(6)
        code = f"def {func}({var}):\n    if {var} == {base_case}:\n        return {base_val}\n    else:\n        return {recur_var} * {func}({var} - {minus_val})"
        return code

    # ...existing code for combining masterkeys and function wrapping...
    def make_func_name(prompt):
        match = re.search(r'(?:function|define|create|make|build|write|implement) (\w+)', prompt.lower())
        if match:
            return match.group(1)
        match2 = re.search(r'(add|subtract|increment|decrement|print|code|multiply|divide|sum|average|filter|sort|remove|append|extend|replace|update|clear|copy|reverse|join|split|strip|find|search|match|case|switch|try|except|finally|raise|assert|with|as|from|pass|continue|break|yield|lambda|generator|comprehension|tuple|set|frozenset|bool|int|float|str|bytes|bytearray|memoryview|complex|super|self|staticmethod|classmethod|property|del|global|nonlocal|assert|async|await|true|false|none)\s+([a-zA-Z_][a-zA-Z0-9_]*)', prompt.lower())
        if match2:
            return f"{match2.group(1)}_{match2.group(2)}"
        return "generated_function"

    def wrap_in_function(code, func_name):
        if code.lstrip().startswith('def '):
            return code
        code_lines = code.splitlines()
        indented = '\n'.join('    ' + line if line.strip() else '' for line in code_lines)
        return f"def {func_name}():\n{indented}\n"

    code_blocks = []
    comments = []
    code = parse_loops_and_ops(prompt)
    if code:
        comments.append(f"# MASTERKEY: This program was generated recursively from the prompt.")
        code_blocks.append(code)
    code2 = parse_loops_and_ops_v2(prompt)
    if code2:
        comments.append(f"# MASTERKEY2: This program was generated from the prompt using natural language patterns.")
        code_blocks.append(code2)
    code3 = universal_masterkey(prompt)
    if code3 and not code3.startswith('# No actionable'):
        comments.append(f"# UNIVERSAL MASTERKEY: This program was generated from the prompt using broad pattern matching.")
        code_blocks.append(code3)
    if code_blocks:
        func_name = make_func_name(prompt)
        combined_code = '\n'.join(code_blocks)
        comment = '\n'.join(comments)
        print(comment)
        print(combined_code)
        return f"{comment}\n{wrap_in_function(combined_code, func_name)}"
    return "# No matching loop/operation pattern found."
def make_func_name(prompt):
    # Try to extract a function name from the prompt, fallback to 'generated_function'
    match = re.search(r'(?:function|define|create|make|build|write|implement) (\w+)', prompt.lower())
    if match:
        return match.group(1)
    # Otherwise, use first verb + variable as a name
    match2 = re.search(r'(add|subtract|increment|decrement|print|code|multiply|divide|sum|average|filter|sort|remove|append|extend|replace|update|clear|copy|reverse|join|split|strip|find|search|match|case|switch|try|except|finally|raise|assert|with|as|from|pass|continue|break|yield|lambda|generator|comprehension|tuple|set|frozenset|bool|int|float|str|bytes|bytearray|memoryview|complex|super|self|staticmethod|classmethod|property|del|global|nonlocal|assert|async|await|true|false|none)\s+([a-zA-Z_][a-zA-Z0-9_]*)', prompt.lower())
    if match2:
        return f"{match2.group(1)}_{match2.group(2)}"
    return "generated_function"

def wrap_in_function(code, func_name):
    # Only wrap if not already a function definition
    if code.lstrip().startswith('def '):
        return code
    # Indent code
    code_lines = code.splitlines()
    indented = '\n'.join('    ' + line if line.strip() else '' for line in code_lines)
    return f"def {func_name}():\n{indented}\n"

    # Try all masterkeys and combine if multiple code blocks are found
    code_blocks = []
    comments = []
    code = parse_loops_and_ops(prompt)
    if code:
        comments.append(f"# MASTERKEY: This program was generated recursively from the prompt.")
        code_blocks.append(code)
    code2 = parse_loops_and_ops_v2(prompt)
    if code2:
        comments.append(f"# MASTERKEY2: This program was generated from the prompt using natural language patterns.")
        code_blocks.append(code2)
    code3 = universal_masterkey(prompt)
    if code3 and not code3.startswith('# No actionable'):
        comments.append(f"# UNIVERSAL MASTERKEY: This program was generated from the prompt using broad pattern matching.")
        code_blocks.append(code3)
    if code_blocks:
        # Combine all code blocks into one function
        func_name = make_func_name(prompt)
        combined_code = '\n'.join(code_blocks)
        comment = '\n'.join(comments)
        print(comment)
        print(combined_code)
        return f"{comment}\n{wrap_in_function(combined_code, func_name)}"
    return "# No matching loop/operation pattern found."

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        prompt = ' '.join(sys.argv[1:])
        print(generate_code(prompt))
    else:
        print("Usage: python generate_code_templates.py <your prompt>")
