#!/usr/bin/env python3
"""
Extract vanilla Stellaris section template data into a structured JSON file.
Hierarchy: Ship Type -> Ship Sections -> Section Entities -> Entity Locators
"""

import json
import re
from pathlib import Path
from collections import defaultdict

# Paths
STELLARIS_PATH = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Stellaris")
SECTION_TEMPLATES_PATH = STELLARIS_PATH / "common" / "section_templates"
OUTPUT_PATH = Path(__file__).parent / "vanilla_ship_data.json"


def extract_blocks(content: str, block_type: str) -> list[str]:
    """Extract all blocks of a given type using brace counting."""
    blocks = []
    pattern = rf"{block_type}\s*=\s*\{{"

    for match in re.finditer(pattern, content):
        start = match.end() - 1  # Start at the opening brace
        brace_count = 0
        end = start

        for i, char in enumerate(content[start:], start):
            if char == "{":
                brace_count += 1
            elif char == "}":
                brace_count -= 1
                if brace_count == 0:
                    end = i + 1
                    break

        if end > start:
            blocks.append(content[start:end])

    return blocks


def parse_section_template(content: str) -> list[dict]:
    """Parse section template file and extract all ship_section_template blocks."""
    sections = []

    # Extract all ship_section_template blocks with proper brace counting
    blocks = extract_blocks(content, "ship_section_template")

    for block in blocks:
        section = {}

        # Extract key
        key_match = re.search(r'key\s*=\s*"([^"]+)"', block)
        if key_match:
            section["key"] = key_match.group(1)

        # Extract ship_size
        ship_size_match = re.search(r"ship_size\s*=\s*(\w+)", block)
        if ship_size_match:
            section["ship_size"] = ship_size_match.group(1)

        # Extract fits_on_slot (handles both quoted and unquoted values)
        slot_match = re.search(r'fits_on_slot\s*=\s*"?(\w+)"?', block)
        if slot_match:
            section["slot"] = slot_match.group(1)

        # Extract entity
        entity_match = re.search(r'entity\s*=\s*"([^"]+)"', block)
        if entity_match:
            section["entity"] = entity_match.group(1)

        # Extract all locatornames from component_slots
        locators = []
        for loc_match in re.finditer(r'locatorname\s*=\s*"([^"]+)"', block):
            loc = loc_match.group(1)
            if loc not in locators:
                locators.append(loc)
        section["locators"] = locators

        # Extract component slot templates (for reference)
        templates = []
        for tmpl_match in re.finditer(r'template\s*=\s*"([^"]+)"', block):
            tmpl = tmpl_match.group(1)
            if tmpl not in templates:
                templates.append(tmpl)
        section["templates"] = templates

        if section.get("key"):
            sections.append(section)

    return sections


def build_hierarchy(all_sections: list[dict]) -> dict:
    """Build the ship type -> section -> entity -> locator hierarchy."""
    hierarchy = {}

    for section in all_sections:
        ship_type = section.get("ship_size", "unknown")
        slot = section.get("slot", "mid")
        entity = section.get("entity", "")
        locators = section.get("locators", [])
        key = section.get("key", "")
        templates = section.get("templates", [])

        if not entity:
            continue

        # Initialize hierarchy levels
        if ship_type not in hierarchy:
            hierarchy[ship_type] = {"slots": {}, "description": ""}

        if slot not in hierarchy[ship_type]["slots"]:
            hierarchy[ship_type]["slots"][slot] = {"entities": {}, "section_keys": []}

        # Add section key for reference
        if key and key not in hierarchy[ship_type]["slots"][slot]["section_keys"]:
            hierarchy[ship_type]["slots"][slot]["section_keys"].append(key)

        # Entity with its locators
        if entity not in hierarchy[ship_type]["slots"][slot]["entities"]:
            hierarchy[ship_type]["slots"][slot]["entities"][entity] = {
                "locators": [],
                "templates": [],
            }

        # Merge locators (unique)
        existing_locators = hierarchy[ship_type]["slots"][slot]["entities"][entity][
            "locators"
        ]
        for loc in locators:
            if loc not in existing_locators:
                existing_locators.append(loc)

        # Merge templates (unique)
        existing_templates = hierarchy[ship_type]["slots"][slot]["entities"][entity][
            "templates"
        ]
        for tmpl in templates:
            if tmpl not in existing_templates:
                existing_templates.append(tmpl)

    return hierarchy


