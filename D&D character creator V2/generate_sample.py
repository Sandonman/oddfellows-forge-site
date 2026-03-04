#!/usr/bin/env python3
"""Generate sample character JSON and PDF in outputs/."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ddcc_v2.pdf_export import export_character_pdf  # noqa: E402
from ddcc_v2.persistence import save_character  # noqa: E402
from ddcc_v2.sample_builder import build_sample_character  # noqa: E402


def main() -> None:
    output_dir = ROOT / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)

    sample = build_sample_character()
    json_path = output_dir / "sample_character.json"
    pdf_path = output_dir / "sample_character.pdf"

    save_character(sample, str(json_path))
    export_character_pdf(sample, str(pdf_path))

    print(f"Wrote {json_path}")
    print(f"Wrote {pdf_path}")


if __name__ == "__main__":
    main()
