"""Reusable code-skill snippets for the NaturalCodeEngine and generators.

Provides `CodeSkillSet` which returns Python source snippets for common
helpers (fibonacci, factorial, IO, safe-eval, HTTP JSON fetch, timer).
Also exposes `synthesize_from_prompt(prompt)` to pick a reasonable snippet
based on keywords.
"""
from typing import Optional
import re


class CodeSkillSet:
    @staticmethod
    def iterative_fib_code() -> str:
        return (
            "def iterative_fib(n: int) -> int:\n"
            "    if n < 0:\n"
            "        raise ValueError(\"n must be >= 0\")\n"
            "    a, b = 0, 1\n"
            "    for _ in range(n):\n"
            "        a, b = b, a + b\n"
            "    return a\n"
        )

    @staticmethod
    def memoized_fib_code() -> str:
        return (
            "def memoized_fib(n: int, cache=None) -> int:\n"
            "    if cache is None:\n"
            "        cache = {}\n"
            "    if n < 2:\n"
            "        return n\n"
            "    if n in cache:\n"
            "        return cache[n]\n"
            "    cache[n] = memoized_fib(n-1, cache) + memoized_fib(n-2, cache)\n"
            "    return cache[n]\n"
        )

    @staticmethod
    def make_fibonacci_class_code() -> str:
        return (
            CodeSkillSet.iterative_fib_code()
            + "\n"
            + CodeSkillSet.memoized_fib_code()
            + (
                "\ndef make_fibonacci_class(name: str = 'Fibonacci', use_memo: bool = True):\n"
                "    def __init__(self):\n"
                "        self._cache = {}\n\n"
                "    def nth(self, n: int) -> int:\n"
                "        if use_memo:\n"
                "            return memoized_fib(n, self._cache)\n"
                "        return iterative_fib(n)\n\n"
                "    def sequence(self, k: int):\n"
                "        return [self.nth(i) for i in range(k)]\n\n"
                "    attrs = {'__init__': __init__, 'nth': nth, 'sequence': sequence}\n"
                "    Fib = type(name, (object,), attrs)\n"
                "    return Fib\n"
            )
        )

    @staticmethod
    def factorial_code() -> str:
        return (
            "def factorial(n: int) -> int:\n"
            "    if n < 0:\n"
            "        raise ValueError('n must be >= 0')\n"
            "    result = 1\n"
            "    for i in range(2, n+1):\n"
            "        result *= i\n"
            "    return result\n"
        )

    @staticmethod
    def io_read_lines_code() -> str:
        return (
            "def read_lines(path):\n"
            "    with open(path, 'r', encoding='utf-8') as f:\n"
            "        return [ln.rstrip('\\n') for ln in f.readlines()]\n"
        )

    @staticmethod
    def io_write_text_code() -> str:
        return (
            "def write_text(path, text):\n"
            "    with open(path, 'w', encoding='utf-8') as f:\n"
            "        f.write(text)\n"
        )

    @staticmethod
    def timer_decorator_code() -> str:
        return (
            "import time\n"
            "def timer(func):\n"
            "    def wrapper(*a, **k):\n"
            "        t0 = time.time()\n"
            "        r = func(*a, **k)\n"
            "        print('elapsed:', time.time()-t0)\n"
            "        return r\n"
            "    return wrapper\n"
        )

    @staticmethod
    def safe_eval_code() -> str:
        return (
            "import ast, operator as _op\n"
            "def safe_eval(expr):\n"
            "    allowed = {ast.Add: _op.add, ast.Sub: _op.sub, ast.Mult: _op.mul, ast.Div: _op.truediv, ast.Pow: _op.pow, ast.USub: _op.neg}\n"
            "    def _eval(node):\n"
            "        if isinstance(node, ast.Constant):\n"
            "            return node.value\n"
            "        if isinstance(node, ast.BinOp):\n"
            "            return allowed[type(node.op)](_eval(node.left), _eval(node.right))\n"
            "        if isinstance(node, ast.UnaryOp):\n"
            "            return allowed[type(node.op)](_eval(node.operand))\n"
            "        raise ValueError('unsupported')\n"
            "    node = ast.parse(expr, mode='eval').body\n"
            "    return _eval(node)\n"
        )

    @staticmethod
    def http_get_json_code() -> str:
        return (
            "import requests\n"
            "def http_get_json(url):\n"
            "    r = requests.get(url)\n"
            "    r.raise_for_status()\n"
            "    return r.json()\n"
        )

    @staticmethod
    def synthesize_from_prompt(prompt: str) -> Optional[str]:
        lp = prompt.lower()
        # priority: fibonacci class
        if 'fibonacci' in lp and 'class' in lp:
            return CodeSkillSet.make_fibonacci_class_code()
        if 'fibonacci' in lp:
            # provide both helpers
            return CodeSkillSet.iterative_fib_code() + '\n' + CodeSkillSet.memoized_fib_code()
        if 'factorial' in lp:
            return CodeSkillSet.factorial_code()
        if 'read_lines' in lp or 'read a list of lines' in lp:
            return CodeSkillSet.io_read_lines_code()
        if 'write_text' in lp or 'write text' in lp:
            return CodeSkillSet.io_write_text_code()
        if 'timer' in lp or 'decorator' in lp:
            return CodeSkillSet.timer_decorator_code()
        if 'safe_eval' in lp or 'evaluate' in lp:
            return CodeSkillSet.safe_eval_code()
        if 'http_get_json' in lp or 'fetch json' in lp or 'requests' in lp:
            return CodeSkillSet.http_get_json_code()
        return None


__all__ = ['CodeSkillSet']
