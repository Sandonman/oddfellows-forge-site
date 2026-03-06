from cc_v3.builder_tab import (
    format_builder_summary,
    format_builder_validation_summary,
    format_character_snapshot,
    format_derived_stats_summary,
    format_equipment_summary,
    format_skills_languages_summary,
    format_spells_summary,
    format_stats_summary,
    generate_builder_validation_messages,
)
from cc_v3.leveling import LevelSnapshot, build_level_snapshot
from cc_v3.persistence import deserialize_builder_state


def test_builder_validation_messages_covers_missing_essentials_and_out_of_range_level():
    messages = generate_builder_validation_messages(
        class_name="",
        level_input=99,
        normalized_level=20,
        character_name="",
        ability_scores={},
    )

    assert "missing name" in messages
    assert "no class selected" in messages
    assert "level adjusted to 20 (valid range 1-20)" in messages
    assert "ability scores using default set" in messages


def test_builder_validation_summary_is_compact():
    text = format_builder_validation_summary(["missing name", "no class selected"])
    assert text == "Validation: missing name; no class selected"
    assert format_builder_validation_summary([]) == "Validation: OK"


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
    assert "Validation: missing name; ability scores using default set" in text
    assert any(line.startswith("- L20:") for line in text.splitlines())


def test_builder_summary_renders_identity_defaults_when_fields_missing():
    snap = build_level_snapshot("Fighter", 1, look_ahead=False)

    text = format_builder_summary(snap, look_ahead=False)

    assert "Validation: missing name; ability scores using default set" in text
    assert "Identity:" in text
    assert "Name: Unnamed" in text
    assert "Race/Species: Unspecified" in text
    assert "Background: Unspecified" in text
    assert "Trait: None" in text
    assert "Ideal: None" in text
    assert "Bond: None" in text
    assert "Flaw: None" in text
    assert "Character Notes: None" in text
    assert "Alignment: Unspecified" in text


def test_builder_scaffold_sections_include_build_context():
    snap = build_level_snapshot("Wizard", 5, look_ahead=False)

    stats = format_stats_summary(snap, {"STR": 15, "DEX": 14, "CON": 13, "INT": 12, "WIS": 10, "CHA": 8})
    skills = format_skills_languages_summary(
        snap,
        {"Acrobatics": True, "Arcana": True, "Athletics": False, "Perception": False},
        "Common, Elvish",
    )
    equipment = format_equipment_summary(snap, 12, "Rope\nTorch")
    spells = format_spells_summary(snap, "Mage Armor\nShield\nMage Armor")

    assert "Stats" in stats
    assert "- STR: 15 (+2)" in stats
    assert "- CHA: 8 (-1)" in stats
    assert "Current class: Wizard" in stats
    assert "Skills & Languages" in skills
    assert "Skill proficiencies: Acrobatics, Arcana" in skills
    assert "Languages: Common, Elvish" in skills
    assert "Build context: Wizard level 5" in skills
    assert "Equipment" in equipment
    assert "Starting gold: 12 gp" in equipment
    assert "- Rope" in equipment
    assert "- Torch" in equipment
    assert "Build context: Wizard level 5" in equipment
    assert "Spells" in spells
    assert "Spellcasting ability: INT" in spells
    assert "Spellcasting status: full caster (INT)" in spells
    assert "- Mage Armor" in spells
    assert "- Shield" in spells
    assert spells.count("Mage Armor") == 1


def test_stats_summary_clamps_and_shows_modifiers_for_normalized_scores():
    snap = build_level_snapshot("Fighter", 1, look_ahead=False)

    stats = format_stats_summary(snap, {"STR": 99, "DEX": -5, "CON": "x"})

    assert "- STR: 30 (+10)" in stats
    assert "- DEX: 1 (-5)" in stats
    assert "- CON: 10 (+0)" in stats


