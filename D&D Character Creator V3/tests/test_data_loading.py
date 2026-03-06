import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "src" / "cc_v3" / "data"

def load_json(name):
    p = DATA_DIR / name
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def test_load_spells_json():
    data = load_json("spells.json")
    assert isinstance(data, (dict, list))
    # basic sanity: ensure there is a top-level structure
    assert bool(data)


def test_load_equipment_json():
    data = load_json("equipment.json")
    assert isinstance(data, dict)
    assert "armor" in data or "weapons" in data
