#!/usr/bin/env python3
"""
Validate mod section templates against vanilla Stellaris data.
Validates the full hierarchy: Ship Type -> Slot -> Entity -> Locators
Reports issues without modifying files.
"""

import json
import re
from pathlib import Path
from dataclasses import dataclass, field

SCRIPT_DIR = Path(__file__).parent
SECTION_DIR = SCRIPT_DIR.parent / "src" / "common" / "section_templates"
VANILLA_DATA_PATH = SCRIPT_DIR / "vanilla_ship_data.json"


@dataclass
class ValidationIssue:
    file: str
    line: int
    issue_type: str
    message: str
    severity: str = "error"  # error, warning, info


@dataclass
class ValidationResult:
    issues: list[ValidationIssue] = field(default_factory=list)

    def add(
        self,
        file: str,
        line: int,
        issue_type: str,
        message: str,
        severity: str = "error",
    ):
        self.issues.append(ValidationIssue(file, line, issue_type, message, severity))

    @property
    def errors(self) -> list[ValidationIssue]:
        return [i for i in self.issues if i.severity == "error"]

    @property
    def warnings(self) -> list[ValidationIssue]:
        return [i for i in self.issues if i.severity == "warning"]


def load_vanilla_data() -> dict:
    """Load vanilla ship data from JSON."""
    if not VANILLA_DATA_PATH.exists():
        raise FileNotFoundError(f"Vanilla data not found: {VANILLA_DATA_PATH}")
    return json.loads(VANILLA_DATA_PATH.read_text(encoding="utf-8"))


def build_hierarchy_lookups(vanilla_data: dict) -> dict:
    """
    Build comprehensive lookup tables from vanilla data.

    Returns dict with:
    - ship_types: set of valid ship types
    - ship_slots: {ship_type: [valid_slots]}
    - slot_entities: {ship_type: {slot: [valid_entities]}}
    - entity_locators: {entity: [valid_locators]}
    - entity_to_ship_slot: {entity: [(ship_type, slot), ...]}
    """
    lookups = {
        "ship_types": set(),
        "ship_slots": {},
        "slot_entities": {},
        "entity_locators": {},
        "entity_to_ship_slot": {},
        "valid_modifiers": set(),
        "invalid_modifiers": {},
        "invalid_techs": set(),
    }

    for ship_type, ship_data in vanilla_data.get("ship_types", {}).items():
        lookups["ship_types"].add(ship_type)
        lookups["ship_slots"][ship_type] = []
        lookups["slot_entities"][ship_type] = {}

        for slot_name, slot_data in ship_data.get("slots", {}).items():
            lookups["ship_slots"][ship_type].append(slot_name)
            lookups["slot_entities"][ship_type][slot_name] = []

            for entity_name, entity_data in slot_data.get("entities", {}).items():
                lookups["slot_entities"][ship_type][slot_name].append(entity_name)

                # Entity locators (merge if entity appears in multiple places)
                if entity_name not in lookups["entity_locators"]:
                    lookups["entity_locators"][entity_name] = set()
                lookups["entity_locators"][entity_name].update(
                    entity_data.get("locators", [])
                )

                # Track which ship_type/slot this entity belongs to
                if entity_name not in lookups["entity_to_ship_slot"]:
                    lookups["entity_to_ship_slot"][entity_name] = []
                lookups["entity_to_ship_slot"][entity_name].append(
                    (ship_type, slot_name)
                )

    # Modifiers
    lookups["valid_modifiers"] = set(
        vanilla_data.get("modifiers", {}).get("valid_ship_modifiers", [])
    )
    lookups["invalid_modifiers"] = vanilla_data.get("modifiers", {}).get(
        "invalid_to_valid_map", {}
    )

    # Technologies
    lookups["invalid_techs"] = set(
        vanilla_data.get("technologies", {}).get("invalid_to_valid_map", {}).keys()
    )

    return lookups


