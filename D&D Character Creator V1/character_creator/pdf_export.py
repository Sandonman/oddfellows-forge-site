"""Minimal PDF export without external dependencies."""

from pathlib import Path

from .data import ABILITIES, SKILLS
from .models import Character, ability_modifier, format_bonus, proficiency_bonus


def _pdf_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _build_pdf_text(lines: list[str]) -> str:
    y_start = 780
    line_height = 16
    chunks = ["BT", "/F1 12 Tf"]
    for i, line in enumerate(lines):
        y = y_start - (i * line_height)
        chunks.append(f"1 0 0 1 50 {y} Tm ({_pdf_escape(line)}) Tj")
    chunks.append("ET")
    return "\n".join(chunks)


def _write_single_page_pdf(path: Path, lines: list[str]) -> None:
    content_stream = _build_pdf_text(lines).encode("latin-1", errors="replace")

    objects: list[bytes] = []
    objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    objects.append(b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>")
    objects.append(b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>")
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    objects.append(f"<< /Length {len(content_stream)} >>\nstream\n".encode("latin-1") + content_stream + b"\nendstream")

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
    prof_bonus = proficiency_bonus(character.level)
    lines: list[str] = [
        "D&D Character Creator V1 Sheet",
        "",
        f"Name: {character.name}",
        f"Level: {character.level}",
        f"Species: {character.species}",
        f"Class: {character.char_class}",
        f"Background: {character.background}",
        "",
        f"Proficiency Bonus: {format_bonus(prof_bonus)}",
        "",
        "Ability Scores",
    ]

    for ability in ABILITIES:
        score = character.ability_scores[ability]
        lines.append(f"- {ability}: {score} ({format_bonus(ability_modifier(score))})")

    lines.extend(
        [
            "",
            "Saving Throw Proficiencies",
            f"- {', '.join(character.saving_throw_proficiencies)}",
            "",
            "Skill Proficiencies",
            f"- {', '.join(character.skill_proficiencies)}",
            "",
            "All Skills",
        ]
    )

    skill_set = set(character.skill_proficiencies)
    save_set = set(character.saving_throw_proficiencies)

    for skill, ability in SKILLS.items():
        mod = ability_modifier(character.ability_scores[ability])
        total = mod + (prof_bonus if skill in skill_set else 0)
        marker = "*" if skill in skill_set else " "
        lines.append(f"{marker} {skill} ({ability}) {format_bonus(total)}")

    lines.extend(
        [
            "",
            "Saving Throws",
        ]
    )
    for ability in ABILITIES:
        mod = ability_modifier(character.ability_scores[ability])
        total = mod + (prof_bonus if ability in save_set else 0)
        marker = "*" if ability in save_set else " "
        lines.append(f"{marker} {ability} {format_bonus(total)}")

    _write_single_page_pdf(Path(output_path), lines)
