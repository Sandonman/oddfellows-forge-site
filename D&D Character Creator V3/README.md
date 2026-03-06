# D&D Character Creator V3

Data-focused workspace for V3 character creator content and validation tests.

## What is in this repo

- `src/cc_v3/data/` - JSON datasets (classes, equipment, monsters, spells, etc.)
- `src/cc_v3/app.py` - Tkinter app shell (top strip + Builder/Library notebook tabs)
- `tests/` - pytest-based validation tests for data loading and schema basics
- `scripts/generate_monsters_json.py` - helper to refresh `monsters.json` from Open5e

## Test harness

Tests validate two things:

1. JSON files are present and readable.
2. Core schema expectations remain stable for monster and equipment data.

## Run tests

From this folder:

```bash
cd "D&D Character Creator V3"
PYTHONPATH=src pytest -q
```

Run the Tkinter shell locally:

```bash
PYTHONPATH=src python -m cc_v3
```

Run only the schema-basics coverage:

```bash
PYTHONPATH=src pytest -q tests/test_data_schema_basics.py
```

## Refresh monsters dataset (optional)

```bash
cd "D&D Character Creator V3"
python3 scripts/generate_monsters_json.py
PYTHONPATH=src pytest -q
```
