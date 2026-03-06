# D&D Character Creator V3

Data-focused workspace for V3 character creator content and validation tests.

## What is in this repo

- `src/cc_v3/data/` - JSON datasets (classes, equipment, monsters, spells, etc.)
- `src/cc_v3/app.py` - Tkinter app shell (top strip + Builder/Library notebook tabs)
- `tests/` - pytest-based validation tests for data loading and schema basics
- `scripts/generate_monsters_json.py` - helper to refresh `monsters.json` from Open5e

## Builder coverage (current)

Builder currently exposes five sections:

- **Overview**: class/level/look-ahead plus identity fields (`character_name`, `race_species`, `background`, `alignment`), Character Notes (`character_notes`), and derived stats summary.
- **Stats**: editable ability scores (`STR`, `DEX`, `CON`, `INT`, `WIS`, `CHA`).
- **Skills & Languages**: core skill proficiency toggles plus comma-separated `languages`.
- **Equipment**: editable `starting_gold` and multiline `inventory_text`.
- **Spells**: multiline `prepared_spells_text` (deduped/normalized on save).

Save/Load buttons use a stable default path:

- `outputs/v3_last_state.json` (see `DEFAULT_STATE_PATH` in `persistence.py`).

## Current capabilities (quality slice)

Recently added capabilities and where they live:

- **Export summary preview**: `CharacterCreatorApp._preview_export_summary()` + `get_export_summary_text()` in `src/cc_v3/app.py`; canonical text generation via `generate_export_summary_from_payload(...)`.
- **Snapshot/export rendering parity**: skill lines include deterministic selected/total counts (`(x/4)`), and personality + Character Notes + derived combat lines stay consistent across Builder snapshot and export summary renderers.
- **Shared concise line helpers**: `concise_trait_line`, `concise_notes_line`, and `concise_equipment_line` are the canonical compact renderers used across overview snapshot, Builder snapshot, and export summary paths.
- **Character Notes normalization/persistence contract**: notes are whitespace-normalized, persisted canonically in save payloads/checkpoints, and rendered as deterministic concise `Notes:`/`Character Notes:` lines in snapshot/export/summary views.
- **Release readiness report helper**: `summarize_release_candidate_readiness(...)` produces deterministic ordered checks for pre-release payload validation.
- **JSON import/export helpers**: `export_builder_payload_json`, `import_builder_payload_json`, `export_app_payload_json`, `import_app_payload_json` in `src/cc_v3/persistence.py`.
- **Undo checkpoints**: `push_undo_checkpoint`, `pop_undo_checkpoint`, plus typed wrappers `push_builder_undo_checkpoint` / `push_app_undo_checkpoint` in `src/cc_v3/persistence.py`.
- **Dirty-state status behavior**: `format_shell_status(...)`, `_on_builder_state_change(...)`, `_save_state()`, and `_load_state()` in `src/cc_v3/app.py`.

## Release-ready marker (lane O)

As of this finalization pass, there are no remaining small deterministic gaps identified in docs/contracts/helpers that require code changes for this scope.

Release gate status:

- ✅ Full suite passes with `PYTHONPATH=src pytest -q`
- ✅ Builder snapshot/export helper contracts are covered and deterministic
- ✅ Data schema + persistence/undo/dirty-state guardrails are covered by tests

## Test harness

Tests validate four things:

1. JSON files are present and readable.
2. Core schema expectations remain stable for monster and equipment data.
3. Builder summary/output helpers stay aligned with current Builder fields, including normalized Character Notes rendering.
4. Export preview contracts, JSON helper determinism, undo checkpoint behavior, and dirty-state status transitions remain stable.

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
