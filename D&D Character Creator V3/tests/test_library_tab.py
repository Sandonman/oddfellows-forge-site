from pathlib import Path

from cc_v3.library_tab import format_library_detail, load_library_index


DATA_DIR = Path(__file__).resolve().parent.parent / "src" / "cc_v3" / "data"


def test_library_index_loads_expected_sections():
    index = load_library_index(DATA_DIR)
    assert set(index.keys()) == {"Spells", "Magic Items", "Monsters"}
    assert len(index["Spells"]) > 0
    assert len(index["Magic Items"]) > 0
    assert len(index["Monsters"]) > 0


def test_library_detail_formatters_smoke():
    index = load_library_index(DATA_DIR)

    spell_text = format_library_detail("Spells", index["Spells"][0])
    item_text = format_library_detail("Magic Items", index["Magic Items"][0])
    monster_text = format_library_detail("Monsters", index["Monsters"][0])

    assert "Name:" in spell_text
    assert "Name:" in item_text
    assert "Name:" in monster_text
