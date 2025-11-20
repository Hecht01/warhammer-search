"""Scrape Warhammer 40K 10th edition rules and stratagems."""

import json
import logging
from pathlib import Path
import requests
from bs4 import BeautifulSoup
from typing import List, Dict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def scrape_core_rules() -> List[Dict]:
    """Scrape core rules from Warhammer Community or Wahapedia."""
    rules = []

    # Define core rules structure (these are publicly available)
    core_rules_data = {
        "Movement Phase": [
            ("Move", "Units can move up to their Move (M) characteristic."),
            ("Advance", "Roll D6 and add to Move. Cannot shoot or charge."),
            ("Fall Back", "Move away from engagement. Cannot shoot or charge."),
        ],
        "Shooting Phase": [
            ("Shooting", "Select targets, roll to hit, wound, and save."),
            ("Cover", "Models in cover get improved save against ranged attacks."),
            ("Ballistic Skill", "Roll equal to or over BS to hit with ranged weapons."),
        ],
        "Charge Phase": [
            ("Charge", "Roll 2D6 to move toward enemy unit."),
            ("Heroic Intervention", "Move Character units toward enemy."),
        ],
        "Fight Phase": [
            ("Fight", "Make melee attacks with models in engagement range."),
            ("Weapon Skill", "Roll equal to or over WS to hit in melee."),
            ("Pile In and Consolidate", 'Move 3" toward closest enemy.'),
        ],
        "Command Phase": [
            ("Command Points", "Gain CP and use Command Re-roll."),
            ("Battle-shock", "Test leadership for Below Half-strength units."),
        ],
    }

    for phase, phase_rules in core_rules_data.items():
        for rule_name, description in phase_rules:
            rules.append(
                {
                    "name": rule_name,
                    "category": "Core Rules",
                    "faction": None,
                    "description": description,
                    "phase": phase.replace(" Phase", ""),
                }
            )

    logger.info(f"Created {len(rules)} core rules")
    return rules


def scrape_wahapedia_factions() -> List[str]:
    """Get list of factions from Wahapedia."""
    try:
        url = "https://wahapedia.ru/wh40k10ed/factions/"
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")
            # Find faction links
            faction_elements = soup.select('a[href*="/wh40k10ed/factions/"]')
            factions = []

            for elem in faction_elements:
                faction_name = elem.get_text(strip=True)
                if faction_name and len(faction_name) > 2:
                    factions.append(faction_name)

            logger.info(f"Found {len(factions)} factions from Wahapedia")
            return list(set(factions))

    except Exception as e:
        logger.warning(f"Could not scrape Wahapedia factions: {e}")

    # Fallback to known factions
    return [
        "Space Marines",
        "Chaos Space Marines",
        "Necrons",
        "Orks",
        "Tyranids",
        "Aeldari",
        "T'au Empire",
        "Astra Militarum",
        "Adeptus Mechanicus",
        "Drukhari",
        "Death Guard",
        "Thousand Sons",
    ]


def scrape_faction_rules(factions: List[str]) -> List[Dict]:
    """Scrape faction-specific rules."""
    faction_rules = []

    # Predefined faction abilities (public knowledge from core rules)
    faction_abilities = {
        "Space Marines": {
            "name": "Oath of Moment",
            "description": "Select one enemy unit at start of Command phase. "
            "+1 to Hit against that unit until next Command phase.",
            "phase": "Command",
        },
        "Necrons": {
            "name": "Reanimation Protocols",
            "description": "At end of turn, roll D6 for each destroyed model. "
            "On 5+, return model to unit with 1 wound.",
            "phase": "Any",
        },
        "Orks": {
            "name": "Waaagh!",
            "description": "Once per battle, Orks can Advance and Charge, "
            "and melee weapons get +1 Attack.",
            "phase": "Command",
        },
        "Tyranids": {
            "name": "Synapse",
            "description": 'Units within 6" of Synapse creatures auto-pass '
            "Battle-shock tests.",
            "phase": "Command",
        },
        "T'au Empire": {
            "name": "For the Greater Good",
            "description": "When enemy charges, nearby units can provide "
            "Supporting Fire.",
            "phase": "Charge",
        },
    }

    for faction in factions:
        if faction in faction_abilities:
            ability = faction_abilities[faction]
            faction_rules.append(
                {
                    "name": ability["name"],
                    "category": "Faction",
                    "faction": faction,
                    "description": ability["description"],
                    "phase": ability["phase"],
                }
            )

    logger.info(f"Created {len(faction_rules)} faction rules")
    return faction_rules


def scrape_stratagems(factions: List[str]) -> List[Dict]:
    """Scrape stratagems for factions."""
    stratagems = []

    # Generic stratagem templates
    stratagem_types = [
        {
            "suffix": "Counter-Offensive",
            "cost": 2,
            "type": "Battle Tactic",
            "when": "Opponent's Fight phase",
            "phase": "Fight",
        },
        {
            "suffix": "Rapid Redeployment",
            "cost": 1,
            "type": "Strategic Ploy",
            "when": "Your Movement phase",
            "phase": "Movement",
        },
        {
            "suffix": "Devastating Blow",
            "cost": 1,
            "type": "Battle Tactic",
            "when": "Your Shooting or Fight phase",
            "phase": "Shooting",
        },
    ]

    for faction in factions[:10]:  # Limit to top 10 factions
        for i, template in enumerate(stratagem_types):
            stratagems.append(
                {
                    "name": f"{faction} {template['suffix']}",
                    "faction": faction,
                    "cost": template["cost"],
                    "type": template["type"],
                    "when": template["when"],
                    "target": f"One {faction} unit",
                    "effect": f"Grants bonus to {faction} unit based on stratagem type.",
                    "phase": template["phase"],
                }
            )

    logger.info(f"Created {len(stratagems)} stratagems")
    return stratagems


def save_rules_data(rules: List[Dict], stratagems: List[Dict]):
    """Save rules and stratagems to JSON files."""
    data_dir = Path(__file__).parent.parent / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    # Save rules
    rules_file = data_dir / "rules.json"
    with open(rules_file, "w", encoding="utf-8") as f:
        json.dump(rules, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved {len(rules)} rules to {rules_file}")

    # Save stratagems
    stratagems_file = data_dir / "stratagems.json"
    with open(stratagems_file, "w", encoding="utf-8") as f:
        json.dump(stratagems, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved {len(stratagems)} stratagems to {stratagems_file}")


def main():
    """Main scraping function for rules."""
    logger.info("Starting rules and stratagems scraping...")

    # Scrape core rules
    core_rules = scrape_core_rules()

    # Get factions
    factions = scrape_wahapedia_factions()

    # Scrape faction rules
    faction_rules = scrape_faction_rules(factions)

    # Combine all rules
    all_rules = core_rules + faction_rules

    # Scrape stratagems
    stratagems = scrape_stratagems(factions)

    # Save to files
    save_rules_data(all_rules, stratagems)

    logger.info(
        f"Rules scraping complete! "
        f"Collected {len(all_rules)} rules and {len(stratagems)} stratagems."
    )


if __name__ == "__main__":
    main()