def extract_modifiers() -> dict:
    """Extract valid ship modifiers from the game."""
    # These are the most common valid ship section modifiers
    return {
        "valid_ship_modifiers": [
            "ship_weapon_damage",
            "ship_weapon_range_mult",
            "ship_fire_rate_mult",
            "ship_accuracy_add",
            "ship_tracking_add",
            "ship_hull_add",
            "ship_hull_mult",
            "ship_armor_add",
            "ship_armor_mult",
            "ship_shield_add",
            "ship_shield_mult",
            "ship_evasion_add",
            "ship_evasion_mult",
            "ship_speed_mult",
            "ship_hull_regen_add_perc",
            "ship_armor_regen_add_perc",
            "ship_shield_regen_add_perc",
            "ship_sensor_range_add",
            "ship_hyperlane_range_add",
            "ship_repair_hull_mult",
            "ship_repair_armor_mult",
        ],
        "invalid_to_valid_map": {
            "ship_weapon_damage_mult": "ship_weapon_damage",
            "fleet_command_limit_add": None,
            "ship_repair_mult": "ship_repair_hull_mult",
            "sensor_range_mult": "ship_sensor_range_add",
        },
    }


def extract_technologies() -> dict:
    """Extract valid technology references."""
    return {
        "invalid_to_valid_map": {
            "tech_railguns_1": "tech_mass_drivers_2",
            "tech_railguns_2": "tech_mass_drivers_3",
            "tech_railguns_3": "tech_mass_drivers_4",
        },
        "common_prerequisites": [
            "tech_corvettes",
            "tech_destroyers",
            "tech_cruisers",
            "tech_battleships",
            "tech_titans",
            "tech_colossus",
            "tech_juggernaut",
            "tech_lasers_1",
            "tech_lasers_2",
            "tech_lasers_3",
            "tech_mass_drivers_1",
            "tech_mass_drivers_2",
            "tech_mass_drivers_3",
            "tech_mass_drivers_4",
            "tech_mass_drivers_5",
            "tech_torpedoes_1",
            "tech_torpedoes_2",
            "tech_torpedoes_3",
            "tech_energy_torpedoes_1",
            "tech_energy_torpedoes_2",
            "tech_strike_craft_1",
            "tech_strike_craft_2",
            "tech_strike_craft_3",
            "tech_plasma_1",
            "tech_plasma_2",
            "tech_plasma_3",
            "tech_disruptors_1",
            "tech_disruptors_2",
            "tech_disruptors_3",
            "tech_nanocomposite_materials",
            "tech_bio_reactor",
            "tech_hive_node",
        ],
    }


def main():
    print("Extracting vanilla Stellaris ship data...")
    print(f"Source: {SECTION_TEMPLATES_PATH}")

    if not SECTION_TEMPLATES_PATH.exists():
        print(f"ERROR: Path not found: {SECTION_TEMPLATES_PATH}")
        return 1

    all_sections = []
    file_count = 0

    # Parse all section template files
    for filepath in sorted(SECTION_TEMPLATES_PATH.glob("*.txt")):
        content = filepath.read_text(encoding="utf-8-sig")
        sections = parse_section_template(content)
        all_sections.extend(sections)
        file_count += 1
        print(f"  Parsed: {filepath.name} ({len(sections)} sections)")

    print(f"\nTotal: {file_count} files, {len(all_sections)} sections")

    # Build hierarchy
    hierarchy = build_hierarchy(all_sections)

    # Build final output
    output = {
        "_metadata": {
            "description": "Vanilla Stellaris ship section data extracted from game files",
            "source": str(SECTION_TEMPLATES_PATH),
            "hierarchy": "ship_type -> slot -> entity -> locators",
        },
        "ship_types": hierarchy,
        "modifiers": extract_modifiers(),
        "technologies": extract_technologies(),
    }

    # Write JSON
    OUTPUT_PATH.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(f"\nOutput written to: {OUTPUT_PATH}")
    print(f"Ship types found: {len(hierarchy)}")

    return 0


if __name__ == "__main__":
    exit(main())
