# MIGRATION Notes (V3)

This document captures practical migration guidance for V3 data/testing changes.

## Current migration baseline

- Added explicit schema-basics tests for:
  - `monsters.json`
  - `equipment.json` (`armor`, `weapons`, `tools`, and `packs.contents`)
- Existing data-loading tests remain in place.

## Why this matters

These checks make data regressions fail fast when fields are removed, renamed, or changed to incompatible types.

## How to run during migration

From `D&D Character Creator V3`:

```bash
PYTHONPATH=src pytest -q
```

If you are editing only data shape, run the focused file first:

```bash
PYTHONPATH=src pytest -q tests/test_data_schema_basics.py
```

## Expected update flow

1. Update data JSON files.
2. Run focused schema tests.
3. Run full test suite.
4. If a schema change is intentional, update tests in lockstep with the new contract.
