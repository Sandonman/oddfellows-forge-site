# D&D Character Creator V1

Simple Python CLI for creating a D&D-style character using SRD 5.2.1-inspired (simplified) data.

## Features

- Species/race selection
- Class selection
- Background selection
- Ability score assignment (standard array or manual)
- Proficiency handling:
  - Saving throw proficiencies (from class)
  - Skill proficiencies (from class + background)
- PDF export
- Non-interactive sample generator for quick testing

## Project Structure

- `character_creator/data.py`: SRD-inspired creation data
- `character_creator/models.py`: character model and stat helpers
- `character_creator/pdf_export.py`: no-dependency PDF writer
- `character_creator/cli.py`: interactive CLI + `--sample` mode
- `generate_sample.py`: dedicated sample PDF generator

## Requirements

Python 3.10+.

Install dependencies:

```bash
pip install -r requirements.txt
```

## Run Interactive Mode

```bash
python -m character_creator.cli --output outputs/character.pdf
```

If `--output` is omitted, the default is `outputs/character.pdf`.

## Run Non-Interactive Sample Generation

Option 1 (dedicated script):

```bash
python generate_sample.py
```

Option 2 (CLI mode):

```bash
python -m character_creator.cli --sample --output outputs/sample_character.pdf
```

Expected output file:

- `outputs/sample_character.pdf`

## Notes

This project is inspired by SRD 5.2.1 concepts, with simplified data and rules intended for a lightweight demo.
