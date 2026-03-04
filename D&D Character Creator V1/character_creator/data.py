"""SRD 5.2.1-inspired character creation data (simplified)."""

ABILITIES = ["STR", "DEX", "CON", "INT", "WIS", "CHA"]

SKILLS = {
    "Acrobatics": "DEX",
    "Animal Handling": "WIS",
    "Arcana": "INT",
    "Athletics": "STR",
    "Deception": "CHA",
    "History": "INT",
    "Insight": "WIS",
    "Intimidation": "CHA",
    "Investigation": "INT",
    "Medicine": "WIS",
    "Nature": "INT",
    "Perception": "WIS",
    "Performance": "CHA",
    "Persuasion": "CHA",
    "Religion": "INT",
    "Sleight of Hand": "DEX",
    "Stealth": "DEX",
    "Survival": "WIS",
}

SPECIES = {
    "Human": {
        "ability_bonuses": {"STR": 1, "DEX": 1, "CON": 1, "INT": 1, "WIS": 1, "CHA": 1},
        "notes": "Versatile and adaptable.",
    },
    "Dwarf": {
        "ability_bonuses": {"CON": 2, "WIS": 1},
        "notes": "Resilient with stonecunning traditions.",
    },
    "Elf": {
        "ability_bonuses": {"DEX": 2, "INT": 1},
        "notes": "Keen senses and fey ancestry themes.",
    },
    "Halfling": {
        "ability_bonuses": {"DEX": 2, "CHA": 1},
        "notes": "Lucky and nimble folk.",
    },
    "Orc": {
        "ability_bonuses": {"STR": 2, "CON": 1},
        "notes": "Powerful and relentless spirit.",
    },
}

CLASSES = {
    "Fighter": {
        "saving_throws": ["STR", "CON"],
        "skill_choices": [
            "Acrobatics",
            "Animal Handling",
            "Athletics",
            "History",
            "Insight",
            "Intimidation",
            "Perception",
            "Survival",
        ],
        "num_skill_choices": 2,
    },
    "Wizard": {
        "saving_throws": ["INT", "WIS"],
        "skill_choices": ["Arcana", "History", "Insight", "Investigation", "Medicine", "Religion"],
        "num_skill_choices": 2,
    },
    "Rogue": {
        "saving_throws": ["DEX", "INT"],
        "skill_choices": [
            "Acrobatics",
            "Athletics",
            "Deception",
            "Insight",
            "Intimidation",
            "Investigation",
            "Perception",
            "Performance",
            "Persuasion",
            "Sleight of Hand",
            "Stealth",
        ],
        "num_skill_choices": 4,
    },
    "Cleric": {
        "saving_throws": ["WIS", "CHA"],
        "skill_choices": ["History", "Insight", "Medicine", "Persuasion", "Religion"],
        "num_skill_choices": 2,
    },
}

BACKGROUNDS = {
    "Acolyte": {
        "skill_proficiencies": ["Insight", "Religion"],
        "notes": "Temple life and sacred studies.",
    },
    "Soldier": {
        "skill_proficiencies": ["Athletics", "Intimidation"],
        "notes": "Military training and rank.",
    },
    "Criminal": {
        "skill_proficiencies": ["Deception", "Stealth"],
        "notes": "Underworld contacts and experience.",
    },
    "Sage": {
        "skill_proficiencies": ["Arcana", "History"],
        "notes": "Academic and research focus.",
    },
}
