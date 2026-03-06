# Smoke Matrix (Finalization Lane O)

Deterministic QA sweep artifact for release handoff.

## Validation commands

```bash
# Full deterministic suite (release gate)
PYTHONPATH=src pytest -q

# Focused smoke slices used as stable anchors
PYTHONPATH=src pytest -q tests/test_data_schema_basics.py
PYTHONPATH=src pytest -q tests/test_concise_rendering_contracts.py
PYTHONPATH=src pytest -q tests/test_export_summary.py
PYTHONPATH=src pytest -q tests/test_persistence.py tests/test_undo_checkpoints.py tests/test_status_transitions.py
```

## Stable surfaces covered

- **Data loading + schema invariants**
  - `test_data_loading.py`
  - `test_data_loading_monsters.py`
  - `test_data_schema_basics.py`
  - `test_spell_dataset_qa.py`
- **Builder snapshot/export concise rendering contracts**
  - `test_concise_rendering_contracts.py`
  - `test_summary_coherence.py`
  - `test_change_summary.py`
  - `test_export_summary.py`
- **Persistence + undo + status transitions**
  - `test_persistence.py`
  - `test_undo_checkpoints.py`
  - `test_status_transitions.py`
  - `test_app_shell_persistence_hooks.py`
- **Release-readiness deterministic helpers/workflows**
  - `test_release_candidate_readiness.py`
  - `test_release_check_workflows.py`
  - `test_release_readiness_summary_chain.py`
  - `test_readiness_concise_cycle_stability.py`

## Final sweep result

- Command: `PYTHONPATH=src pytest -q`
- Result: **140 passed**
- Runtime: **0.42s**
- Known limits observed in this lane: **none new** (no production behavior changes required).
