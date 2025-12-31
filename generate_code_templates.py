import re

templates = [
    {
        'name': 'subtract_nested_loop_specific',
        'pattern': r'subtract (\d+) from ([a-zA-Z_][a-zA-Z0-9_]*) (\d+) times in a (\d+) repetition loop if ([^,]+)',
        'code': lambda m: (
            f"{m.group(2)} = 0\n"
            f"for _ in range({m.group(4)}):\n"
            f"    for _ in range({m.group(3)}):\n"
            f"        if {m.group(5)}:\n"
            f"            {m.group(2)} -= {m.group(1)}\n"
            f"    print({m.group(2)})"
        )
    },
    {
        'name': 'add_nested_loop_specific',
        'pattern': r'add (\d+) to ([a-zA-Z_][a-zA-Z0-9_]*) (\d+) times if ([^,]+), during a (\d+) repetition loop',
        'code': lambda m: (
            f"{m.group(2)} = 0\n"
            f"for _ in range({m.group(5)}):\n"
            f"    for _ in range({m.group(3)}):\n"
            f"        if {m.group(4)}:\n"
            f"            {m.group(2)} += {m.group(1)}\n"
            f"    print({m.group(2)})"
        )
    },
    {
        'name': 'recursive_nested_loop',
        'pattern': r'(?:for|repeat|do|nested) (\d+) times? (?:in|inside|within|during|over|through|for) a (\d+) repetition loop(?: if ([^,]+))?(?: with (add|subtract|increment|decrement|multiply|divide) (\d+) to ([a-zA-Z_][a-zA-Z0-9_]*) (?:if ([^,]+))?)?',
        'code': lambda m: (
            f"{m.group(6) or 'x'} = 0\n"
            f"for _ in range({m.group(2)}):\n"
            + (
                f"    for _ in range({m.group(1)}):\n"
                + (
                    f"        if {m.group(7) or m.group(3)}:\n"
                    f"            {m.group(6) or 'x'} {'+=' if m.group(4) in ['add', 'increment'] else '-=' if m.group(4) in ['subtract', 'decrement'] else '*=' if m.group(4) == 'multiply' else '/=' if m.group(4) == 'divide' else '+='} {m.group(5) or 1}\n"
                    if (m.group(7) or m.group(3)) else
                    f"        {m.group(6) or 'x'} {'+=' if m.group(4) in ['add', 'increment'] else '-=' if m.group(4) in ['subtract', 'decrement'] else '*=' if m.group(4) == 'multiply' else '/=' if m.group(4) == 'divide' else '+='} {m.group(5) or 1}\n"
                )
            )
            + f"    print({m.group(6) or 'x'})"
        )
    },
    {
        'name': 'deep_recursive_nested_loop',
        'pattern': r'(?:for|repeat|do|nested) (\d+) times? (?:in|inside|within|during|over|through|for) a (\d+) repetition loop(?: if ([^,]+))?(?: with (add|subtract|increment|decrement|multiply|divide) (\d+) to ([a-zA-Z_][a-zA-Z0-9_]*) (?:if ([^,]+))?)?(?: and (?:for|repeat|do|nested) (\d+) times? (?:in|inside|within|during|over|through|for) a (\d+) repetition loop(?: if ([^,]+))?(?: with (add|subtract|increment|decrement|multiply|divide) (\d+) to ([a-zA-Z_][a-zA-Z0-9_]*) (?:if ([^,]+))?)?)?',
        'code': lambda m: (
            f"{m.group(6) or 'x'} = 0\n"
            f"for _ in range({m.group(2)}):\n"
            + (
                f"    for _ in range({m.group(1)}):\n"
                + (
                    f"        if {m.group(7) or m.group(3)}:\n"
                    f"            {m.group(6) or 'x'} {'+=' if m.group(4) in ['add', 'increment'] else '-=' if m.group(4) in ['subtract', 'decrement'] else '*=' if m.group(4) == 'multiply' else '/=' if m.group(4) == 'divide' else '+='} {m.group(5) or 1}\n"
                    if (m.group(7) or m.group(3)) else
                    f"        {m.group(6) or 'x'} {'+=' if m.group(4) in ['add', 'increment'] else '-=' if m.group(4) in ['subtract', 'decrement'] else '*=' if m.group(4) == 'multiply' else '/=' if m.group(4) == 'divide' else '+='} {m.group(5) or 1}\n"
                )
                + (
                    f"        for _ in range({m.group(8)}):\n"
                    + (
                        f"            if {m.group(13) or m.group(10)}:\n"
                        f"                {m.group(12) or 'y'} {'+=' if m.group(9) in ['add', 'increment'] else '-=' if m.group(9) in ['subtract', 'decrement'] else '*=' if m.group(9) == 'multiply' else '/=' if m.group(9) == 'divide' else '+='} {m.group(11) or 1}\n"
                        if (m.group(13) or m.group(10)) else
                        f"            {m.group(12) or 'y'} {'+=' if m.group(9) in ['add', 'increment'] else '-=' if m.group(9) in ['subtract', 'decrement'] else '*=' if m.group(9) == 'multiply' else '/=' if m.group(9) == 'divide' else '+='} {m.group(11) or 1}\n"
                    )
                )
            )
            + f"    print({m.group(6) or 'x'})"
        )
    },
            # Print/loop templates (prioritized before math wildcards)
            {
                'name': 'print_n_times',
                'pattern': r"print ['\"]?([^'\"]+)['\"]? (\-?\d+) times",
                'code': lambda m: (
                    f"# Print '{m.group(1)}' {m.group(2)} times\n"
                    f"for _ in range({m.group(2)}):\n    print('{m.group(1)}')" if int(m.group(2)) > 0 else f"# Print '{m.group(1)}' 0 times (no output)"
                )
            },
            {
                'name': 'loop_print_n_times',
                'pattern': r"loop that prints ['\"]?([^'\"]+)['\"]? (\-?\d+) times",
                'code': lambda m: (
                    f"# Loop that prints '{m.group(1)}' {m.group(2)} times\n"
                    f"for _ in range({m.group(2)}):\n    print('{m.group(1)}')" if int(m.group(2)) > 0 else f"# Loop that prints '{m.group(1)}' 0 times (no output)"
                )
            },
        {
            'name': 'add_nested_loop',
            'pattern': r'add (\d+) to ([a-zA-Z_][a-zA-Z0-9_]*) (\d+) times(?: if ([^,]+))?,? (?:during|in|inside|within|over|through|for) a (\d+) repetition loop',
            'code': lambda m: (
                f"{m.group(2)} = 0\n"
                f"for _ in range({m.group(5)}):\n"
                + (
                    f"    if {m.group(4)}:\n"
                    f"        for _ in range({m.group(3)}):\n"
                    f"            {m.group(2)} += {m.group(1)}\n"
                    f"        print({m.group(2)})"
                    if m.group(4) else
                    f"    for _ in range({m.group(3)}):\n"
                    f"        {m.group(2)} += {m.group(1)}\n"
                    f"    print({m.group(2)})"
                )
            )
        },
        {
            'name': 'subtract_nested_loop',
            'pattern': r'subtract\s+(\d+)\s+from\s+([a-zA-Z_][a-zA-Z0-9_]*)\s+(\d+)\s+times(?:\s+if\s+([^,]+?))?[,.]?\s*(?:during|in|inside|within|over|through|for)\s+a\s+(\d+)\s+repetition\s+loop',
            'code': lambda m: (
                f"{m.group(2)} = 0\n"
                f"for _ in range({m.group(5)}):\n"
                + (
                    f"    for _ in range({m.group(3)}):\n"
                    f"        if {m.group(4)}:\n"
                    f"            {m.group(2)} -= {m.group(1)}\n"
                    f"    print({m.group(2)})"
                    if m.group(4) else
                    f"    for _ in range({m.group(3)}):\n"
                    f"        {m.group(2)} -= {m.group(1)}\n"
                    f"    print({m.group(2)})"
                )
            )
        },
        # Wildcard templates for math.json words
        {
            'name': 'addition',
            'pattern': r'addition|add|sum|plus',
            'code': lambda m: '# Math operation: addition\n# Formula: a + b\nresult = a + b'
        },
        {
            'name': 'subtraction',
            'pattern': r'subtraction|subtract|minus|difference',
            'code': lambda m: '# Math operation: subtraction\n# Formula: a - b\nresult = a - b'
        },
        {
            'name': 'multiplication',
            'pattern': r'multiplication|multiply|product|times',
            'code': lambda m: '# Math operation: multiplication\n# Formula: a * b\nresult = a * b'
        },
        {
            'name': 'division',
            'pattern': r'division|divide|quotient',
            'code': lambda m: '# Math operation: division\n# Formula: a / b\nresult = a / b'
        },
        {
            'name': 'integer_division',
            'pattern': r'integer division|floor division|//',
            'code': lambda m: '# Math operation: integer division\n# Formula: a // b\nresult = a // b'
        },
        {
            'name': 'modulus',
            'pattern': r'modulus|modulo|mod|remainder|%',
            'code': lambda m: '# Math operation: modulus\n# Formula: a % b\nresult = a % b'
        },
        {
            'name': 'exponent',
            'pattern': r'exponent|power|raise|\^|\*\*',
            'code': lambda m: '# Math operation: exponent\n# Formula: a ** n\nresult = a ** n'
        },
        {
            'name': 'square',
            'pattern': r'square(?! root)',
            'code': lambda m: '# Math operation: square\n# Formula: x ** 2\nresult = x ** 2'
        },
        {
            'name': 'cube',
            'pattern': r'cube(?! root)',
            'code': lambda m: '# Math operation: cube\n# Formula: x ** 3\nresult = x ** 3'
        },
        {
            'name': 'square_root',
            'pattern': r'square root|sqrt',
            'code': lambda m: '# Math operation: square root\n# Formula: x ** 0.5\nresult = x ** 0.5'
        },
        {
            'name': 'cube_root',
            'pattern': r'cube root',
            'code': lambda m: '# Math operation: cube root\n# Formula: x ** (1/3)\nresult = x ** (1/3)'
        },
        {
            'name': 'absolute_value',
            'pattern': r'absolute value|abs',
            'code': lambda m: '# Math operation: absolute value\n# Formula: abs(x)\nresult = abs(x)'
        },
        {
            'name': 'negation',
            'pattern': r'negation|negative|negate',
            'code': lambda m: '# Math operation: negation\n# Formula: -x\nresult = -x'
        },
        {
            'name': 'average',
            'pattern': r'average|mean',
            'code': lambda m: '# Math operation: average\n# Formula: sum(values) / len(values)\nresult = sum(values) / len(values)'
        },
        {
            'name': 'percentage',
            'pattern': r'percentage|percent',
            'code': lambda m: '# Math operation: percentage\n# Formula: (p / 100) * x\nresult = (p / 100.0) * x'
        },
        {
            'name': 'percentage_change',
            'pattern': r'percentage change|percent change',
            'code': lambda m: '# Math operation: percentage change\n# Formula: ((new - old) / old) * 100\nresult = (new - old) / old * 100.0'
        },
        {
            'name': 'order_of_operations',
            'pattern': r'order of operations|pemdas|bodmas',
            'code': lambda m: '# Math operation: order of operations\n# Formula: eval(expr)\nresult = eval(expr)'
        },
        {
            'name': 'for_else_loop',
            'pattern': r'for[- ]?else loop',
            'code': lambda m: (
                '# For-else loop example\n'
                'for item in iterable:\n'
                '    if condition:\n'
                '        break\n'
                'else:\n'
                '    print("No break occurred")'
            )
        },
        {
            'name': 'while_loop',
            'pattern': r'while loop',
            'code': lambda m: (
                '# While loop example\n'
                'i = 0\n'
                'while i < 10:\n'
                '    print(i)\n'
                '    i += 1'
            )
        },
        {
            'name': 'if_elif_else',
            'pattern': r'if[ -]?elif[ -]?else',
            'code': lambda m: (
                '# If-Elif-Else example\n'
                'x = 0\n'
                'if x < 0:\n'
                '    print("Negative")\n'
                'elif x == 0:\n'
                '    print("Zero")\n'
                'else:\n'
                '    print("Positive")'
            )
        },
        {
            'name': 'list_comprehension',
            'pattern': r'list comprehension',
            'code': lambda m: (
                '# List comprehension example\n'
                'squares = [x**2 for x in range(10)]\n'
                'print(squares)'
            )
        },
        {
            'name': 'try_except',
            'pattern': r'try[ -]?except',
            'code': lambda m: (
                '# Try-Except example\n'
                'try:\n'
                '    result = 10 / 0\n'
                'except ZeroDivisionError:\n'
                '    print("Cannot divide by zero")'
            )
        }
    ]
    
def generate_code(prompt: str):
    for template in templates:
        match = re.search(template['pattern'], prompt.lower())
        if match:
            code = template['code'](match)
            comment = f"# This program matches template: {template['name']}"
            print(comment)
            print(code)
            return f"{comment}\n{code}"
    return "# No matching template found."