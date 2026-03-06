from cc_v3.builder_tab import (
    format_builder_summary,
    format_equipment_summary,
    format_skills_languages_summary,
    format_spells_summary,
    format_stats_summary,
)
from cc_v3.leveling import build_level_snapshot


def test_builder_summary_includes_gained_and_visible_features_without_lookahead():
    snap = build_level_snapshot("Fighter", 3, look_ahead=False)
    text = format_builder_summary(snap, look_ahead=False)

    assert "Gained at this level:" in text
    assert "Visible features:" in text
    for feature in snap.gained_features:
        assert f"- {feature}" in text


def test_builder_summary_shows_future_feature_tags_with_lookahead():
    snap = build_level_snapshot("Fighter", 3, look_ahead=True)
    text = format_builder_summary(snap, look_ahead=True)

    assert "Look Ahead: On" in text
    assert any(line.startswith("- L20:") for line in text.splitlines())


def test_builder_scaffold_sections_include_build_context():
    snap = build_level_snapshot("Wizard", 5, look_ahead=False)

    stats = format_stats_summary(snap)
    skills = format_skills_languages_summary(snap)
    equipment = format_equipment_summary(snap)
    spells = format_spells_summary(snap)

    assert "Stats (Scaffold)" in stats
    assert "Current class: Wizard" in stats
    assert "Skills & Languages (Scaffold)" in skills
    assert "Build context: Wizard level 5" in skills
    assert "Equipment (Scaffold)" in equipment
    assert "Build context: Wizard level 5" in equipment
    assert "Spells (Scaffold)" in spells
    assert "Spellcasting status:" in spells
