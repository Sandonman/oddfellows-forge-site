"""CLI for D&D Character Creator V1."""

import argparse
from pathlib import Path

from .data import ABILITIES, BACKGROUNDS, CLASSES, SPECIES
from .models import Character, apply_ability_bonuses
from .pdf_export import export_character_pdf


STANDARD_ARRAY = [15, 14, 13, 12, 10, 8]


def _prompt_choice(label: str, options: list[str]) -> str:
    print(f"\nChoose {label}:")
    for idx, option in enumerate(options, start=1):
        print(f"  {idx}. {option}")

    while True:
        raw = input(f"Enter number (1-{len(options)}): ").strip()
        if raw.isdigit() and 1 <= int(raw) <= len(options):
            return options[int(raw) - 1]
        print("Invalid selection. Try again.")


def _prompt_level() -> int:
    raw = input("Level [1]: ").strip() or "1"
    if raw.isdigit() and int(raw) > 0:
        return int(raw)
    print("Invalid level, using 1.")
    return 1


def _prompt_ability_scores() -> dict[str, int]:
    print("\nAbility score mode:")
    print("  1. Standard array assignment (15,14,13,12,10,8)")
    print("  2. Manual input")
    mode = input("Choose mode [1]: ").strip() or "1"

    if mode == "2":
        scores = {}
        for ability in ABILITIES:
            raw = input(f"{ability} [10]: ").strip() or "10"
            try:
                value = max(3, min(18, int(raw)))
            except ValueError:
                value = 10
            scores[ability] = value
        return scores

    remaining = STANDARD_ARRAY[:]
    scores = {}
    for ability in ABILITIES:
        while True:
            print(f"Remaining values: {remaining}")
            raw = input(f"Pick value for {ability}: ").strip()
            if raw.isdigit() and int(raw) in remaining:
                value = int(raw)
                remaining.remove(value)
                scores[ability] = value
                break
            print("Pick one of the remaining values.")
    return scores


def _pick_class_skills(class_name: str, existing: list[str], scripted: bool = False) -> list[str]:
    class_info = CLASSES[class_name]
    choices = [s for s in class_info["skill_choices"] if s not in existing]
    num_to_pick = min(class_info["num_skill_choices"], len(choices))

    if scripted:
        return choices[:num_to_pick]

    picked: list[str] = []
    print(f"\nChoose {num_to_pick} class skills:")
    while len(picked) < num_to_pick:
        available = [s for s in choices if s not in picked]
        skill = _prompt_choice(f"skill {len(picked)+1}", available)
        picked.append(skill)
    return picked


def build_character_interactive() -> Character:
    print("D&D Character Creator V1")
    print("(SRD 5.2.1-inspired simplified data)\n")

    name = input("Character name: ").strip() or "Unnamed Hero"
    level = _prompt_level()
    species = _prompt_choice("species", sorted(SPECIES.keys()))
    char_class = _prompt_choice("class", sorted(CLASSES.keys()))
    background = _prompt_choice("background", sorted(BACKGROUNDS.keys()))

    base_scores = _prompt_ability_scores()
    final_scores = apply_ability_bonuses(base_scores, SPECIES[species]["ability_bonuses"])

    background_skills = BACKGROUNDS[background]["skill_proficiencies"]
    class_skills = _pick_class_skills(char_class, background_skills)

    return Character(
        name=name,
        level=level,
        species=species,
        char_class=char_class,
        background=background,
        ability_scores=final_scores,
        saving_throw_proficiencies=CLASSES[char_class]["saving_throws"],
        skill_proficiencies=sorted(set(background_skills + class_skills)),
    )


def build_sample_character() -> Character:
    species = "Human"
    char_class = "Fighter"
    background = "Soldier"
    base_scores = {
        "STR": 15,
        "DEX": 13,
        "CON": 14,
        "INT": 10,
        "WIS": 12,
        "CHA": 8,
    }
    final_scores = apply_ability_bonuses(base_scores, SPECIES[species]["ability_bonuses"])

    background_skills = BACKGROUNDS[background]["skill_proficiencies"]
    class_skills = _pick_class_skills(char_class, background_skills, scripted=True)

    return Character(
        name="Aric Stone",
        level=1,
        species=species,
        char_class=char_class,
        background=background,
        ability_scores=final_scores,
        saving_throw_proficiencies=CLASSES[char_class]["saving_throws"],
        skill_proficiencies=sorted(set(background_skills + class_skills)),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="D&D Character Creator V1")
    parser.add_argument("--sample", action="store_true", help="Generate sample character PDF")
    parser.add_argument(
        "--output",
        default=None,
        help="Output PDF path (default: outputs/character.pdf)",
    )
    args = parser.parse_args()

    if args.sample:
        character = build_sample_character()
        output = args.output or "outputs/sample_character.pdf"
    else:
        character = build_character_interactive()
        output = args.output or "outputs/character.pdf"

    export_character_pdf(character, output)
    print(f"\nPDF exported to: {Path(output).resolve()}")


if __name__ == "__main__":
    main()
