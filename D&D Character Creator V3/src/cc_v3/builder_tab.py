from __future__ import annotations

from typing import Any, Callable

from .derived_combat import build_derived_combat_summary
from .leveling import MAX_LEVEL, LevelSnapshot, build_level_snapshot, load_classes
from .persistence import (
    ABILITY_NAMES,
    ALIGNMENT_OPTIONS,
    CORE_SKILLS,
    BuilderState,
    DEFAULT_ABILITY_SCORE,
    MAX_ABILITY_SCORE,
    MIN_ABILITY_SCORE,
    compute_ability_modifiers,
    concise_equipment_line,
    concise_notes_line,
    concise_trait_line,
    deserialize_builder_state,
    normalize_ability_scores,
    normalize_alignment,
    normalize_character_notes_text,
    normalize_identity_text,
    normalize_inventory_text,
    normalize_languages_text,
    normalize_prepared_spells_list,
    normalize_prepared_spells_text,
    normalize_skill_proficiencies,
    normalize_starting_gold,
    normalize_trait_text,
    serialize_builder_state,
)

try:
    import tkinter as tk
    from tkinter import ttk

    TK_AVAILABLE = True
except ModuleNotFoundError:  # pragma: no cover - depends on runtime image
    tk = None  # type: ignore[assignment]
    ttk = None  # type: ignore[assignment]
    TK_AVAILABLE = False


def _estimate_hp_baseline(level: int, con_modifier: int) -> int:
    # Deterministic baseline for now: 8 HP at level 1 + 5 HP per additional level + CON mod per level.
    return max(1, 8 + (max(1, level) - 1) * 5 + con_modifier * max(1, level))


def format_derived_stats_summary(
    snapshot: LevelSnapshot,
    ability_scores: dict[str, int] | None,
    skill_proficiencies: dict[str, bool] | None,
) -> list[str]:
    abilities = normalize_ability_scores(ability_scores or {})
    modifiers = compute_ability_modifiers(abilities)
    skills = normalize_skill_proficiencies(skill_proficiencies or {})

    hp_baseline = _estimate_hp_baseline(snapshot.level, modifiers["CON"])
    passive_perception = 10 + modifiers["WIS"] + (
        snapshot.proficiency_bonus if skills.get("Perception", False) else 0
    )

    derived_combat_summary = build_derived_combat_summary(
        ability_scores=abilities,
        skill_proficiencies=skills,
        proficiency_bonus=snapshot.proficiency_bonus,
    )

    lines = [
        "Derived stats:",
        f"- HP baseline estimate: {hp_baseline} (rule: 8 + 5×(level-1) + CON mod×level)",
        f"- Passive Perception: {passive_perception}",
        f"- Derived Combat: {derived_combat_summary}",
    ]

    if snapshot.spellcasting:
        spellcasting_ability = None
        if isinstance(snapshot.spellcasting, dict):
            raw_ability = snapshot.spellcasting.get("spellcasting_ability")
            if isinstance(raw_ability, str) and raw_ability in ABILITY_NAMES:
                spellcasting_ability = raw_ability

        if spellcasting_ability:
            spell_mod = modifiers[spellcasting_ability]
            lines.append(
                f"- Spell save DC / spell attack: {8 + snapshot.proficiency_bonus + spell_mod} / {snapshot.proficiency_bonus + spell_mod:+d} ({spellcasting_ability})"
            )
        else:
            lines.append(
                "- Spell save DC / spell attack: fallback to INT (class spellcasting ability missing)",
            )

    return lines


def generate_builder_validation_messages(
    *,
    class_name: str,
    level_input: Any,
    normalized_level: int,
    character_name: str,
    ability_scores: dict[str, Any] | None,
) -> list[str]:
    messages: list[str] = []

    if not normalize_identity_text(character_name):
        messages.append("missing name")

    if not normalize_identity_text(class_name):
        messages.append("no class selected")

    level_in_range = True
    try:
        parsed_level = int(level_input)
    except (TypeError, ValueError):
        level_in_range = False
    else:
        level_in_range = 1 <= parsed_level <= MAX_LEVEL

    if not level_in_range:
        messages.append(f"level adjusted to {normalized_level} (valid range 1-{MAX_LEVEL})")

    if not isinstance(ability_scores, dict) or not ability_scores:
        messages.append("ability scores using default set")

    return messages


def format_builder_validation_summary(messages: list[str]) -> str:
    if not messages:
        return "Validation: OK"
    return "Validation: " + "; ".join(messages)


def _concise_trait_summary(value: str, *, max_len: int = 40) -> str:
    return concise_trait_line(value, max_len=max_len)


def _concise_notes_summary(value: str, *, max_len: int = 60) -> str:
    return concise_notes_line(value, max_len=max_len)