def test_skills_languages_summary_normalizes_empty_values():
    snap = build_level_snapshot("Cleric", 2, look_ahead=False)

    skills = format_skills_languages_summary(
        snap,
        {"Arcana": 1, "Acrobatics": 0},
        " Common, , Dwarvish  ,",
    )

    assert "Skill proficiencies: Arcana" in skills
    assert "Languages: Common, Dwarvish" in skills


def test_equipment_summary_normalizes_gold_and_inventory_text():
    snap = build_level_snapshot("Cleric", 2, look_ahead=False)

    equipment = format_equipment_summary(
        snap,
        -20,
        " Rope  \n\n Torch\n  ",
    )

    assert "Starting gold: 0 gp" in equipment
    assert "- Rope" in equipment
    assert "- Torch" in equipment


def test_derived_stats_summary_calculates_hp_passive_perception_and_spell_metrics():
    snap = build_level_snapshot("Wizard", 5, look_ahead=False)

    lines = format_derived_stats_summary(
        snap,
        {"STR": 8, "DEX": 14, "CON": 14, "INT": 16, "WIS": 12, "CHA": 10},
        {"Perception": True},
    )
    text = "\n".join(lines)

    assert "HP baseline estimate: 38 (rule: 8 + 5×(level-1) + CON mod×level)" in text
    assert "Passive Perception: 14" in text
    assert "Spell save DC / spell attack: 14 / +6 (INT)" in text


def test_builder_summary_renders_validation_strip_for_level_adjustment():
    snap = build_level_snapshot("Cleric", 20, look_ahead=False)

    text = format_builder_summary(
        snap,
        look_ahead=False,
        character_name="Aela",
        ability_scores={"STR": 10, "DEX": 10, "CON": 10, "INT": 10, "WIS": 10, "CHA": 10},
        level_input=99,
    )

    assert "Validation: level adjusted to 20 (valid range 1-20)" in text


def test_builder_summary_renders_derived_stats_block_with_live_inputs():
    snap = build_level_snapshot("Cleric", 4, look_ahead=False)

    text = format_builder_summary(
        snap,
        look_ahead=False,
        ability_scores={"CON": 16, "WIS": 18},
        skill_proficiencies={"Perception": True},
    )

    assert "Derived stats:" in text
    assert "HP baseline estimate: 35 (rule: 8 + 5×(level-1) + CON mod×level)" in text
    assert "Passive Perception: 16" in text
    assert "Derived Combat: Initiative +0 | Passive Perception 16 | Attack Baseline +2 to hit, +0 damage mod (best STR/DEX)" in text
    assert "Spell save DC / spell attack: 14 / +6 (WIS)" in text


def test_derived_stats_spellcasting_fallback_when_ability_missing():
    snap = LevelSnapshot(
        class_name="TestCaster",
        level=3,
        proficiency_bonus=2,
        gained_features=[],
        visible_features=[],
        spellcasting={"caster_type": "full"},
    )

    lines = format_derived_stats_summary(snap, {"INT": 12}, {"Perception": False})
    text = "\n".join(lines)

    assert "Spell save DC / spell attack: fallback to INT (class spellcasting ability missing)" in text


def test_section_output_helpers_match_current_builder_sections():
    """Overview/Stats/Skills & Languages/Equipment/Spells should stay in sync with helper outputs."""
    snap = build_level_snapshot("Wizard", 5, look_ahead=False)

    overview = format_builder_summary(
        snap,
        look_ahead=False,
        character_name="Elora",
        race_species="Elf",
        background="Sage",
        alignment="Neutral Good",
        ability_scores={"CON": 14, "WIS": 12, "INT": 16},
        skill_proficiencies={"Perception": True, "Arcana": True},
    )
    stats = format_stats_summary(snap, {"STR": 9, "DEX": 14, "CON": 14, "INT": 16, "WIS": 12, "CHA": 10})
    skills_languages = format_skills_languages_summary(
        snap,
        {"Arcana": True, "Perception": True, "Athletics": False, "Acrobatics": False},
        "Common, Elvish",
    )
    equipment = format_equipment_summary(snap, 25, "Rope\nTorch")
    spells = format_spells_summary(snap, "Mage Armor\nShield")

    # Overview tab content comes from the builder summary helper.
    assert "Class: Wizard" in overview
    assert "Identity:" in overview
    assert "Derived stats:" in overview

    # Section helper headers should match tab names where applicable.
    assert stats.splitlines()[0] == "Stats"
    assert skills_languages.splitlines()[0] == "Skills & Languages"
    assert equipment.splitlines()[0] == "Equipment"
    assert spells.splitlines()[0] == "Spells"

    # Non-overview helper outputs should keep a shared build context format.
    for text in (skills_languages, equipment, spells):
        assert "Build context: Wizard level 5" in text


