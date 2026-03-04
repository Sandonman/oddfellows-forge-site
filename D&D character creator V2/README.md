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
- Expanded progression and spell datasets for future multi-level implementation

## Dataset Note

This project ships with a **local SRD-inspired open-content-style dataset** intended for current level-1 play plus future expansion.

- `classes.json` now includes `level_progression` entries for levels `1..20` for every class.
- Each class progression row includes:
  - `features_summary`
  - `proficiency_bonus`
  - `spellcasting` metadata (where applicable), including:
    - full-caster slot progression
    - half-caster slot progression
    - warlock pact slots + pact slot level + mystic arcanum unlock markers
- `spells.json` now includes spells across levels `0..9`, with:
  - class eligibility (`classes`)
  - concise text fields (`description`, `rules_text`)
- `spells_by_class.json` provides a grouped class-level index (`class -> spell level -> spell names`) for future UI/service expansion.

Current app behavior remains intentionally level-1 oriented (GUI spell picker still surfaces cantrips + level-1 spells), but the data layer is ready for multi-level features.

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