def extract_sections(content: str) -> list[tuple[int, str, dict]]:
    """Extract section blocks with their starting line numbers."""
    sections = []
    lines = content.split("\n")

    i = 0
    while i < len(lines):
        line = lines[i]
        if "ship_section_template" in line and "=" in line and "{" in line:
            start_line = i + 1  # 1-indexed
            brace_count = line.count("{") - line.count("}")
            section_lines = [line]
            i += 1

            while i < len(lines) and brace_count > 0:
                line = lines[i]
                brace_count += line.count("{") - line.count("}")
                section_lines.append(line)
                i += 1

            block = "\n".join(section_lines)

            # Parse section data
            section_data = {}
            key_match = re.search(r'key\s*=\s*"([^"]+)"', block)
            if key_match:
                section_data["key"] = key_match.group(1)

            entity_match = re.search(r'entity\s*=\s*"([^"]+)"', block)
            if entity_match:
                section_data["entity"] = entity_match.group(1)

            ship_size_match = re.search(r"ship_size\s*=\s*(\w+)", block)
            if ship_size_match:
                section_data["ship_size"] = ship_size_match.group(1)

            slot_match = re.search(r"fits_on_slot\s*=\s*(\w+)", block)
            if slot_match:
                section_data["slot"] = slot_match.group(1)

            # Extract locators with their line numbers
            locators = []
            for j, section_line in enumerate(section_lines):
                loc_match = re.search(r'locatorname\s*=\s*"([^"]+)"', section_line)
                if loc_match:
                    locators.append((start_line + j, loc_match.group(1)))
            section_data["locators"] = locators

            # Extract modifiers with line numbers
            modifiers = []
            for j, section_line in enumerate(section_lines):
                mod_match = re.search(r"(\w+)\s*=\s*[\d.\-]+", section_line)
                if mod_match and "ship_" in mod_match.group(1):
                    modifiers.append((start_line + j, mod_match.group(1)))
            section_data["modifiers"] = modifiers

            # Extract tech prereqs with line numbers
            techs = []
            for j, section_line in enumerate(section_lines):
                for tech_match in re.finditer(r'"(tech_\w+)"', section_line):
                    techs.append((start_line + j, tech_match.group(1)))
            section_data["techs"] = techs

            sections.append((start_line, block, section_data))
        else:
            i += 1

    return sections


