from __future__ import annotations

from .persistence import compute_ability_modifiers, normalize_ability_scores, normalize_skill_proficiencies


def build_derived_combat_summary(
    *,
    ability_scores: dict[str, int] | None,
    skill_proficiencies: dict[str, bool] | None,
    proficiency_bonus: int,
) -> str:
    """Return deterministic one-line derived combat summary from normalized state."""

    normalized_abilities = normalize_ability_scores(ability_scores or {})
    modifiers = compute_ability_modifiers(normalized_abilities)
    normalized_skills = normalize_skill_proficiencies(skill_proficiencies or {})

    initiative = modifiers["DEX"]
    passive_perception = 10 + modifiers["WIS"] + (
        proficiency_bonus if normalized_skills.get("Perception", False) else 0
    )

    best_attack_mod = max(modifiers["STR"], modifiers["DEX"])
    baseline_to_hit = proficiency_bonus + best_attack_mod

    return (
        "Initiative "
        f"{initiative:+d} | "
        f"Passive Perception {passive_perception} | "
        f"Attack Baseline +{baseline_to_hit} to hit, {best_attack_mod:+d} damage mod (best STR/DEX)"
    )
