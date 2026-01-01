# Natural Code Engine Project Structure

## Installation

1. (Optional) Create and activate a virtual environment:

   ```sh
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install requirements:

   ```sh
   pip install -r requirements.txt
   ```

3. (Optional) Install as a package (for CLI entry point):

   ```sh
   pip install .
   ```

## Project Structure

- eng1neer.py: Main code/definition engine
- new_natural_code_engine.py: Natural language code engine logic
- data/: Definitions and domain data (JSON)
- requirements.txt: Python dependencies
- setup.py: Install/setup script
- test.py: Test script

## Usage

Run the engine interactively:

```sh
python eng1neer.py
```

Or, if installed as a package:

```sh
natural-code-engine
```