def format_character_snapshot(
    snapshot: LevelSnapshot,
    *,
    character_name: str = "",
    race_species: str = "",
    background: str = "",
    trait: str = "",
    ideal: str = "",
    bond: str = "",
    flaw: str = "",
    character_notes: str = "",
    alignment: str = "",
    ability_scores: dict[str, int] | None = None,
    skill_proficiencies: dict[str, bool] | None = None,
    languages: str = "",
    starting_gold: int = 0,
    inventory_text: str = "",
    prepared_spells_text: str = "",
) -> str:
    normalized_name = normalize_identity_text(character_name)
    normalized_race_species = normalize_identity_text(race_species)
    normalized_background = normalize_identity_text(background)
    normalized_trait = _concise_trait_summary(trait)
    normalized_ideal = _concise_trait_summary(ideal)
    normalized_bond = _concise_trait_summary(bond)
    normalized_flaw = _concise_trait_summary(flaw)
    normalized_notes = _concise_notes_summary(character_notes)
    normalized_alignment = normalize_alignment(alignment)
    normalized_abilities = normalize_ability_scores(ability_scores or {})
    normalized_modifiers = compute_ability_modifiers(normalized_abilities)
    normalized_skills = normalize_skill_proficiencies(skill_proficiencies or {})
    selected_skills = [skill for skill in CORE_SKILLS if normalized_skills[skill]]
    normalized_languages = normalize_languages_text(languages)
    equipment_summary = concise_equipment_line(starting_gold, inventory_text)
    prepared_spells = normalize_prepared_spells_list(prepared_spells_text)

    ability_summary = ", ".join(
        f"{ability} {normalized_abilities[ability]} ({normalized_modifiers[ability]:+d})"
        for ability in ABILITY_NAMES
    )
    skills_list = ", ".join(selected_skills) if selected_skills else "None"
    skills_summary = f"{skills_list} ({len(selected_skills)}/{len(CORE_SKILLS)})"
    languages_summary = normalized_languages or "None"

    derived_combat_summary = build_derived_combat_summary(
        ability_scores=normalized_abilities,
        skill_proficiencies=normalized_skills,
        proficiency_bonus=snapshot.proficiency_bonus,
    )

    return "\n".join(
        [
            "Character Snapshot:",
            f"Identity: {normalized_name or 'Unnamed'} | {normalized_race_species or 'Unspecified'} | {normalized_background or 'Unspecified'} | {normalized_alignment or 'Unspecified'}",
            f"Class/Level: {snapshot.class_name} {snapshot.level}",
            f"Personality: Trait={normalized_trait} | Ideal={normalized_ideal} | Bond={normalized_bond} | Flaw={normalized_flaw}",
            f"Notes: {normalized_notes}",
            f"Ability Scores: {ability_summary}",
            f"Derived Combat: {derived_combat_summary}",
            f"Skills: {skills_summary}",
            f"Languages: {languages_summary}",
            f"Equipment: {equipment_summary}",
            f"Prepared Spells Count: {len(prepared_spells)}",
        ]
    )


def format_builder_summary(
    snapshot: LevelSnapshot,
    *,
    look_ahead: bool,
    character_name: str = "",
    race_species: str = "",
    background: str = "",
    trait: str = "",
    ideal: str = "",
    bond: str = "",
    flaw: str = "",
    character_notes: str = "",
    alignment: str = "",
    ability_scores: dict[str, int] | None = None,
    skill_proficiencies: dict[str, bool] | None = None,
    languages: str = "",
    starting_gold: int = 0,
    inventory_text: str = "",
    prepared_spells_text: str = "",
    level_input: Any | None = None,
) -> str:
    gained = snapshot.gained_features or ["None"]
    visible = snapshot.visible_features or ["None"]
    normalized_name = normalize_identity_text(character_name)
    normalized_race_species = normalize_identity_text(race_species)
    normalized_background = normalize_identity_text(background)
    normalized_trait = _concise_trait_summary(trait)
    normalized_ideal = _concise_trait_summary(ideal)
    normalized_bond = _concise_trait_summary(bond)
    normalized_flaw = _concise_trait_summary(flaw)
    normalized_notes = _concise_notes_summary(character_notes)
    normalized_alignment = normalize_alignment(alignment)

    validation_messages = generate_builder_validation_messages(
        class_name=snapshot.class_name,
        level_input=snapshot.level if level_input is None else level_input,
        normalized_level=snapshot.level,
        character_name=character_name,
        ability_scores=ability_scores,
    )

    lines = [
        f"Class: {snapshot.class_name}",
        f"Level: {snapshot.level}",
        f"Proficiency Bonus: +{snapshot.proficiency_bonus}",
        f"Look Ahead: {'On' if look_ahead else 'Off'}",
        format_builder_validation_summary(validation_messages),
        "",
        "Identity:",
        f"- Name: {normalized_name or 'Unnamed'}",
        f"- Race/Species: {normalized_race_species or 'Unspecified'}",
        f"- Background: {normalized_background or 'Unspecified'}",
        f"- Trait: {normalized_trait}",
        f"- Ideal: {normalized_ideal}",
        f"- Bond: {normalized_bond}",
        f"- Flaw: {normalized_flaw}",
        f"- Character Notes: {normalized_notes}",
        f"- Alignment: {normalized_alignment or 'Unspecified'}",
        "",
        format_character_snapshot(
            snapshot,
            character_name=character_name,
            race_species=race_species,
            background=background,
            trait=trait,
            ideal=ideal,
            bond=bond,
            flaw=flaw,
            character_notes=character_notes,
            alignment=alignment,
            ability_scores=ability_scores,
            skill_proficiencies=skill_proficiencies,
            languages=languages,
            starting_gold=starting_gold,
            inventory_text=inventory_text,
            prepared_spells_text=prepared_spells_text,
        ),
        "",
        *format_derived_stats_summary(snapshot, ability_scores, skill_proficiencies),
        "",
        "Gained at this level:",
        *(f"- {item}" for item in gained),
        "",
        "Visible features:",
        *(f"- {item}" for item in visible),
    ]

    if snapshot.spellcasting:
        lines.extend([
            "",
            "Spellcasting:",
            f"- {snapshot.spellcasting}",
        ])

    return "\n".join(lines)