def validate_file(filepath: Path, lookups: dict) -> ValidationResult:
    """Validate a single file using full hierarchy."""
    result = ValidationResult()
    content = filepath.read_text(encoding="utf-8-sig")
    filename = filepath.name

    sections = extract_sections(content)

    for start_line, block, data in sections:
        key = data.get("key", "unknown")
        entity = data.get("entity", "")
        ship_size = data.get("ship_size", "")
        slot = data.get("slot", "")

        # === HIERARCHY VALIDATION ===

        # 1. Check if ship_size is valid
        if ship_size and ship_size not in lookups["ship_types"]:
            result.add(
                filename,
                start_line,
                "unknown_ship_type",
                f"Section '{key}': Ship type '{ship_size}' not found in vanilla data",
                severity="warning",
            )

        # 2. Check if slot is valid for this ship_size
        if ship_size and slot:
            valid_slots = lookups["ship_slots"].get(ship_size, [])
            if valid_slots and slot not in valid_slots:
                result.add(
                    filename,
                    start_line,
                    "invalid_slot",
                    f"Section '{key}': Slot '{slot}' not valid for ship '{ship_size}'. "
                    f"Valid slots: {valid_slots}",
                    severity="warning",
                )

        # 3. Check if entity is valid for this ship_size/slot combination
        if entity and ship_size and slot:
            valid_entities = lookups["slot_entities"].get(ship_size, {}).get(slot, [])
            if valid_entities and entity not in valid_entities:
                # Check if entity exists at all
                if entity in lookups["entity_locators"]:
                    # Entity exists but for different ship/slot
                    expected = lookups["entity_to_ship_slot"].get(entity, [])
                    result.add(
                        filename,
                        start_line,
                        "wrong_entity_context",
                        f"Section '{key}': Entity '{entity}' not valid for {ship_size}/{slot}. "
                        f"This entity belongs to: {expected}",
                        severity="warning",
                    )
                else:
                    result.add(
                        filename,
                        start_line,
                        "unknown_entity",
                        f"Section '{key}': Entity '{entity}' not found in vanilla data",
                        severity="warning",
                    )
        elif entity and entity not in lookups["entity_locators"]:
            result.add(
                filename,
                start_line,
                "unknown_entity",
                f"Section '{key}': Entity '{entity}' not found in vanilla data",
                severity="warning",
            )

        # 4. Validate locators for the entity
        if entity and entity in lookups["entity_locators"]:
            valid_locs = lookups["entity_locators"][entity]
            for line_num, locator in data.get("locators", []):
                if valid_locs and locator not in valid_locs:
                    result.add(
                        filename,
                        line_num,
                        "invalid_locator",
                        f"Section '{key}': Entity '{entity}' has no locator '{locator}'. "
                        f"Valid: {sorted(valid_locs)}",
                    )

        # === MODIFIER VALIDATION ===
        for line_num, modifier in data.get("modifiers", []):
            if modifier in lookups["invalid_modifiers"]:
                replacement = lookups["invalid_modifiers"][modifier]
                if replacement:
                    result.add(
                        filename,
                        line_num,
                        "invalid_modifier",
                        f"Section '{key}': Invalid modifier '{modifier}', use '{replacement}'",
                    )
                else:
                    result.add(
                        filename,
                        line_num,
                        "invalid_modifier",
                        f"Section '{key}': Invalid modifier '{modifier}' (remove it)",
                    )

        # === TECH VALIDATION ===
        for line_num, tech in data.get("techs", []):
            if tech in lookups["invalid_techs"]:
                result.add(
                    filename,
                    line_num,
                    "invalid_tech",
                    f"Section '{key}': Invalid technology '{tech}'",
                )

    return result


def print_hierarchy_summary(lookups: dict):
    """Print a summary of the hierarchy data."""
    print(f"\nHierarchy Summary:")
    print(f"  Ship types: {len(lookups['ship_types'])}")
    print(f"  Total entities: {len(lookups['entity_locators'])}")

    # Count entities per ship type
    entity_counts = {}
    for ship_type, slots in lookups["slot_entities"].items():
        count = sum(len(entities) for entities in slots.values())
        if count > 0:
            entity_counts[ship_type] = count

    print(f"  Ship types with entities: {len(entity_counts)}")


def main():
    print("Stellaris Section Template Validator")
    print("=" * 50)

    # Load vanilla data
    try:
        vanilla_data = load_vanilla_data()
        print(f"Loaded vanilla data from: {VANILLA_DATA_PATH.name}")
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        return 1

    lookups = build_hierarchy_lookups(vanilla_data)
    print(f"  Ship types: {len(lookups['ship_types'])}")
    print(f"  Entity mappings: {len(lookups['entity_locators'])}")

    if not SECTION_DIR.exists():
        print(f"ERROR: Section directory not found: {SECTION_DIR}")
        return 1

    files = list(SECTION_DIR.glob("*.txt"))
    print(f"\nValidating {len(files)} section files...\n")

    total_errors = 0
    total_warnings = 0

    for filepath in sorted(files):
        result = validate_file(filepath, lookups)

        if result.errors or result.warnings:
            print(f"📄 {filepath.name}")

            for issue in result.errors:
                print(f"  ❌ Line {issue.line}: [{issue.issue_type}] {issue.message}")
                total_errors += 1

            for issue in result.warnings:
                print(f"  ⚠️  Line {issue.line}: [{issue.issue_type}] {issue.message}")
                total_warnings += 1

            print()

    print("=" * 50)
    if total_errors == 0 and total_warnings == 0:
        print("✅ All files valid!")
    else:
        print(f"Found {total_errors} errors, {total_warnings} warnings")

    return 1 if total_errors > 0 else 0


if __name__ == "__main__":
    exit(main())
