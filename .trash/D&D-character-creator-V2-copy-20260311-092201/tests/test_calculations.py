from ddcc_v2.calculations import (
    ability_modifier,
    calculate_armor_class,
    calculate_max_hp,
    calculate_passive_perception,
    calculate_spell_attack_bonus,
    calculate_spell_save_dc,
    proficiency_bonus,
)


def test_ability_modifier_values():
    assert ability_modifier(8) == -1
    assert ability_modifier(10) == 0
    assert ability_modifier(15) == 2


def test_proficiency_bonus_level_1():
    assert proficiency_bonus(1) == 2


def test_hp_level_1_uses_hit_die_plus_con():
    assert calculate_max_hp(1, 8, 2) == 10
    assert calculate_max_hp(1, 6, -2) == 4


def test_ac_by_armor_type():
    assert calculate_armor_class(3, None) == 13
    assert calculate_armor_class(3, {"ac": 11, "type": "light"}) == 14
    assert calculate_armor_class(3, {"ac": 14, "type": "medium"}) == 16
    assert calculate_armor_class(3, {"ac": 16, "type": "heavy"}) == 16


def test_spell_stats_and_passive_perception():
    assert calculate_spell_save_dc(2, 3) == 13
    assert calculate_spell_attack_bonus(2, 3) == 5
    assert calculate_passive_perception(4) == 14
