"""Generate the required sample character PDF for testing."""

from character_creator.cli import build_sample_character
from character_creator.pdf_export import export_character_pdf


def main() -> None:
    export_character_pdf(build_sample_character(), "outputs/sample_character.pdf")
    print("Generated outputs/sample_character.pdf")


if __name__ == "__main__":
    main()
