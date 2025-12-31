# Additional edge case prompts for masterkey testing
edge_cases = [
    "Multiply y by 2 for each of 10 steps, starting from 1",
    "Print 'done' 3 times if flag is True",
    "Add 5 to total every time in a 4 repetition loop, unless total is over 20",
    "Decrement counter by 1 until it reaches 0",
    "For each number in range 5, print the square",
    "If x is less than 10, add 2 to x five times",
    "Print 'hello' for every even number from 0 to 8",
    "Subtract 3 from score 7 times, but only if score is positive",
    "Double the value of a 6 times loop",
    "For 4 rounds, if n is odd, print n and subtract 1 from n"
]

if __name__ == "__main__":
    from new_natural_code_engine import NaturalCodeEngine
    engine = NaturalCodeEngine('data')
    for prompt in edge_cases:
        print(f"\nPrompt: {prompt}\n")
        code = engine.generate_code(prompt)
        print("Generated code:")
        print(code)
        print("-" * 40)
