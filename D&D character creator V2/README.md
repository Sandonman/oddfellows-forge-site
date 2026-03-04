# D&D Character Creator V2

Tkinter desktop app for creating a **level 1 SRD-style D&D character** with local data, hover tooltips, JSON save/load, and printable PDF export.

## Features

- Tabbed GUI sections:
  - Identity
  - Species
  - Class
  - Background
  - Ability Scores
  - Skills/Saving Throws
  - Equipment
  - Spells
  - Summary/Export
- Local SRD JSON data files loaded from `src/ddcc_v2/data/`
- Tooltips for major selectable options:
  - class, species, background
  - skills
  - equipment
  - spells
- Derived stat calculation:
  - ability modifiers
  - proficiency bonus
  - HP, AC baseline, initiative, passive perception
  - spellcasting ability, spell save DC, spell attack bonus
- Save/load character JSON
- Export readable character sheet PDF (pure Python renderer; no heavy dependencies)
- CLI helper to generate sample character JSON/PDF in `outputs/`
- Pytest coverage for calculations + serialization/derivation

## Dataset Note

This project ships with a **local SRD-inspired subset** intended for broad level-1 coverage and easy expansion. It includes major core options (classes, species, backgrounds, skills, baseline equipment, cantrips, level-1 spells). If you need strict canonical parity for a specific SRD release/version, extend or replace the JSON files under `src/ddcc_v2/data/`.

## Project Layout

- `run.py` - launch GUI
- `generate_sample.py` - generate sample outputs
- `src/ddcc_v2/` - package source code
- `src/ddcc_v2/data/` - local JSON datasets
- `tests/` - pytest tests
- `outputs/` - generated JSON/PDF files

## Run

```bash
cd "D&D character creator V2"
python3 -m pip install -r requirements.txt
python3 run.py
```

## Generate Sample Files

```bash
cd "D&D character creator V2"
python3 generate_sample.py
```

Expected output files:

- `outputs/sample_character.json`
- `outputs/sample_character.pdf`

## Run Tests

```bash
cd "D&D character creator V2"
pytest -q
```