def format_stats_summary(snapshot: LevelSnapshot, ability_scores: dict[str, int]) -> str:
    abilities = normalize_ability_scores(ability_scores)
    modifiers = compute_ability_modifiers(abilities)
    ability_lines = [
        f"- {name}: {abilities[name]} ({modifiers[name]:+d})"
        for name in ABILITY_NAMES
    ]
    return "\n".join(
        [
            "Stats",
            "- Editable ability scores (score and modifier):",
            *ability_lines,
            f"- Current class: {snapshot.class_name}",
            f"- Current level: {snapshot.level}",
            f"- Proficiency bonus: +{snapshot.proficiency_bonus}",
        ]
    )


def format_skills_languages_summary(
    snapshot: LevelSnapshot,
    skill_proficiencies: dict[str, bool],
    languages: str,
) -> str:
    normalized_skills = normalize_skill_proficiencies(skill_proficiencies)
    selected_skills = [skill for skill in CORE_SKILLS if normalized_skills[skill]]
    normalized_languages = normalize_languages_text(languages)

    return "\n".join(
        [
            "Skills & Languages",
            f"- Skill proficiencies: {', '.join(selected_skills) if selected_skills else 'None selected'}",
            f"- Languages: {normalized_languages or 'None entered'}",
            f"- Build context: {snapshot.class_name} level {snapshot.level}",
        ]
    )


def format_equipment_summary(snapshot: LevelSnapshot, starting_gold: int, inventory_text: str) -> str:
    normalized_gold = normalize_starting_gold(starting_gold)
    normalized_inventory = normalize_inventory_text(inventory_text)
    inventory_lines = normalized_inventory.splitlines()
    inventory_entries = [f"  - {item}" for item in inventory_lines] or ["  - None entered"]

    return "\n".join(
        [
            "Equipment",
            f"- Starting gold: {normalized_gold} gp",
            "- Inventory:",
            *inventory_entries,
            f"- Build context: {snapshot.class_name} level {snapshot.level}",
        ]
    )


def format_spells_summary(snapshot: LevelSnapshot, prepared_spells_text: str) -> str:
    spellcasting = snapshot.spellcasting
    if isinstance(spellcasting, dict):
        spellcasting_ability = spellcasting.get("spellcasting_ability") or "Unknown"
        caster_type = spellcasting.get("caster_type") or "Unknown"
        spellcasting_status = f"{caster_type} caster ({spellcasting_ability})"
    else:
        spellcasting_ability = "None"
        spellcasting_status = "No spellcasting progression for this class/level"

    prepared_spells = normalize_prepared_spells_list(prepared_spells_text)
    prepared_lines = [f"  - {spell}" for spell in prepared_spells] or ["  - None entered"]

    return "\n".join(
        [
            "Spells",
            f"- Spellcasting ability: {spellcasting_ability}",
            f"- Spellcasting status: {spellcasting_status}",
            "- Prepared spells:",
            *prepared_lines,
            f"- Build context: {snapshot.class_name} level {snapshot.level}",
        ]
    )