def test_character_snapshot_includes_key_export_fields_with_normalized_values():
    snap = build_level_snapshot("Wizard", 5, look_ahead=False)

    text = format_character_snapshot(
        snap,
        character_name="  Elora  ",
        race_species=" Elf ",
        background=" Sage ",
        trait="  Always polishing my spellbook.\n",
        ideal=" Knowledge should be shared. ",
        bond=" The old academy archive. ",
        flaw=" I underestimate practical people. ",
        character_notes="  Needs rare inks for rituals.\n\n  Owes guild dues.  ",
        alignment="Neutral Good",
        ability_scores={"STR": 9, "DEX": 18, "CON": 14, "INT": 16, "WIS": 11, "CHA": None},
        skill_proficiencies={"Athletics": 1, "Arcana": "yes", "Perception": "", "Acrobatics": 0},
        languages=" Common, Elvish, Common ",
        starting_gold="42",
        inventory_text=" Rope\n\n Torch ",
        prepared_spells_text=" Mage Armor\n\nShield\nMage Armor ",
    )

    assert "Character Snapshot:" in text
    assert "Identity: Elora | Elf | Sage | Neutral Good" in text
    assert "Class/Level: Wizard 5" in text
    assert "Personality: Trait=Always polishing my spellbook. | Ideal=Knowledge should be shared. | Bond=The old academy archive. | Flaw=I underestimate practical people." in text
    assert "Notes: Needs rare inks for rituals." in text
    assert "Ability Scores: STR 9 (-1), DEX 18 (+4), CON 14 (+2), INT 16 (+3), WIS 11 (+0), CHA 10 (+0)" in text
    assert "Derived Combat: Initiative +4 | Passive Perception 10 | Attack Baseline +7 to hit, +4 damage mod (best STR/DEX)" in text
    assert "Skills: Arcana, Athletics (2/4)" in text
    assert "Languages: Common, Elvish" in text
    assert "Equipment: 42 gp; 2 item(s): Rope, Torch" in text
    assert "Prepared Spells Count: 2" in text


def test_builder_summary_includes_character_snapshot_block_for_overview_consistency():
    snap = build_level_snapshot("Wizard", 5, look_ahead=False)

    overview = format_builder_summary(
        snap,
        look_ahead=False,
        character_name="Elora",
        race_species="Elf",
        background="Sage",
        trait="  Keeps a travel journal.\n",
        ideal="  Knowledge should be shared.  ",
        bond="  The old academy archive.  ",
        flaw="  Overthinks simple choices.  ",
        character_notes="  Keeps backup scrolls in hidden sleeve.  ",
        alignment="Neutral Good",
        ability_scores={"STR": 9, "DEX": 18, "CON": 14, "INT": 16, "WIS": 11, "CHA": 10},
        skill_proficiencies={"Athletics": True, "Arcana": True, "Perception": False, "Acrobatics": False},
        languages="Common, Elvish",
        starting_gold=42,
        inventory_text="Rope\nTorch",
        prepared_spells_text="Mage Armor\nShield",
    )

    assert "Character Snapshot:" in overview
    assert "Class/Level: Wizard 5" in overview
    assert "Personality: Trait=Keeps a travel journal. | Ideal=Knowledge should be shared. | Bond=The old academy archive. | Flaw=Overthinks simple choices." in overview
    assert "Notes: Keeps backup scrolls in hidden sleeve." in overview
    assert "Prepared Spells Count: 2" in overview
    assert "Equipment: 42 gp; 2 item(s): Rope, Torch" in overview


