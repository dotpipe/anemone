Patch Kingdom JSON Patcher
==========================

Usage (local):

```
python scripts/patch_kingdom_json.py --file data/generated_kingdoms.json --grep "old" --replace "new" --layer loop --dry-run
```

If the package is installed, the CLI entry `patch-kingdom-json` is available:

```
patch-kingdom-json --file data/generated_kingdoms.json --grep "old" --replace "new" --inplace
```

Features:
- Plain or regex search/replace
- Layer-scoped edits (e.g., `--layer loop`)
- Dry-run and in-place backup (`.bak`)

CLI to manage pending previews
-----------------------------

A chat-preview of a patch is saved to `data/pending_patches.json`. Use the included CLI to manage these:

```
python scripts/pending_patches_cli.py list
python scripts/pending_patches_cli.py preview <pending_id>
python scripts/pending_patches_cli.py apply <pending_id> [--inplace] [--out path/to/file.json]
python scripts/pending_patches_cli.py remove <pending_id>
```

Notes:
- Preview mode (default) does not write files. Use `apply ... --inplace` to write and create a `.bak`.
- The pending store persists across sessions in `data/pending_patches.json`.

Live editor
-----------

You can run a small local editor that shows layers and paragraphs and lets you edit them in a large text box. Edits are saved on blur and a `.bak` copy of the JSON file is created automatically.

Start the editor:

```powershell
python scripts/kingdom_editor.py
# then open in your browser:
http://127.0.0.1:8001/editor?path=data/generated_kingdoms.json
```

The editor page is located at `examples/editor.html` and saves paragraph edits via `/api/update_paragraph`.
