"""Pure-Python PDF export for printable character sheets."""

from __future__ import annotations

import textwrap
from pathlib import Path

from .calculations import format_bonus
from .models import ABILITIES, Character

PAGE_WIDTH = 612
PAGE_HEIGHT = 792
MARGIN = 36
CONTENT_WIDTH = PAGE_WIDTH - (MARGIN * 2)


def _pdf_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _build_sections(character: Character) -> list[tuple[str, list[str]]]:
    identity = [
        f"Name: {character.name}",
        f"Level: {character.level}    Alignment: {character.alignment}",
        f"Species: {character.species}    Class: {character.char_class}",
        f"Background: {character.background}",
        f"Size: {character.size}    Speed: {character.speed} ft    Proficiency: {format_bonus(character.proficiency_bonus)}",
    ]

    combat = [
        f"HP: {character.max_hp}",
        f"AC: {character.ac_baseline}",
        f"Initiative: {format_bonus(character.initiative)}",
        f"Passive Perception: {character.passive_perception}",
    ]

    abilities = [
        f"{a}: {character.final_ability_scores[a]} ({format_bonus(character.ability_modifiers[a])})"
        + (" [Save Prof]" if a in character.saving_throw_proficiencies else "")
        for a in ABILITIES
    ]

    profs = [
        f"Saving Throw Proficiencies: {', '.join(character.saving_throw_proficiencies) or 'None'}",
        f"Skill Proficiencies: {', '.join(character.skill_proficiencies) or 'None'}",
        f"Languages: {', '.join(character.languages) or 'None'}",
    ]

    gear = [
        f"Equipment: {', '.join(character.equipment) or 'None'}",
        f"Attack Placeholders: {', '.join(character.attacks) or 'None'}",
    ]

    if character.spellcasting_ability:
        spells = [
            f"Spellcasting Ability: {character.spellcasting_ability}",
            f"Spell Save DC: {character.spell_save_dc}",
            f"Spell Attack Bonus: {format_bonus(character.spell_attack_bonus or 0)}",
            f"Cantrips: {', '.join(character.known_spells.get('0', [])) or 'None'}",
            f"Level 1 Spells: {', '.join(character.known_spells.get('1', [])) or 'None'}",
        ]
    else:
        spells = ["No class spellcasting at level 1."]

    sections: list[tuple[str, list[str]]] = [
        ("Character Identity", identity),
        ("Combat Stats", combat),
        ("Ability Scores", abilities),
        ("Proficiencies", profs),
        ("Equipment and Attacks", gear),
        ("Spellcasting", spells),
    ]

    if character.notes:
        sections.append(("Notes", [character.notes]))

    return sections


def _wrap_line(line: str, width: int = 92) -> list[str]:
    wrapped = textwrap.wrap(line, width=width, break_long_words=False, replace_whitespace=False)
    return wrapped or [""]


def _build_pages(sections: list[tuple[str, list[str]]]) -> list[bytes]:
    pages: list[bytes] = []
    ops: list[str] = []
    y_cursor = PAGE_HEIGHT - MARGIN

    title = "D&D Character Creator V2 - Level 1 Character Sheet"
    ops.extend(
        [
            "BT",
            "/F2 14 Tf",
            f"1 0 0 1 {MARGIN} {y_cursor} Tm ({_pdf_escape(title)}) Tj",
            "ET",
        ]
    )
    y_cursor -= 26

    def flush_page() -> None:
        nonlocal ops, y_cursor
        pages.append("\n".join(ops).encode("latin-1", errors="replace"))
        ops = []
        y_cursor = PAGE_HEIGHT - MARGIN
        ops.extend(
            [
                "BT",
                "/F2 12 Tf",
                f"1 0 0 1 {MARGIN} {y_cursor} Tm ({_pdf_escape('Character Sheet (continued)')}) Tj",
                "ET",
            ]
        )
        y_cursor -= 22

    for section_title, section_lines in sections:
        wrapped_lines: list[str] = []
        for raw in section_lines:
            wrapped_lines.extend(_wrap_line(raw))

        line_height = 12
        box_padding = 8
        title_height = 18
        box_height = title_height + box_padding + (len(wrapped_lines) * line_height) + 8

        if y_cursor - box_height < MARGIN:
            flush_page()

        box_x = MARGIN
        box_y = y_cursor - box_height
        ops.append(f"{box_x} {box_y} {CONTENT_WIDTH} {box_height} re S")

        ops.extend(
            [
                "BT",
                "/F2 11 Tf",
                f"1 0 0 1 {box_x + 8} {y_cursor - 14} Tm ({_pdf_escape(section_title)}) Tj",
                "ET",
            ]
        )

        text_y = y_cursor - 30
        for line in wrapped_lines:
            ops.extend(
                [
                    "BT",
                    "/F1 10 Tf",
                    f"1 0 0 1 {box_x + 10} {text_y} Tm ({_pdf_escape(line)}) Tj",
                    "ET",
                ]
            )
            text_y -= line_height

        y_cursor = box_y - 10

    pages.append("\n".join(ops).encode("latin-1", errors="replace"))
    return pages


def _write_pdf(path: Path, page_streams: list[bytes]) -> None:
    objects: list[bytes] = []
    font_regular_obj_num = 3
    font_bold_obj_num = 4

    # 1 catalog, 2 pages tree, then fonts, then per-page objects (page + content)
    objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    objects.append(b"<< /Type /Pages /Kids [] /Count 0 >>")
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>")

    kids_refs: list[str] = []
    for stream in page_streams:
        page_obj_num = len(objects) + 1
        content_obj_num = len(objects) + 2
        kids_refs.append(f"{page_obj_num} 0 R")

        page_obj = (
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {PAGE_WIDTH} {PAGE_HEIGHT}] "
            f"/Resources << /Font << /F1 {font_regular_obj_num} 0 R /F2 {font_bold_obj_num} 0 R >> >> "
            f"/Contents {content_obj_num} 0 R >>"
        ).encode("latin-1")
        content_obj = f"<< /Length {len(stream)} >>\nstream\n".encode("latin-1") + stream + b"\nendstream"

        objects.append(page_obj)
        objects.append(content_obj)

    pages_obj = f"<< /Type /Pages /Kids [{' '.join(kids_refs)}] /Count {len(page_streams)} >>".encode("latin-1")
    objects[1] = pages_obj

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as f:
        f.write(b"%PDF-1.4\n")
        offsets = [0]
        for i, obj in enumerate(objects, start=1):
            offsets.append(f.tell())
            f.write(f"{i} 0 obj\n".encode("latin-1"))
            f.write(obj)
            f.write(b"\nendobj\n")

        xref_start = f.tell()
        f.write(f"xref\n0 {len(objects) + 1}\n".encode("latin-1"))
        f.write(b"0000000000 65535 f \n")
        for offset in offsets[1:]:
            f.write(f"{offset:010d} 00000 n \n".encode("latin-1"))

        trailer = f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_start}\n%%EOF\n"
        f.write(trailer.encode("latin-1"))


def export_character_pdf(character: Character, output_path: str) -> None:
    sections = _build_sections(character)
    pages = _build_pages(sections)
    _write_pdf(Path(output_path), pages)