def test_summary_sections_align_with_deserialized_builder_state_fields():
    payload = {
        "builder": {
            "class_name": "Wizard",
            "level": "5",
            "look_ahead": 1,
            "ability_scores": {"STR": "9", "DEX": "18", "CON": "14", "INT": "16", "WIS": "11", "CHA": None},
            "skill_proficiencies": {"Athletics": 1, "Arcana": "yes", "Perception": "", "Acrobatics": 0},
            "character_name": "  Elora  ",
            "race_species": "  Elf  ",
            "background": " Sage ",
            "character_notes": "  Plans routes before dawn.  ",
            "alignment": "Neutral Good",
            "languages": " Common, Elvish, Common ",
            "starting_gold": "42",
            "inventory_text": "  Rope\n\n Torch  ",
            "prepared_spells_text": " Mage Armor\n\nShield\nMage Armor ",
        }
    }

    state = deserialize_builder_state(payload, available_classes=["Cleric", "Fighter", "Wizard"])
    snap = build_level_snapshot(state.class_name, state.level, look_ahead=state.look_ahead)

    builder = format_builder_summary(
        snap,
        look_ahead=state.look_ahead,
        character_name=state.character_name,
        race_species=state.race_species,
        background=state.background,
        character_notes=state.character_notes,
        alignment=state.alignment,
        ability_scores=state.ability_scores,
        skill_proficiencies=state.skill_proficiencies,
        languages=state.languages,
        starting_gold=state.starting_gold,
        inventory_text=state.inventory_text,
        prepared_spells_text=state.prepared_spells_text,
    )
    stats = format_stats_summary(snap, state.ability_scores)
    skills = format_skills_languages_summary(snap, state.skill_proficiencies, state.languages)
    equipment = format_equipment_summary(snap, state.starting_gold, state.inventory_text)
    spells = format_spells_summary(snap, state.prepared_spells_text)

    assert "Class: Wizard" in builder
    assert "Level: 5" in builder
    assert "Look Ahead: On" in builder
    assert "Identity:" in builder
    assert "Name: Elora" in builder
    assert "Race/Species: Elf" in builder
    assert "Background: Sage" in builder
    assert "Trait: None" in builder
    assert "Ideal: None" in builder
    assert "Bond: None" in builder
    assert "Flaw: None" in builder
    assert "Character Notes: Plans routes before dawn." in builder
    assert "Alignment: Neutral Good" in builder
    assert "Spell save DC / spell attack: 14 / +6 (INT)" in builder
    assert "Character Snapshot:" in builder
    assert "Class/Level: Wizard 5" in builder
    assert "Skills: Arcana, Athletics (2/4)" in builder
    assert "Languages: Common, Elvish" in builder
    assert "Equipment: 42 gp; 2 item(s): Rope, Torch" in builder
    assert "Prepared Spells Count: 2" in builder

    assert "- STR: 9 (-1)" in stats
    assert "- DEX: 18 (+4)" in stats
    assert "- INT: 16 (+3)" in stats
    assert "Current class: Wizard" in stats
    assert "Current level: 5" in stats

    assert "Skill proficiencies: Arcana, Athletics" in skills
    assert "Languages: Common, Elvish" in skills
    assert "Build context: Wizard level 5" in skills

    assert "Starting gold: 42 gp" in equipment
    assert "- Rope" in equipment
    assert "- Torch" in equipment
    assert "Build context: Wizard level 5" in equipment

    assert "Spellcasting ability: INT" in spells
    assert "- Mage Armor" in spells
    assert "- Shield" in spells
    assert spells.count("Mage Armor") == 1
    assert "Build context: Wizard level 5" in spells
