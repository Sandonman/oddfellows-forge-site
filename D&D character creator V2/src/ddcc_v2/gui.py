"""Tkinter GUI for D&D Character Creator V2."""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from .calculations import format_bonus
from .data_loader import index_by_name, load_dataset
from .models import ABILITIES, Character
from .pdf_export import export_character_pdf
from .persistence import load_character, save_character
from .service import ValidationError, derive_character, validate_character_input
from .tooltip import ListboxTooltip, Tooltip


class CharacterCreatorGUI(ttk.Frame):
    def __init__(self, master: tk.Tk) -> None:
        super().__init__(master, padding=8)
        self.master = master
        self.data = load_dataset()

        self.classes_by_name = index_by_name(self.data["classes"])
        self.species_by_name = index_by_name(self.data["species"])
        self.backgrounds_by_name = index_by_name(self.data["backgrounds"])
        self.skills_by_name = index_by_name(self.data["skills"])
        self.armor_by_name = index_by_name(self.data["equipment"]["armor"])

        self.character = Character()

        self._build_state_vars()
        self._build_ui()
        self._reset_defaults()
        self.pack(fill=tk.BOTH, expand=True)

    @staticmethod
    def _is_baseline_armor(item: dict[str, object]) -> bool:
        armor_type = str(item.get("type", item.get("armor_type", ""))).lower()
        return armor_type != "shield"

    @staticmethod
    def _weapon_properties_text(weapon: dict[str, object]) -> str:
        legacy = weapon.get("properties")
        if isinstance(legacy, str):
            return legacy
        explicit = weapon.get("properties_text")
        if isinstance(explicit, str):
            return explicit
        raw = weapon.get("properties")
        if isinstance(raw, list):
            return ", ".join(str(x) for x in raw) if raw else "-"
        return "-"

    def _build_state_vars(self) -> None:
        self.var_name = tk.StringVar(value="")
        self.var_alignment = tk.StringVar(value=self.data["alignments"][4])
        self.var_species = tk.StringVar(value="Human")
        self.var_class = tk.StringVar(value="Fighter")
        self.var_background = tk.StringVar(value="Acolyte")

        self.var_languages_extra = tk.StringVar(value="")
        self.var_selected_armor = tk.StringVar(value="Unarmored")
        self.var_equipment_notes = tk.StringVar(value="")

        self.var_spell_note = tk.StringVar(value="")
        self.var_skill_note = tk.StringVar(value="")

        self.ability_vars: dict[str, tk.IntVar] = {ability: tk.IntVar(value=10) for ability in ABILITIES}

    def _build_ui(self) -> None:
        self.master.title("D&D Character Creator V2 (SRD Level 1)")
        self.master.geometry("1180x780")

        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True)

        self.tab_identity = ttk.Frame(notebook, padding=8)
        self.tab_species = ttk.Frame(notebook, padding=8)
        self.tab_class = ttk.Frame(notebook, padding=8)
        self.tab_background = ttk.Frame(notebook, padding=8)
        self.tab_abilities = ttk.Frame(notebook, padding=8)
        self.tab_skills = ttk.Frame(notebook, padding=8)
        self.tab_equipment = ttk.Frame(notebook, padding=8)
        self.tab_spells = ttk.Frame(notebook, padding=8)
        self.tab_summary = ttk.Frame(notebook, padding=8)

        notebook.add(self.tab_identity, text="Identity")
        notebook.add(self.tab_species, text="Species")
        notebook.add(self.tab_class, text="Class")
        notebook.add(self.tab_background, text="Background")
        notebook.add(self.tab_abilities, text="Ability Scores")
        notebook.add(self.tab_skills, text="Skills/Saves")
        notebook.add(self.tab_equipment, text="Equipment")
        notebook.add(self.tab_spells, text="Spells")
        notebook.add(self.tab_summary, text="Summary/Export")

        self._build_identity_tab()
        self._build_species_tab()
        self._build_class_tab()
        self._build_background_tab()
        self._build_abilities_tab()
        self._build_skills_tab()
        self._build_equipment_tab()
        self._build_spells_tab()
        self._build_summary_tab()

    def _build_identity_tab(self) -> None:
        ttk.Label(self.tab_identity, text="Character Name").grid(row=0, column=0, sticky="w")
        ttk.Entry(self.tab_identity, textvariable=self.var_name, width=40).grid(row=0, column=1, sticky="w", padx=8)

        ttk.Label(self.tab_identity, text="Alignment").grid(row=1, column=0, sticky="w", pady=(8, 0))
        cmb_alignment = ttk.Combobox(
            self.tab_identity,
            textvariable=self.var_alignment,
            values=self.data["alignments"],
            state="readonly",
            width=30,
        )
        cmb_alignment.grid(row=1, column=1, sticky="w", padx=8, pady=(8, 0))

        ttk.Label(self.tab_identity, text="Extra Languages (comma-separated)").grid(row=2, column=0, sticky="w", pady=(8, 0))
        ttk.Entry(self.tab_identity, textvariable=self.var_languages_extra, width=40).grid(
            row=2, column=1, sticky="w", padx=8, pady=(8, 0)
        )

    def _build_species_tab(self) -> None:
        ttk.Label(self.tab_species, text="Species").grid(row=0, column=0, sticky="w")
        cmb = ttk.Combobox(
            self.tab_species,
            textvariable=self.var_species,
            values=sorted(self.species_by_name.keys()),
            state="readonly",
            width=36,
        )
        cmb.grid(row=0, column=1, sticky="w", padx=8)
        cmb.bind("<<ComboboxSelected>>", lambda _e: self._refresh_summary_preview())

        Tooltip(cmb, lambda: self._species_tooltip(self.var_species.get()))

        self.species_text = tk.Text(self.tab_species, width=90, height=16, wrap=tk.WORD)
        self.species_text.grid(row=1, column=0, columnspan=3, sticky="nsew", pady=(10, 0))
        self.species_text.configure(state=tk.DISABLED)

        self.tab_species.rowconfigure(1, weight=1)
        self.tab_species.columnconfigure(2, weight=1)

    def _build_class_tab(self) -> None:
        ttk.Label(self.tab_class, text="Class").grid(row=0, column=0, sticky="w")
        cmb = ttk.Combobox(
            self.tab_class,
            textvariable=self.var_class,
            values=sorted(self.classes_by_name.keys()),
            state="readonly",
            width=36,
        )
        cmb.grid(row=0, column=1, sticky="w", padx=8)
        cmb.bind("<<ComboboxSelected>>", lambda _e: self._on_class_changed())
        Tooltip(cmb, lambda: self._class_tooltip(self.var_class.get()))

        self.class_text = tk.Text(self.tab_class, width=90, height=20, wrap=tk.WORD)
        self.class_text.grid(row=1, column=0, columnspan=3, sticky="nsew", pady=(10, 0))
        self.class_text.configure(state=tk.DISABLED)

        self.tab_class.rowconfigure(1, weight=1)
        self.tab_class.columnconfigure(2, weight=1)

    def _build_background_tab(self) -> None:
        ttk.Label(self.tab_background, text="Background").grid(row=0, column=0, sticky="w")
        cmb = ttk.Combobox(
            self.tab_background,
            textvariable=self.var_background,
            values=sorted(self.backgrounds_by_name.keys()),
            state="readonly",
            width=36,
        )
        cmb.grid(row=0, column=1, sticky="w", padx=8)
        cmb.bind("<<ComboboxSelected>>", lambda _e: self._on_background_changed())
        Tooltip(cmb, lambda: self._background_tooltip(self.var_background.get()))

        self.background_text = tk.Text(self.tab_background, width=90, height=16, wrap=tk.WORD)
        self.background_text.grid(row=1, column=0, columnspan=3, sticky="nsew", pady=(10, 0))
        self.background_text.configure(state=tk.DISABLED)

        self.tab_background.rowconfigure(1, weight=1)
        self.tab_background.columnconfigure(2, weight=1)

    def _build_abilities_tab(self) -> None:
        ttk.Label(self.tab_abilities, text="Base ability scores (3-18). Species bonuses are applied automatically.").grid(
            row=0, column=0, columnspan=3, sticky="w"
        )

        for i, ability in enumerate(ABILITIES, start=1):
            ttk.Label(self.tab_abilities, text=ability).grid(row=i, column=0, sticky="w", pady=4)
            ttk.Spinbox(
                self.tab_abilities,
                from_=3,
                to=18,
                textvariable=self.ability_vars[ability],
                width=8,
                command=self._refresh_summary_preview,
            ).grid(row=i, column=1, sticky="w")

        ttk.Button(self.tab_abilities, text="Standard Array", command=self._apply_standard_array).grid(row=7, column=0, pady=(10, 0), sticky="w")

    def _build_skills_tab(self) -> None:
        left = ttk.Frame(self.tab_skills)
        right = ttk.Frame(self.tab_skills)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)

        ttk.Label(left, text="Class Skill Choices").pack(anchor="w")
        self.class_skill_list = tk.Listbox(left, selectmode=tk.MULTIPLE, exportselection=False, width=36, height=16)
        self.class_skill_list.pack(fill=tk.BOTH, expand=True, pady=(4, 4))
        self.class_skill_list.bind("<<ListboxSelect>>", self._enforce_class_skill_limit)
        ListboxTooltip(self.class_skill_list, lambda item: self.skills_by_name[item]["description"])

        self.class_skill_note_label = ttk.Label(left, textvariable=self.var_skill_note)
        self.class_skill_note_label.pack(anchor="w")

        ttk.Label(right, text="Saving Throws (from class)").pack(anchor="w")
        self.saving_throw_label = ttk.Label(right, text="")
        self.saving_throw_label.pack(anchor="w", pady=(4, 12))

        ttk.Label(right, text="Background Skills (auto) ").pack(anchor="w")
        self.background_skills_label = ttk.Label(right, text="")
        self.background_skills_label.pack(anchor="w", pady=(4, 12))

    def _build_equipment_tab(self) -> None:
        top = ttk.Frame(self.tab_equipment)
        top.pack(fill=tk.X)

        ttk.Label(top, text="Armor for AC baseline").grid(row=0, column=0, sticky="w")
        baseline_armor = [a for a in self.data["equipment"]["armor"] if self._is_baseline_armor(a)]
        cmb_armor = ttk.Combobox(
            top,
            textvariable=self.var_selected_armor,
            values=[a["name"] for a in baseline_armor],
            state="readonly",
            width=34,
        )
        cmb_armor.grid(row=0, column=1, sticky="w", padx=8)
        cmb_armor.bind("<<ComboboxSelected>>", lambda _e: self._refresh_summary_preview())
        Tooltip(cmb_armor, lambda: self.armor_by_name[self.var_selected_armor.get()]["description"])

        ttk.Label(top, text="Class starting equipment notes (free text)").grid(row=1, column=0, sticky="w", pady=(8, 0))
        ttk.Entry(top, textvariable=self.var_equipment_notes, width=80).grid(row=1, column=1, sticky="w", padx=8, pady=(8, 0))

        body = ttk.Frame(self.tab_equipment)
        body.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        self.weapon_list = self._make_equipment_listbox(body, "Weapons", [x["name"] for x in self.data["equipment"]["weapons"]], 0)
        self.pack_list = self._make_equipment_listbox(body, "Packs", [x["name"] for x in self.data["equipment"]["packs"]], 1)
        self.gear_list = self._make_equipment_listbox(body, "Adventuring Gear", [x["name"] for x in self.data["equipment"]["adventuring_gear"]], 2)

        weapon_index = index_by_name(self.data["equipment"]["weapons"])
        packs_index = index_by_name(self.data["equipment"]["packs"])
        gear_index = index_by_name(self.data["equipment"]["adventuring_gear"])

        ListboxTooltip(
            self.weapon_list,
            lambda item: f"{weapon_index[item]['damage']} | {self._weapon_properties_text(weapon_index[item])}\n{weapon_index[item]['description']}",
        )
        ListboxTooltip(self.pack_list, lambda item: packs_index[item]["description"])
        ListboxTooltip(self.gear_list, lambda item: gear_index[item]["description"])

    def _make_equipment_listbox(self, parent: ttk.Frame, title: str, values: list[str], col: int) -> tk.Listbox:
        frame = ttk.Frame(parent)
        frame.grid(row=0, column=col, sticky="nsew", padx=4)
        parent.columnconfigure(col, weight=1)

        ttk.Label(frame, text=title).pack(anchor="w")
        listbox = tk.Listbox(frame, selectmode=tk.MULTIPLE, exportselection=False, height=16)
        for value in values:
            listbox.insert(tk.END, value)
        listbox.pack(fill=tk.BOTH, expand=True, pady=(4, 0))
        return listbox

    def _build_spells_tab(self) -> None:
        ttk.Label(self.tab_spells, textvariable=self.var_spell_note).pack(anchor="w")

        row = ttk.Frame(self.tab_spells)
        row.pack(fill=tk.BOTH, expand=True, pady=(8, 0))

        cantrip_frame = ttk.Frame(row)
        level1_frame = ttk.Frame(row)
        cantrip_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        level1_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)

        ttk.Label(cantrip_frame, text="Cantrips").pack(anchor="w")
        self.cantrip_list = tk.Listbox(cantrip_frame, selectmode=tk.MULTIPLE, exportselection=False, height=20)
        self.cantrip_list.pack(fill=tk.BOTH, expand=True, pady=(4, 0))
        self.cantrip_list.bind("<<ListboxSelect>>", lambda _e: self._on_spell_selection())

        ttk.Label(level1_frame, text="Level 1 Spells").pack(anchor="w")
        self.level1_spell_list = tk.Listbox(level1_frame, selectmode=tk.MULTIPLE, exportselection=False, height=20)
        self.level1_spell_list.pack(fill=tk.BOTH, expand=True, pady=(4, 0))
        self.level1_spell_list.bind("<<ListboxSelect>>", lambda _e: self._on_spell_selection())

        spells_index = index_by_name(self.data["spells"])
        ListboxTooltip(self.cantrip_list, lambda item: self._spell_tooltip(spells_index[item]))
        ListboxTooltip(self.level1_spell_list, lambda item: self._spell_tooltip(spells_index[item]))

    def _build_summary_tab(self) -> None:
        buttons = ttk.Frame(self.tab_summary)
        buttons.pack(fill=tk.X)

        ttk.Button(buttons, text="Recalculate", command=self._refresh_summary_preview).pack(side=tk.LEFT)
        ttk.Button(buttons, text="Save Character JSON", command=self._save_character_dialog).pack(side=tk.LEFT, padx=6)
        ttk.Button(buttons, text="Load Character JSON", command=self._load_character_dialog).pack(side=tk.LEFT, padx=6)
        ttk.Button(buttons, text="Export PDF", command=self._export_pdf_dialog).pack(side=tk.LEFT, padx=6)

        ttk.Label(self.tab_summary, text="Notes").pack(anchor="w", pady=(10, 0))
        self.notes_text = tk.Text(self.tab_summary, width=70, height=5, wrap=tk.WORD)
        self.notes_text.pack(fill=tk.X)

        self.summary_text = tk.Text(self.tab_summary, wrap=tk.WORD)
        self.summary_text.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        self.summary_text.configure(state=tk.DISABLED)

    def _reset_defaults(self) -> None:
        defaults = [15, 14, 13, 12, 10, 8]
        for ability, value in zip(ABILITIES, defaults):
            self.ability_vars[ability].set(value)

        self.var_species.set("Human")
        self.var_class.set("Fighter")
        self.var_background.set("Acolyte")
        self.var_selected_armor.set("Unarmored")

        self._on_class_changed()
        self._on_background_changed()
        self._on_species_changed()
        self._refresh_summary_preview()

    def _apply_standard_array(self) -> None:
        values = [15, 14, 13, 12, 10, 8]
        for ability, value in zip(ABILITIES, values):
            self.ability_vars[ability].set(value)
        self._refresh_summary_preview()

    def _species_tooltip(self, species_name: str) -> str:
        species = self.species_by_name.get(species_name)
        if not species:
            return ""
        bonuses = ", ".join(f"{k} +{v}" for k, v in species.get("ability_bonuses", {}).items())
        langs = ", ".join(species.get("languages", []))
        return (
            f"{species['name']} ({species['size']}, {species['speed']} ft)\n"
            f"Ability bonuses: {bonuses or 'None'}\n"
            f"Languages: {langs or 'None'}\n"
            f"Traits: {species.get('traits', '')}\n"
            f"{species.get('description', '')}"
        )

    def _class_tooltip(self, class_name: str) -> str:
        cls = self.classes_by_name.get(class_name)
        if not cls:
            return ""
        return (
            f"{cls['name']} (d{cls['hit_die']} hit die)\n"
            f"Saving throws: {', '.join(cls['saving_throws'])}\n"
            f"Skill choices: choose {cls['skill_choose']} from {', '.join(cls['skill_choices'])}\n"
            f"Proficiencies: {cls['proficiencies']}\n"
            f"{cls['description']}"
        )

    def _background_tooltip(self, background_name: str) -> str:
        bg = self.backgrounds_by_name.get(background_name)
        if not bg:
            return ""
        return (
            f"{bg['name']}\n"
            f"Skills: {', '.join(bg['skill_proficiencies'])}\n"
            f"Languages: {', '.join(bg.get('languages', [])) or 'None'}\n"
            f"Equipment: {', '.join(bg.get('equipment', []))}\n"
            f"{bg.get('description', '')}"
        )

    def _spell_tooltip(self, spell: dict) -> str:
        return (
            f"{spell['name']} (Level {spell['level']} {spell['school']})\n"
            f"Classes: {', '.join(spell['classes'])}\n"
            f"Casting Time: {spell['casting_time']}\n"
            f"Range: {spell['range']}\n"
            f"Components: {spell['components']}\n"
            f"Duration: {spell['duration']}\n"
            f"{spell['description']}"
        )

    def _on_species_changed(self) -> None:
        species = self.species_by_name[self.var_species.get()]
        text = self._species_tooltip(species["name"])
        self._set_text(self.species_text, text)
        self._refresh_summary_preview()

    def _on_class_changed(self) -> None:
        class_name = self.var_class.get()
        cls = self.classes_by_name[class_name]

        self.class_skill_list.delete(0, tk.END)
        for skill in cls["skill_choices"]:
            self.class_skill_list.insert(tk.END, skill)

        self.var_skill_note.set(f"Choose {cls['skill_choose']} class skills")
        self.saving_throw_label.configure(text=", ".join(cls["saving_throws"]))
        self._set_text(self.class_text, self._class_full_text(cls))

        self._refresh_spells_tab()
        self._refresh_summary_preview()

    def _on_background_changed(self) -> None:
        bg = self.backgrounds_by_name[self.var_background.get()]
        self.background_skills_label.configure(text=", ".join(bg["skill_proficiencies"]))
        self._set_text(self.background_text, self._background_tooltip(bg["name"]))
        self._refresh_summary_preview()

    def _class_full_text(self, cls: dict) -> str:
        lines = [
            f"{cls['name']}\n",
            f"Hit Die: d{cls['hit_die']}",
            f"Saving Throws: {', '.join(cls['saving_throws'])}",
            f"Class Skills: choose {cls['skill_choose']} from {', '.join(cls['skill_choices'])}",
            f"Proficiencies: {cls['proficiencies']}",
            "",
            "Starting Equipment Suggestions:",
        ]
        lines.extend(f"- {item}" for item in cls["starting_equipment"])
        lines.append("")
        lines.append(cls["description"])
        return "\n".join(lines)

    def _set_text(self, widget: tk.Text, content: str) -> None:
        widget.configure(state=tk.NORMAL)
        widget.delete("1.0", tk.END)
        widget.insert("1.0", content)
        widget.configure(state=tk.DISABLED)

    def _enforce_class_skill_limit(self, _event: tk.Event | None = None) -> None:
        cls = self.classes_by_name[self.var_class.get()]
        limit = int(cls["skill_choose"])
        selected = list(self.class_skill_list.curselection())
        if len(selected) > limit:
            for idx in selected[limit:]:
                self.class_skill_list.selection_clear(idx)
            messagebox.showwarning("Skill limit", f"You can choose up to {limit} class skills for {cls['name']}.")
        self._refresh_summary_preview()

    def _refresh_spells_tab(self) -> None:
        cls = self.classes_by_name[self.var_class.get()]
        class_name = cls["name"]

        cantrips = sorted([s["name"] for s in self.data["spells"] if s["level"] == 0 and class_name in s["classes"]])
        level1 = sorted([s["name"] for s in self.data["spells"] if s["level"] == 1 and class_name in s["classes"]])

        self.cantrip_list.delete(0, tk.END)
        self.level1_spell_list.delete(0, tk.END)

        for spell in cantrips:
            self.cantrip_list.insert(tk.END, spell)
        for spell in level1:
            self.level1_spell_list.insert(tk.END, spell)

        mode = cls.get("spellcasting_mode", "none")
        if mode == "none":
            self.var_spell_note.set("This class has no level-1 spellcasting.")
            self.cantrip_list.configure(state=tk.DISABLED)
            self.level1_spell_list.configure(state=tk.DISABLED)
        else:
            self.cantrip_list.configure(state=tk.NORMAL)
            self.level1_spell_list.configure(state=tk.NORMAL)
            cantrip_limit, level1_limit = self._spell_limits_for_class(cls)
            if mode == "prepared":
                self.var_spell_note.set(
                    f"Prepared caster: choose up to {cantrip_limit} cantrips and {level1_limit} prepared level-1 spells (ability mod + level, minimum 1)."
                )
            elif mode == "spellbook":
                self.var_spell_note.set(
                    f"Spellbook caster: choose up to {cantrip_limit} cantrips and {level1_limit} level-1 spells known in spellbook."
                )
            else:
                self.var_spell_note.set(f"Known caster: choose up to {cantrip_limit} cantrips and {level1_limit} level-1 spells known.")

    def _spell_limits_for_class(self, cls: dict) -> tuple[int, int]:
        cantrip_limit = int(cls.get("cantrips_known", 0))
        mode = cls.get("spellcasting_mode", "none")
        if mode == "prepared":
            casting_ability = cls.get("spellcasting_ability")
            if casting_ability:
                mod = (int(self.ability_vars[casting_ability].get()) - 10) // 2
                level1_limit = max(1, mod + 1)
            else:
                level1_limit = 1
        else:
            level1_limit = int(cls.get("level1_spell_count", 0))
        return cantrip_limit, level1_limit

    def _enforce_spell_limits(self) -> None:
        cls = self.classes_by_name[self.var_class.get()]
        if cls.get("spellcasting_mode") == "none":
            return

        cantrip_limit, level1_limit = self._spell_limits_for_class(cls)
        self._trim_listbox_to_limit(self.cantrip_list, cantrip_limit, "cantrips")
        self._trim_listbox_to_limit(self.level1_spell_list, level1_limit, "level-1 spells")

    def _on_spell_selection(self) -> None:
        self._enforce_spell_limits()
        self._refresh_summary_preview()

    def _trim_listbox_to_limit(self, listbox: tk.Listbox, limit: int, label: str) -> None:
        selected = list(listbox.curselection())
        if len(selected) <= limit:
            return
        for idx in selected[limit:]:
            listbox.selection_clear(idx)
        messagebox.showwarning("Spell limit", f"Selection trimmed to {limit} {label}.")

    def _collect_listbox_selection(self, listbox: tk.Listbox) -> list[str]:
        return [listbox.get(i) for i in listbox.curselection()]

    def _create_character_from_form(self) -> Character:
        base_scores = {}
        for ability in ABILITIES:
            base_scores[ability] = int(self.ability_vars[ability].get())

        char = Character(
            name=self.var_name.get().strip(),
            level=1,
            alignment=self.var_alignment.get(),
            species=self.var_species.get(),
            char_class=self.var_class.get(),
            background=self.var_background.get(),
            base_ability_scores=base_scores,
        )

        class_skills = self._collect_listbox_selection(self.class_skill_list)
        char.skill_proficiencies = class_skills

        extra_languages = [x.strip() for x in self.var_languages_extra.get().split(",") if x.strip()]
        char.languages = extra_languages

        equipment = []
        armor = self.var_selected_armor.get().strip()
        if armor and armor != "Unarmored":
            equipment.append(armor)
            char.selected_armor = armor
        equipment.extend(self._collect_listbox_selection(self.weapon_list))
        equipment.extend(self._collect_listbox_selection(self.pack_list))
        equipment.extend(self._collect_listbox_selection(self.gear_list))
        if self.var_equipment_notes.get().strip():
            equipment.append(self.var_equipment_notes.get().strip())
        char.equipment = sorted(set(equipment))

        char.attacks = [x for x in self._collect_listbox_selection(self.weapon_list)]

        cls = self.classes_by_name[char.char_class]
        if cls.get("spellcasting_mode") != "none":
            char.known_spells = {
                "0": self._collect_listbox_selection(self.cantrip_list),
                "1": self._collect_listbox_selection(self.level1_spell_list),
            }

        char.notes = self.notes_text.get("1.0", tk.END).strip()

        validate_character_input(char, self.data)

        selected_armor_item = self.armor_by_name.get(self.var_selected_armor.get())
        if selected_armor_item and selected_armor_item["name"] == "Unarmored":
            selected_armor_item = None

        return derive_character(char, self.data, selected_armor=selected_armor_item, skills_index=self.skills_by_name)

    def _refresh_summary_preview(self) -> None:
        try:
            character = self._create_character_from_form()
            self.character = character
        except ValidationError as exc:
            self._set_text(self.summary_text, f"Validation error: {exc}")
            return
        except Exception as exc:  # noqa: BLE001
            self._set_text(self.summary_text, f"Unable to calculate character: {exc}")
            return

        self._set_text(self.summary_text, self._summary_text(character))

    def _summary_text(self, char: Character) -> str:
        lines = [
            f"Name: {char.name}",
            f"Level: {char.level}",
            f"Species: {char.species}",
            f"Class: {char.char_class}",
            f"Background: {char.background}",
            f"Alignment: {char.alignment}",
            "",
            f"Proficiency Bonus: {format_bonus(char.proficiency_bonus)}",
            f"HP: {char.max_hp}",
            f"AC: {char.ac_baseline}",
            f"Initiative: {format_bonus(char.initiative)}",
            f"Passive Perception: {char.passive_perception}",
            f"Speed: {char.speed} ft | Size: {char.size}",
            "",
            "Ability Scores:",
        ]
        for ability in ABILITIES:
            lines.append(f"- {ability}: {char.final_ability_scores[ability]} ({format_bonus(char.ability_modifiers[ability])})")

        lines.extend(
            [
                "",
                f"Saving Throw Proficiencies: {', '.join(char.saving_throw_proficiencies) or 'None'}",
                f"Skill Proficiencies: {', '.join(char.skill_proficiencies) or 'None'}",
                f"Languages: {', '.join(char.languages) or 'None'}",
                "",
                f"Equipment: {', '.join(char.equipment) or 'None'}",
                f"Attacks (placeholders): {', '.join(char.attacks) or 'None'}",
                "",
            ]
        )

        if char.spellcasting_ability:
            lines.extend(
                [
                    f"Spellcasting Ability: {char.spellcasting_ability}",
                    f"Spell Save DC: {char.spell_save_dc}",
                    f"Spell Attack Bonus: {format_bonus(char.spell_attack_bonus or 0)}",
                    f"Cantrips: {', '.join(char.known_spells.get('0', [])) or 'None'}",
                    f"Level 1 Spells: {', '.join(char.known_spells.get('1', [])) or 'None'}",
                ]
            )
        else:
            lines.append("Spellcasting: None at level 1")

        return "\n".join(lines)

    def _save_character_dialog(self) -> None:
        try:
            char = self._create_character_from_form()
        except ValidationError as exc:
            messagebox.showerror("Validation", str(exc))
            return

        path = filedialog.asksaveasfilename(
            title="Save Character",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )
        if not path:
            return

        save_character(char, path)
        messagebox.showinfo("Saved", f"Character saved:\n{path}")

    def _load_character_dialog(self) -> None:
        path = filedialog.askopenfilename(
            title="Load Character",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )
        if not path:
            return

        loaded = load_character(path)
        self._populate_form(loaded)
        self._refresh_summary_preview()
        messagebox.showinfo("Loaded", f"Character loaded:\n{path}")

    def _export_pdf_dialog(self) -> None:
        try:
            char = self._create_character_from_form()
        except ValidationError as exc:
            messagebox.showerror("Validation", str(exc))
            return

        path = filedialog.asksaveasfilename(
            title="Export Character PDF",
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
        )
        if not path:
            return

        export_character_pdf(char, path)
        messagebox.showinfo("Exported", f"PDF written:\n{path}")

    def _populate_form(self, char: Character) -> None:
        self.var_name.set(char.name)
        self.var_alignment.set(char.alignment)
        self.var_species.set(char.species)
        self.var_class.set(char.char_class)
        self.var_background.set(char.background)

        for ability in ABILITIES:
            self.ability_vars[ability].set(int(char.base_ability_scores.get(ability, 10)))

        self.var_languages_extra.set(", ".join([x for x in char.languages if x not in self.species_by_name.get(char.species, {}).get("languages", [])]))

        self.var_selected_armor.set(char.selected_armor if char.selected_armor else "Unarmored")
        self.var_equipment_notes.set("")

        self._on_class_changed()
        self._on_background_changed()
        self._on_species_changed()

        self._set_listbox_selection(self.class_skill_list, char.skill_proficiencies)
        self._set_listbox_selection(self.weapon_list, char.equipment)
        self._set_listbox_selection(self.pack_list, char.equipment)
        self._set_listbox_selection(self.gear_list, char.equipment)

        self._set_listbox_selection(self.cantrip_list, char.known_spells.get("0", []))
        self._set_listbox_selection(self.level1_spell_list, char.known_spells.get("1", []))

        self.notes_text.delete("1.0", tk.END)
        self.notes_text.insert("1.0", char.notes)

    def _set_listbox_selection(self, listbox: tk.Listbox, values: list[str]) -> None:
        value_set = set(values)
        listbox.selection_clear(0, tk.END)
        for i in range(listbox.size()):
            if listbox.get(i) in value_set:
                listbox.selection_set(i)


def launch_app() -> None:
    root = tk.Tk()
    app = CharacterCreatorGUI(root)

    app.var_species.trace_add("write", lambda *_: app._on_species_changed())
    app.var_background.trace_add("write", lambda *_: app._on_background_changed())

    icon_path = Path(__file__).resolve().parent / "data" / "icon.ico"
    if icon_path.exists():
        try:
            root.iconbitmap(default=str(icon_path))
        except Exception:  # noqa: BLE001
            pass

    root.mainloop()
