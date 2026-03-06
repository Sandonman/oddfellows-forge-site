import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "src" / "cc_v3" / "data"

def load_json(name):
    p = DATA_DIR / name
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def test_load_monsters_json_exists():
    p = DATA_DIR / "monsters.json"
    assert p.exists(), f"monsters.json missing at {p}"


def test_monsters_json_valid():
    p = DATA_DIR / "monsters.json"
    if p.exists():
        data = load_json("monsters.json")
        assert isinstance(data, (list, dict))