if TK_AVAILABLE:
    class BuilderTab(ttk.Frame):
        """Character builder panel with scaffolds for planned V3 builder sections."""

        def __init__(self, parent: tk.Misc, on_state_change: Callable[[dict[str, Any]], None] | None = None):
            super().__init__(parent, padding=8)
            self._classes_index = load_classes()
            self._on_state_change = on_state_change
            self._suppress_change_events = True
            class_names = sorted(self._classes_index.keys())

            default_class = class_names[0] if class_names else ""
            self._class_name = tk.StringVar(value=default_class)
            self._level = tk.IntVar(value=1)
            self._look_ahead = tk.BooleanVar(value=False)
            self._ability_scores: dict[str, tk.IntVar] = {
                ability: tk.IntVar(value=DEFAULT_ABILITY_SCORE) for ability in ABILITY_NAMES
            }
            self._skill_proficiencies: dict[str, tk.BooleanVar] = {
                skill: tk.BooleanVar(value=False) for skill in CORE_SKILLS
            }
            self._character_name = tk.StringVar(value="")
            self._race_species = tk.StringVar(value="")
            self._background = tk.StringVar(value="")
            self._trait = tk.StringVar(value="")
            self._ideal = tk.StringVar(value="")
            self._bond = tk.StringVar(value="")
            self._flaw = tk.StringVar(value="")
            self._character_notes = tk.StringVar(value="")
            self._alignment = tk.StringVar(value="")
            self._languages = tk.StringVar(value="")
            self._starting_gold = tk.IntVar(value=0)
            self._spellcasting_ability = tk.StringVar(value="None")

            self.builder_notebook = ttk.Notebook(self)
            self.builder_notebook.pack(fill=tk.BOTH, expand=True)

            self.overview_tab = ttk.Frame(self.builder_notebook, padding=8)
            self.stats_tab = ttk.Frame(self.builder_notebook, padding=8)
            self.skills_languages_tab = ttk.Frame(self.builder_notebook, padding=8)
            self.equipment_tab = ttk.Frame(self.builder_notebook, padding=8)
            self.spells_tab = ttk.Frame(self.builder_notebook, padding=8)

            self.builder_notebook.add(self.overview_tab, text="Overview")
            self.builder_notebook.add(self.stats_tab, text="Stats")
            self.builder_notebook.add(self.skills_languages_tab, text="Skills & Languages")
            self.builder_notebook.add(self.equipment_tab, text="Equipment")
            self.builder_notebook.add(self.spells_tab, text="Spells")

            controls = ttk.Frame(self.overview_tab)
            controls.pack(fill=tk.X, pady=(0, 8))

            ttk.Label(controls, text="Class:").grid(row=0, column=0, sticky=tk.W)
            self.class_box = ttk.Combobox(
                controls,
                textvariable=self._class_name,
                values=class_names,
                state="readonly",
                width=18,
            )
            self.class_box.grid(row=0, column=1, sticky=tk.W, padx=(6, 12))

            ttk.Label(controls, text="Level:").grid(row=0, column=2, sticky=tk.W)
            self.level_spin = ttk.Spinbox(
                controls,
                from_=1,
                to=MAX_LEVEL,
                textvariable=self._level,
                width=5,
                command=self._refresh_summary,
            )
            self.level_spin.grid(row=0, column=3, sticky=tk.W, padx=(6, 12))

            self.look_ahead_check = ttk.Checkbutton(
                controls,
                text="Look Ahead",
                variable=self._look_ahead,
                command=self._refresh_summary,
            )
            self.look_ahead_check.grid(row=0, column=4, sticky=tk.W)

            ttk.Label(controls, text="Name:").grid(row=1, column=0, sticky=tk.W, pady=(6, 0))
            name_entry = ttk.Entry(controls, textvariable=self._character_name, width=22)
            name_entry.grid(row=1, column=1, sticky=tk.W, padx=(6, 12), pady=(6, 0))

            ttk.Label(controls, text="Race/Species:").grid(row=1, column=2, sticky=tk.W, pady=(6, 0))
            race_entry = ttk.Entry(controls, textvariable=self._race_species, width=18)
            race_entry.grid(row=1, column=3, sticky=tk.W, padx=(6, 12), pady=(6, 0))

            ttk.Label(controls, text="Background:").grid(row=2, column=0, sticky=tk.W, pady=(6, 0))
            background_entry = ttk.Entry(controls, textvariable=self._background, width=22)
            background_entry.grid(row=2, column=1, sticky=tk.W, padx=(6, 12), pady=(6, 0))

            ttk.Label(controls, text="Alignment:").grid(row=2, column=2, sticky=tk.W, pady=(6, 0))
            alignment_box = ttk.Combobox(
                controls,
                textvariable=self._alignment,
                values=("", *ALIGNMENT_OPTIONS),
                state="readonly",
                width=18,
            )
            alignment_box.grid(row=2, column=3, sticky=tk.W, padx=(6, 12), pady=(6, 0))

            personality_frame = ttk.LabelFrame(self.overview_tab, text="Personality Notes", padding=8)
            personality_frame.pack(fill=tk.X, pady=(0, 8))

            ttk.Label(personality_frame, text="Trait").grid(row=0, column=0, sticky=tk.W)
            ttk.Label(personality_frame, text="Ideal").grid(row=0, column=1, sticky=tk.W, padx=(8, 0))
            self.trait_text = tk.Text(personality_frame, wrap=tk.WORD, height=3, width=36)
            self.ideal_text = tk.Text(personality_frame, wrap=tk.WORD, height=3, width=36)
            self.trait_text.grid(row=1, column=0, sticky=tk.NSEW)
            self.ideal_text.grid(row=1, column=1, sticky=tk.NSEW, padx=(8, 0))

            ttk.Label(personality_frame, text="Bond").grid(row=2, column=0, sticky=tk.W, pady=(8, 0))
            ttk.Label(personality_frame, text="Flaw").grid(row=2, column=1, sticky=tk.W, padx=(8, 0), pady=(8, 0))
            self.bond_text = tk.Text(personality_frame, wrap=tk.WORD, height=3, width=36)
            self.flaw_text = tk.Text(personality_frame, wrap=tk.WORD, height=3, width=36)
            self.bond_text.grid(row=3, column=0, sticky=tk.NSEW, pady=(0, 2))
            self.flaw_text.grid(row=3, column=1, sticky=tk.NSEW, padx=(8, 0), pady=(0, 2))

            personality_frame.columnconfigure(0, weight=1)
            personality_frame.columnconfigure(1, weight=1)

            notes_frame = ttk.LabelFrame(self.overview_tab, text="Character Notes", padding=8)
            notes_frame.pack(fill=tk.X, pady=(0, 8))
            self.character_notes_text = tk.Text(notes_frame, wrap=tk.WORD, height=4)
            self.character_notes_text.pack(fill=tk.X)

            for widget in (self.trait_text, self.ideal_text, self.bond_text, self.flaw_text, self.character_notes_text):
                widget.bind("<FocusOut>", self._refresh_summary)
                widget.bind("<KeyRelease>", self._refresh_summary)

            name_entry.bind("<FocusOut>", self._refresh_summary)
            name_entry.bind("<Return>", self._refresh_summary)
            race_entry.bind("<FocusOut>", self._refresh_summary)
            race_entry.bind("<Return>", self._refresh_summary)
            background_entry.bind("<FocusOut>", self._refresh_summary)
            background_entry.bind("<Return>", self._refresh_summary)
            alignment_box.bind("<<ComboboxSelected>>", self._refresh_summary)

            self.summary = tk.Text(self.overview_tab, wrap=tk.WORD, state=tk.DISABLED, height=16)
            summary_scroll = ttk.Scrollbar(self.overview_tab, orient=tk.VERTICAL, command=self.summary.yview)
            self.summary.configure(yscrollcommand=summary_scroll.set)
            self.summary.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            summary_scroll.pack(side=tk.RIGHT, fill=tk.Y)

            self.stats_summary = tk.StringVar(value="")
            self.skills_languages_summary = tk.StringVar(value="")
            self.equipment_summary = tk.StringVar(value="")
            self.spells_summary = tk.StringVar(value="")

            stats_controls = ttk.LabelFrame(self.stats_tab, text="Ability Scores", padding=8)
            stats_controls.pack(fill=tk.X, pady=(0, 8))

            for idx, ability in enumerate(ABILITY_NAMES):
                row = idx // 3
                col = (idx % 3) * 2
                ttk.Label(stats_controls, text=f"{ability}:").grid(row=row, column=col, sticky=tk.W, padx=(0, 4), pady=2)
                spin = ttk.Spinbox(
                    stats_controls,
                    from_=MIN_ABILITY_SCORE,
                    to=MAX_ABILITY_SCORE,
                    textvariable=self._ability_scores[ability],
                    width=5,
                    command=self._refresh_summary,
                )
                spin.grid(row=row, column=col + 1, sticky=tk.W, padx=(0, 12), pady=2)
                spin.bind("<FocusOut>", self._refresh_summary)
                spin.bind("<Return>", self._refresh_summary)

            skills_controls = ttk.LabelFrame(self.skills_languages_tab, text="Skill Proficiencies", padding=8)
            skills_controls.pack(fill=tk.X, pady=(0, 8))
            for idx, skill in enumerate(CORE_SKILLS):
                row = idx // 2
                col = idx % 2
                ttk.Checkbutton(
                    skills_controls,
                    text=skill,
                    variable=self._skill_proficiencies[skill],
                    command=self._refresh_summary,
                ).grid(row=row, column=col, sticky=tk.W, padx=(0, 16), pady=2)

            language_controls = ttk.Frame(self.skills_languages_tab)
            language_controls.pack(fill=tk.X, pady=(0, 8))
            ttk.Label(language_controls, text="Languages (comma-separated):").grid(row=0, column=0, sticky=tk.W)
            language_entry = ttk.Entry(language_controls, textvariable=self._languages)
            language_entry.grid(row=1, column=0, sticky=tk.EW, pady=(4, 0))
            language_controls.columnconfigure(0, weight=1)
            language_entry.bind("<FocusOut>", self._refresh_summary)
            language_entry.bind("<Return>", self._refresh_summary)

            equipment_controls = ttk.LabelFrame(self.equipment_tab, text="Equipment", padding=8)
            equipment_controls.pack(fill=tk.BOTH, expand=False, pady=(0, 8))

            ttk.Label(equipment_controls, text="Starting Gold (gp):").grid(row=0, column=0, sticky=tk.W)
            starting_gold_spin = ttk.Spinbox(
                equipment_controls,
                from_=0,
                to=999999,
                textvariable=self._starting_gold,
                width=8,
                command=self._refresh_summary,
            )
            starting_gold_spin.grid(row=0, column=1, sticky=tk.W, padx=(6, 0), pady=(0, 8))
            starting_gold_spin.bind("<FocusOut>", self._refresh_summary)
            starting_gold_spin.bind("<Return>", self._refresh_summary)

            ttk.Label(equipment_controls, text="Inventory (one item per line):").grid(
                row=1,
                column=0,
                columnspan=2,
                sticky=tk.W,
            )
            self.inventory_text = tk.Text(equipment_controls, wrap=tk.WORD, height=8)
            self.inventory_text.grid(row=2, column=0, columnspan=2, sticky=tk.NSEW, pady=(4, 0))
            equipment_controls.columnconfigure(0, weight=1)
            equipment_controls.columnconfigure(1, weight=0)
            equipment_controls.rowconfigure(2, weight=1)
            self.inventory_text.bind("<FocusOut>", self._refresh_summary)
            self.inventory_text.bind("<KeyRelease>", self._refresh_summary)

            spells_controls = ttk.LabelFrame(self.spells_tab, text="Spells", padding=8)
            spells_controls.pack(fill=tk.BOTH, expand=False, pady=(0, 8))
            ttk.Label(spells_controls, text="Spellcasting ability:").grid(row=0, column=0, sticky=tk.W)
            ttk.Label(spells_controls, textvariable=self._spellcasting_ability).grid(
                row=0,
                column=1,
                sticky=tk.W,
                padx=(6, 0),
            )
            ttk.Label(spells_controls, text="Prepared spells (one spell per line):").grid(
                row=1,
                column=0,
                columnspan=2,
                sticky=tk.W,
                pady=(8, 0),
            )
            self.prepared_spells_text = tk.Text(spells_controls, wrap=tk.WORD, height=8)
            self.prepared_spells_text.grid(row=2, column=0, columnspan=2, sticky=tk.NSEW, pady=(4, 0))
            spells_controls.columnconfigure(0, weight=1)
            spells_controls.rowconfigure(2, weight=1)
            self.prepared_spells_text.bind("<FocusOut>", self._refresh_summary)
            self.prepared_spells_text.bind("<KeyRelease>", self._refresh_summary)

            ttk.Label(self.stats_tab, textvariable=self.stats_summary, justify=tk.LEFT, anchor=tk.NW).pack(
                fill=tk.BOTH,
                expand=True,
            )
            ttk.Label(
                self.skills_languages_tab,
                textvariable=self.skills_languages_summary,
                justify=tk.LEFT,
                anchor=tk.NW,
            ).pack(fill=tk.BOTH, expand=True)
            ttk.Label(self.equipment_tab, textvariable=self.equipment_summary, justify=tk.LEFT, anchor=tk.NW).pack(
                fill=tk.BOTH,
                expand=True,
            )
            ttk.Label(self.spells_tab, textvariable=self.spells_summary, justify=tk.LEFT, anchor=tk.NW).pack(
                fill=tk.BOTH,
                expand=True,
            )

            self.class_box.bind("<<ComboboxSelected>>", self._refresh_summary)
            self.level_spin.bind("<FocusOut>", self._refresh_summary)
            self.level_spin.bind("<Return>", self._refresh_summary)

            self._refresh_summary()
            self._suppress_change_events = False

        def get_persisted_state(self) -> dict[str, Any]:
            state = BuilderState(
                class_name=self._class_name.get(),
                level=self._safe_level(),
                look_ahead=bool(self._look_ahead.get()),
                ability_scores=self._get_ability_scores(),
                skill_proficiencies=self._get_skill_proficiencies(),
                character_name=self._get_character_name(),
                race_species=self._get_race_species(),
                background=self._get_background(),
                trait=self._get_trait(),
                ideal=self._get_ideal(),
                bond=self._get_bond(),
                flaw=self._get_flaw(),
                character_notes=self._get_character_notes(),
                alignment=self._get_alignment(),
                languages=self._get_languages(),
                starting_gold=self._get_starting_gold(),
                inventory_text=self._get_inventory_text(),
                prepared_spells_text=self._get_prepared_spells_text(),
            )
            return serialize_builder_state(state)

        def apply_persisted_state(self, payload: dict[str, Any]) -> BuilderState:
            state = deserialize_builder_state(
                payload,
                available_classes=self._classes_index.keys(),
            )
            previous_suppression = self._suppress_change_events
            self._suppress_change_events = True
            try:
                self._class_name.set(state.class_name)
                self._level.set(state.level)
                self._look_ahead.set(state.look_ahead)
                for ability, score in state.ability_scores.items():
                    if ability in self._ability_scores:
                        self._ability_scores[ability].set(score)
                for skill, selected in state.skill_proficiencies.items():
                    if skill in self._skill_proficiencies:
                        self._skill_proficiencies[skill].set(selected)
                self._character_name.set(state.character_name)
                self._race_species.set(state.race_species)
                self._background.set(state.background)
                self._trait.set(state.trait)
                self._ideal.set(state.ideal)
                self._bond.set(state.bond)
                self._flaw.set(state.flaw)
                self._character_notes.set(state.character_notes)
                self._alignment.set(state.alignment)
                self._languages.set(state.languages)
                self._starting_gold.set(state.starting_gold)
                self.trait_text.delete("1.0", tk.END)
                if state.trait:
                    self.trait_text.insert("1.0", state.trait)
                self.ideal_text.delete("1.0", tk.END)
                if state.ideal:
                    self.ideal_text.insert("1.0", state.ideal)
                self.bond_text.delete("1.0", tk.END)
                if state.bond:
                    self.bond_text.insert("1.0", state.bond)
                self.flaw_text.delete("1.0", tk.END)
                if state.flaw:
                    self.flaw_text.insert("1.0", state.flaw)
                self.character_notes_text.delete("1.0", tk.END)
                if state.character_notes:
                    self.character_notes_text.insert("1.0", state.character_notes)
                self.inventory_text.delete("1.0", tk.END)
                if state.inventory_text:
                    self.inventory_text.insert("1.0", state.inventory_text)
                self.prepared_spells_text.delete("1.0", tk.END)
                if state.prepared_spells_text:
                    self.prepared_spells_text.insert("1.0", state.prepared_spells_text)
                self._refresh_summary()
            finally:
                self._suppress_change_events = previous_suppression
            return state

        def _safe_level(self) -> int:
            try:
                level = int(self._level.get())
            except (ValueError, tk.TclError):
                return 1
            return min(MAX_LEVEL, max(1, level))

        def _get_ability_scores(self) -> dict[str, int]:
            raw_scores: dict[str, int] = {}
            for ability, var in self._ability_scores.items():
                try:
                    raw_scores[ability] = int(var.get())
                except (ValueError, tk.TclError):
                    raw_scores[ability] = DEFAULT_ABILITY_SCORE

            normalized = normalize_ability_scores(raw_scores)
            for ability, value in normalized.items():
                self._ability_scores[ability].set(value)
            return normalized

        def _get_skill_proficiencies(self) -> dict[str, bool]:
            raw = {skill: var.get() for skill, var in self._skill_proficiencies.items()}
            normalized = normalize_skill_proficiencies(raw)
            for skill, selected in normalized.items():
                self._skill_proficiencies[skill].set(selected)
            return normalized

        def _get_character_name(self) -> str:
            normalized = normalize_identity_text(self._character_name.get())
            self._character_name.set(normalized)
            return normalized

        def _get_race_species(self) -> str:
            normalized = normalize_identity_text(self._race_species.get())
            self._race_species.set(normalized)
            return normalized

        def _get_background(self) -> str:
            normalized = normalize_identity_text(self._background.get())
            self._background.set(normalized)
            return normalized

        def _normalize_text_widget(self, widget: tk.Text) -> str:
            raw_text = widget.get("1.0", tk.END)
            normalized = normalize_trait_text(raw_text)
            cleaned_widget_text = f"{normalized}\n" if normalized else ""
            if raw_text != cleaned_widget_text:
                widget.delete("1.0", tk.END)
                if normalized:
                    widget.insert("1.0", normalized)
            return normalized

        def _get_trait(self) -> str:
            normalized = self._normalize_text_widget(self.trait_text)
            self._trait.set(normalized)
            return normalized

        def _get_ideal(self) -> str:
            normalized = self._normalize_text_widget(self.ideal_text)
            self._ideal.set(normalized)
            return normalized

        def _get_bond(self) -> str:
            normalized = self._normalize_text_widget(self.bond_text)
            self._bond.set(normalized)
            return normalized

        def _get_flaw(self) -> str:
            normalized = self._normalize_text_widget(self.flaw_text)
            self._flaw.set(normalized)
            return normalized

        def _get_character_notes(self) -> str:
            raw_text = self.character_notes_text.get("1.0", tk.END)
            normalized = normalize_character_notes_text(raw_text)
            cleaned_widget_text = f"{normalized}\n" if normalized else ""
            if raw_text != cleaned_widget_text:
                self.character_notes_text.delete("1.0", tk.END)
                if normalized:
                    self.character_notes_text.insert("1.0", normalized)
            self._character_notes.set(normalized)
            return normalized

        def _get_alignment(self) -> str:
            normalized = normalize_alignment(self._alignment.get())
            self._alignment.set(normalized)
            return normalized

        def _get_languages(self) -> str:
            normalized = normalize_languages_text(self._languages.get())
            self._languages.set(normalized)
            return normalized

        def _get_starting_gold(self) -> int:
            normalized = normalize_starting_gold(self._starting_gold.get())
            self._starting_gold.set(normalized)
            return normalized

        def _get_inventory_text(self) -> str:
            raw_text = self.inventory_text.get("1.0", tk.END)
            normalized = normalize_inventory_text(raw_text)
            cleaned_widget_text = f"{normalized}\n" if normalized else ""
            if raw_text != cleaned_widget_text:
                self.inventory_text.delete("1.0", tk.END)
                if normalized:
                    self.inventory_text.insert("1.0", normalized)
            return normalized

        def _get_prepared_spells_text(self) -> str:
            raw_text = self.prepared_spells_text.get("1.0", tk.END)
            normalized = normalize_prepared_spells_text(raw_text)
            cleaned_widget_text = f"{normalized}\n" if normalized else ""
            if raw_text != cleaned_widget_text:
                self.prepared_spells_text.delete("1.0", tk.END)
                if normalized:
                    self.prepared_spells_text.insert("1.0", normalized)
            return normalized

        def _refresh_summary(self, _event: tk.Event | None = None) -> None:
            class_name = self._class_name.get()
            if class_name not in self._classes_index:
                return

            level = self._safe_level()
            self._level.set(level)
            look_ahead = bool(self._look_ahead.get())
            snapshot = build_level_snapshot(
                class_name,
                level,
                look_ahead=look_ahead,
                classes_index=self._classes_index,
            )

            ability_scores = self._get_ability_scores()
            skill_proficiencies = self._get_skill_proficiencies()
            character_name = self._get_character_name()
            race_species = self._get_race_species()
            background = self._get_background()
            trait = self._get_trait()
            ideal = self._get_ideal()
            bond = self._get_bond()
            flaw = self._get_flaw()
            character_notes = self._get_character_notes()
            alignment = self._get_alignment()
            languages = self._get_languages()
            starting_gold = self._get_starting_gold()
            inventory_text = self._get_inventory_text()
            prepared_spells_text = self._get_prepared_spells_text()

            self.summary.configure(state=tk.NORMAL)
            self.summary.delete("1.0", tk.END)
            self.summary.insert(
                "1.0",
                format_builder_summary(
                    snapshot,
                    look_ahead=look_ahead,
                    character_name=character_name,
                    race_species=race_species,
                    background=background,
                    trait=trait,
                    ideal=ideal,
                    bond=bond,
                    flaw=flaw,
                    character_notes=character_notes,
                    alignment=alignment,
                    ability_scores=ability_scores,
                    skill_proficiencies=skill_proficiencies,
                    languages=languages,
                    starting_gold=starting_gold,
                    inventory_text=inventory_text,
                    prepared_spells_text=prepared_spells_text,
                    level_input=self._level.get(),
                ),
            )
            self.summary.configure(state=tk.DISABLED)

            self.stats_summary.set(format_stats_summary(snapshot, ability_scores))
            self.skills_languages_summary.set(
                format_skills_languages_summary(
                    snapshot,
                    skill_proficiencies,
                    languages,
                )
            )
            self.equipment_summary.set(
                format_equipment_summary(
                    snapshot,
                    starting_gold,
                    inventory_text,
                )
            )
            spellcasting_ability = (
                snapshot.spellcasting.get("spellcasting_ability")
                if isinstance(snapshot.spellcasting, dict)
                else None
            )
            self._spellcasting_ability.set(spellcasting_ability or "None")
            self.spells_summary.set(format_spells_summary(snapshot, prepared_spells_text))

            if self._on_state_change is not None and not self._suppress_change_events:
                self._on_state_change(self.get_persisted_state())


    def attach_builder_tab(
        notebook: ttk.Notebook,
        on_state_change: Callable[[dict[str, Any]], None] | None = None,
    ) -> BuilderTab:
        tab = BuilderTab(notebook, on_state_change=on_state_change)
        notebook.add(tab, text="Builder")
        return tab
else:
    class BuilderTab:  # type: ignore[no-redef]
        def __init__(self, *_args: Any, **_kwargs: Any) -> None:
            raise RuntimeError("tkinter is not available in this Python runtime")


    def attach_builder_tab(*_args: Any, **_kwargs: Any) -> BuilderTab:  # type: ignore[no-redef]
        raise RuntimeError("tkinter is not available in this Python runtime")
