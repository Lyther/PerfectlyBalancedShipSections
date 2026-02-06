#!/usr/bin/env python3
"""
Fix Stellaris section template errors using vanilla data as reference.
Strategy:
1. Try to find a better entity that has the needed locators
2. If no better entity, map to valid locators from current entity
"""

import json
import re
import sys
from pathlib import Path
from collections import defaultdict

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Import tier calculation from generate_sections
from generate_sections import parse_notation, TIER_MULTIPLIERS, DEFAULT_BASE_POINTS
import generate_sections

SCRIPT_DIR = Path(__file__).parent
SECTION_DIR = SCRIPT_DIR.parent / "src" / "common" / "section_templates"
VANILLA_DATA_PATH = SCRIPT_DIR / "vanilla_ship_data.json"

# Valid tier names for detection
VALID_TIERS = {"COMMON", "ADVANCED", "PRO", "ULTRA", "ULTIMATE"}

# Ship base points (populated from vanilla data)
SHIP_BASE_POINTS: dict[str, int] = {}


def load_vanilla_data() -> dict:
    """Load vanilla ship data from JSON and populate SHIP_BASE_POINTS."""
    global SHIP_BASE_POINTS

    if not VANILLA_DATA_PATH.exists():
        raise FileNotFoundError(
            f"Vanilla data not found: {VANILLA_DATA_PATH}\n"
            "Run extract_vanilla_data.py first."
        )

    data = json.loads(VANILLA_DATA_PATH.read_text(encoding="utf-8"))

    # Populate SHIP_BASE_POINTS from vanilla data
    base_points_data = data.get("ship_base_points", {})
    for ship_type, info in base_points_data.items():
        if isinstance(info, dict):
            SHIP_BASE_POINTS[ship_type] = info.get("base_points", DEFAULT_BASE_POINTS)
        else:
            SHIP_BASE_POINTS[ship_type] = info

    # Also update generate_sections module's SHIP_BASE_POINTS
    generate_sections.SHIP_BASE_POINTS.update(SHIP_BASE_POINTS)

    return data


def build_entity_locator_map(vanilla_data: dict) -> dict[str, set[str]]:
    """Build entity -> valid locators mapping."""
    entity_map = {}
    for ship_type, ship_data in vanilla_data.get("ship_types", {}).items():
        for slot_name, slot_data in ship_data.get("slots", {}).items():
            for entity_name, entity_data in slot_data.get("entities", {}).items():
                locators = entity_data.get("locators", [])
                if entity_name not in entity_map:
                    entity_map[entity_name] = set()
                entity_map[entity_name].update(locators)
    return entity_map


def build_locator_entity_map(vanilla_data: dict) -> dict[str, list[str]]:
    """Build locator -> entities that have it (reverse lookup)."""
    locator_map = defaultdict(list)
    for ship_type, ship_data in vanilla_data.get("ship_types", {}).items():
        for slot_name, slot_data in ship_data.get("slots", {}).items():
            for entity_name, entity_data in slot_data.get("entities", {}).items():
                for locator in entity_data.get("locators", []):
                    if entity_name not in locator_map[locator]:
                        locator_map[locator].append(entity_name)
    return dict(locator_map)


def build_ship_slot_entities(vanilla_data: dict) -> dict[str, dict[str, list[str]]]:
    """Build ship_type -> slot -> list of entities mapping."""
    result = {}
    for ship_type, ship_data in vanilla_data.get("ship_types", {}).items():
        result[ship_type] = {}
        for slot_name, slot_data in ship_data.get("slots", {}).items():
            result[ship_type][slot_name] = list(slot_data.get("entities", {}).keys())
    return result


def get_modifier_replacements(vanilla_data: dict) -> dict[str, str | None]:
    """Get invalid -> valid modifier mappings."""
    return vanilla_data.get("modifiers", {}).get("invalid_to_valid_map", {})


def get_tech_replacements(vanilla_data: dict) -> dict[str, str]:
    """Get invalid -> valid tech mappings."""
    return vanilla_data.get("technologies", {}).get("invalid_to_valid_map", {})


def build_valid_slots(vanilla_data: dict) -> dict[str, list[str]]:
    """Build ship_type -> valid_slots mapping."""
    result = {}
    for ship_type, ship_data in vanilla_data.get("ship_types", {}).items():
        result[ship_type] = list(ship_data.get("slots", {}).keys())
    return result


def normalize_slot_name(slot: str, ship_type: str, valid_slots: dict) -> str:
    """Normalize slot names to valid vanilla values."""
    # Common slot name mappings
    slot_aliases = {
        "ship": "mid",
        "core": "mid",
        "section": "mid",
        "main": "mid",
    }

    # If slot is already valid for this ship type, keep it
    if ship_type in valid_slots and slot in valid_slots[ship_type]:
        return slot

    # Try alias mapping
    if slot in slot_aliases:
        normalized = slot_aliases[slot]
        if ship_type in valid_slots and normalized in valid_slots[ship_type]:
            return normalized

    # Fallback to first valid slot for this ship type
    if ship_type in valid_slots and valid_slots[ship_type]:
        return valid_slots[ship_type][0]

    return slot  # Return original if nothing works


def get_valid_entity_for_slot(
    ship_type: str,
    slot: str,
    ship_slot_entities: dict,
    entity_locators: dict,
) -> str | None:
    """Get a valid entity for the given ship_type and slot."""
    if ship_type not in ship_slot_entities:
        return None
    if slot not in ship_slot_entities[ship_type]:
        return None

    entities = ship_slot_entities[ship_type][slot]
    if not entities:
        return None

    # Return entity with most locators (most flexible)
    best = None
    best_count = 0
    for entity in entities:
        locs = entity_locators.get(entity, set())
        if len(locs) > best_count:
            best = entity
            best_count = len(locs)

    return best


def fix_modifiers(content: str, replacements: dict) -> str:
    """Replace invalid modifiers with valid ones or remove them."""
    for old_mod, new_mod in replacements.items():
        if new_mod is None:
            content = re.sub(
                rf"^\s*{re.escape(old_mod)}\s*=\s*[\d.\-]+\s*#?.*$\n?",
                "",
                content,
                flags=re.MULTILINE,
            )
        else:
            content = re.sub(rf"\b{re.escape(old_mod)}\b", new_mod, content)
    return content


def fix_tech_references(content: str, replacements: dict) -> str:
    """Replace invalid tech references with valid ones."""
    for old_tech, new_tech in replacements.items():
        content = content.replace(old_tech, new_tech)
    return content


def find_best_entity(
    needed_locators: set[str],
    current_entity: str,
    ship_type: str,
    slot: str,
    entity_locators: dict,
    ship_slot_entities: dict,
) -> str | None:
    """
    Find a better entity that has all needed locators.
    Prefer entities from the same ship_type and slot.
    """
    # Get candidate entities for this ship type and slot
    candidates = []
    if ship_type in ship_slot_entities and slot in ship_slot_entities[ship_type]:
        candidates = ship_slot_entities[ship_type][slot]

    # Only consider valid context entities; otherwise keep current and remap locators.
    if not candidates:
        return None

    base_pattern = current_entity.replace("_entity", "").split("_")[0]

    best_match = None
    best_score = 0

    for entity in candidates:
        locators = entity_locators.get(entity, set())
        if not locators:
            continue

        # Check how many needed locators this entity has
        matching = needed_locators & locators
        score = len(matching)

        # Bonus for similar naming
        if base_pattern in entity:
            score += 5

        # Must have all needed locators
        if matching == needed_locators and score > best_score:
            best_score = score
            best_match = entity

    return best_match if best_match != current_entity else None


def get_locator_mapping(
    needed_locators: set[str], valid_locators: set[str]
) -> dict[str, str]:
    """Create a mapping from invalid locators to valid ones."""
    mapping = {}

    if not valid_locators:
        return mapping

    valid_list = sorted(valid_locators)

    for needed in needed_locators:
        if needed in valid_locators:
            continue  # Already valid

        # Try to find similar locator
        best_match = None

        # Size-based matching
        size_map = {
            "xl_gun": ["large_gun", "extra_large", "xl_gun"],
            "extra_large": ["xl_gun", "large_gun", "extra_large"],
            "large_gun": ["large_gun", "xl_gun", "medium_gun"],
            "medium_gun": ["medium_gun", "large_gun", "small_gun"],
            "small_gun": ["small_gun", "medium_gun", "point_defence"],
            "main_body": ["root", "core", "weapon_01"],
            "weapon": ["weapon_01", "weapon_02", "root"],
        }

        # Find what size category the needed locator is
        for size_key, preferences in size_map.items():
            if size_key in needed:
                for pref in preferences:
                    for valid in valid_list:
                        if pref in valid:
                            best_match = valid
                            break
                    if best_match:
                        break
                break

        # Fallback: use first available locator
        if not best_match:
            best_match = valid_list[0]

        mapping[needed] = best_match

    return mapping


def extract_section_data(section_content: str) -> dict:
    """Extract key data from a section template block."""
    data = {}

    key_match = re.search(r'key\s*=\s*"([^"]+)"', section_content)
    if key_match:
        data["key"] = key_match.group(1)

    entity_match = re.search(r'entity\s*=\s*"([^"]+)"', section_content)
    if entity_match:
        data["entity"] = entity_match.group(1)

    ship_size_match = re.search(r"ship_size\s*=\s*(\w+)", section_content)
    if ship_size_match:
        data["ship_size"] = ship_size_match.group(1)

    slot_match = re.search(r"fits_on_slot\s*=\s*(\w+)", section_content)
    if slot_match:
        data["slot"] = slot_match.group(1)

    # Extract all locators
    locators = set()
    for loc_match in re.finditer(r'locatorname\s*=\s*"([^"]+)"', section_content):
        locators.add(loc_match.group(1))
    data["locators"] = locators

    return data


def find_default_entity(
    ship_type: str,
    slot: str,
    ship_slot_entities: dict,
    entity_locators: dict,
) -> str | None:
    """Find a default entity for unknown/invalid entity names."""
    if ship_type not in ship_slot_entities:
        return None

    # Try exact slot first, then fallback to alternatives
    slot_alternatives = [slot]
    if slot == "core":
        slot_alternatives.extend(["mid", "bow", "stern"])
    elif slot == "mid":
        slot_alternatives.extend(["core"])

    candidates = []
    for try_slot in slot_alternatives:
        if try_slot in ship_slot_entities[ship_type]:
            candidates = ship_slot_entities[ship_type][try_slot]
            if candidates:
                break

    if not candidates:
        return None

    # Prefer entity with most locators (most flexible)
    best = None
    best_count = 0
    for entity in candidates:
        locs = entity_locators.get(entity, set())
        if len(locs) > best_count:
            best = entity
            best_count = len(locs)

    return best


def build_entity_to_ship_slot(vanilla_data: dict) -> dict[str, list[tuple[str, str]]]:
    """Build entity -> [(ship_type, slot), ...] mapping."""
    result = {}
    for ship_type, ship_data in vanilla_data.get("ship_types", {}).items():
        for slot_name, slot_data in ship_data.get("slots", {}).items():
            for entity_name in slot_data.get("entities", {}).keys():
                if entity_name not in result:
                    result[entity_name] = []
                result[entity_name].append((ship_type, slot_name))
    return result


def is_entity_valid_for_context(
    entity: str,
    ship_type: str,
    slot: str,
    entity_to_ship_slot: dict,
    ship_slot_entities: dict,
) -> bool:
    """Check if entity is valid for the given ship_type/slot context."""
    if entity not in entity_to_ship_slot:
        return False  # Unknown entity

    # Check if this entity belongs to any valid context for this ship_type/slot
    valid_contexts = entity_to_ship_slot[entity]

    # Direct match
    if (ship_type, slot) in valid_contexts:
        return True

    # Check if entity is in the valid entities for this ship_type/slot
    if ship_type in ship_slot_entities:
        if slot in ship_slot_entities[ship_type]:
            if entity in ship_slot_entities[ship_type][slot]:
                return True

    return False


def fix_section(
    section_content: str,
    entity_locators: dict,
    locator_entities: dict,
    ship_slot_entities: dict,
    entity_to_ship_slot: dict,
) -> tuple[str, list[str]]:
    """Fix a single section template, returning (fixed_content, changes)."""
    changes = []
    data = extract_section_data(section_content)

    entity = data.get("entity", "")
    ship_type = data.get("ship_size", "")
    slot = data.get("slot", "mid")
    needed_locators = data.get("locators", set())

    if not entity:
        return section_content, changes

    # Strategy 0: Check if entity is valid for this ship_type/slot context
    entity_valid_context = is_entity_valid_for_context(
        entity, ship_type, slot, entity_to_ship_slot, ship_slot_entities
    )

    if not entity_valid_context:
        # Entity is from wrong ship type - must replace with correct entity
        correct_entity = get_valid_entity_for_slot(
            ship_type, slot, ship_slot_entities, entity_locators
        )
        if correct_entity:
            old_entity = entity
            pattern = rf'entity\s*=\s*"{re.escape(entity)}"'
            section_content = re.sub(
                pattern,
                f'entity = "{correct_entity}"',
                section_content,
            )
            changes.append(
                f"Fixed wrong context entity '{old_entity}' -> '{correct_entity}' (was from different ship type)"
            )
            entity = correct_entity

    # Re-check entity status after potential fix
    entity_exists = entity in entity_locators
    valid_locators = entity_locators.get(entity, set())

    # Strategy 1: If entity still doesn't exist, find a default one
    if not entity_exists:
        default_entity = find_default_entity(
            ship_type, slot, ship_slot_entities, entity_locators
        )
        if default_entity:
            section_content = re.sub(
                rf'entity\s*=\s*"{re.escape(entity)}"',
                f'entity = "{default_entity}"',
                section_content,
            )
            changes.append(f"Replaced unknown entity '{entity}' -> '{default_entity}'")
            entity = default_entity
            valid_locators = entity_locators.get(entity, set())

    if not needed_locators:
        return section_content, changes

    invalid_locators = needed_locators - valid_locators

    if not invalid_locators:
        return section_content, changes  # All locators valid

    # Strategy 2: Try to find a better entity that has all needed locators
    # But only from valid entities for this ship_type/slot!
    better_entity = find_best_entity(
        needed_locators, entity, ship_type, slot, entity_locators, ship_slot_entities
    )

    if better_entity:
        section_content = re.sub(
            rf'entity\s*=\s*"{re.escape(entity)}"',
            f'entity = "{better_entity}"',
            section_content,
        )
        changes.append(f"Changed entity '{entity}' -> '{better_entity}'")
        return section_content, changes

    # Strategy 3: Map invalid locators to valid ones
    if valid_locators:
        locator_mapping = get_locator_mapping(invalid_locators, valid_locators)

        for old_loc, new_loc in locator_mapping.items():
            section_content = re.sub(
                rf'locatorname\s*=\s*"{re.escape(old_loc)}"',
                f'locatorname = "{new_loc}"',
                section_content,
            )
            changes.append(f"Mapped locator '{old_loc}' -> '{new_loc}'")

    return section_content, changes


def fix_section_tiers(content: str) -> tuple[str, list[str]]:
    """Fix section tier names based on calculated points vs base points."""
    changes = []

    def fix_key(match):
        full_key = match.group(1)

        # Parse key: PBSS_<SHIP_TYPE>_<SLOT>_<TIER>_<NOTATION>
        # Example: PBSS_CORVETTE_MID_COMMON_S3UL1
        parts = full_key.split("_")
        if len(parts) < 5 or parts[0] != "PBSS":
            return match.group(0)

        # Find tier position (it's after PBSS, ship_type, slot)
        tier_idx = None
        for i, part in enumerate(parts):
            if part in VALID_TIERS:
                tier_idx = i
                break

        if tier_idx is None:
            return match.group(0)

        current_tier = parts[tier_idx]
        notation = "_".join(parts[tier_idx + 1 :])

        # Reconstruct ship_type from parts between PBSS and tier
        # Handle multi-word ship types like "CRISIS_CORVETTE" or "OFFSPRING_BATTLESHIP"
        ship_type_parts = parts[1 : tier_idx - 1]  # Exclude slot
        slot = parts[tier_idx - 1].lower()

        # Build ship_type by joining and lowercasing
        ship_type = "_".join(ship_type_parts).lower()

        # Skip if we can't determine ship type
        if ship_type not in SHIP_BASE_POINTS:
            # Try without the slot part
            ship_type = "_".join(parts[1:tier_idx]).lower()
            if ship_type not in SHIP_BASE_POINTS:
                return match.group(0)

        try:
            design = parse_notation(notation, ship_type)
            correct_tier = design.tier.upper()

            if correct_tier != current_tier:
                new_key = full_key.replace(f"_{current_tier}_", f"_{correct_tier}_")
                changes.append(
                    f"Tier fix: {full_key} -> {new_key} ({design.total_points}pts, {design.total_points / SHIP_BASE_POINTS.get(ship_type, 12):.1f}x base)"
                )
                return f'key = "{new_key}"'
        except Exception:
            pass

        return match.group(0)

    new_content = re.sub(r'key\s*=\s*"(PBSS_[^"]+)"', fix_key, content)
    return new_content, changes


def fix_slot_names(content: str, valid_slots: dict) -> tuple[str, list[str]]:
    """Fix invalid slot names in sections."""
    changes = []
    lines = content.split("\n")
    result_lines = []

    i = 0
    while i < len(lines):
        line = lines[i]

        if "ship_section_template" in line and "=" in line and "{" in line:
            # Extract section to find ship_size
            brace_count = line.count("{") - line.count("}")
            section_lines = [line]
            section_start = i
            i += 1

            while i < len(lines) and brace_count > 0:
                brace_count += lines[i].count("{") - lines[i].count("}")
                section_lines.append(lines[i])
                i += 1

            section_content = "\n".join(section_lines)

            # Extract ship_size and slot
            ship_match = re.search(r"ship_size\s*=\s*(\w+)", section_content)
            slot_match = re.search(r"fits_on_slot\s*=\s*(\w+)", section_content)
            key_match = re.search(r'key\s*=\s*"([^"]+)"', section_content)

            if ship_match and slot_match:
                ship_type = ship_match.group(1)
                current_slot = slot_match.group(1)
                key = key_match.group(1) if key_match else "unknown"

                normalized = normalize_slot_name(current_slot, ship_type, valid_slots)
                if normalized != current_slot:
                    # Replace slot in section
                    new_section = re.sub(
                        rf"fits_on_slot\s*=\s*{re.escape(current_slot)}",
                        f"fits_on_slot = {normalized}",
                        section_content,
                    )
                    changes.append(
                        f"Fixed slot '{current_slot}' -> '{normalized}' in '{key}'"
                    )
                    result_lines.extend(new_section.split("\n"))
                else:
                    result_lines.extend(section_lines)
            else:
                result_lines.extend(section_lines)
        else:
            result_lines.append(line)
            i += 1

    return "\n".join(result_lines), changes


def process_file(
    filepath: Path,
    entity_locators: dict,
    locator_entities: dict,
    ship_slot_entities: dict,
    entity_to_ship_slot: dict,
    modifier_replacements: dict,
    tech_replacements: dict,
    valid_slots: dict,
) -> tuple[bool, list[str]]:
    """Process a single file."""
    content = filepath.read_text(encoding="utf-8-sig")
    original = content
    all_changes = []

    # Fix section tiers first (based on new multiplier calculation)
    new_content, tier_changes = fix_section_tiers(content)
    if tier_changes:
        all_changes.extend(tier_changes)
        content = new_content

    # Fix slot names
    new_content, slot_changes = fix_slot_names(content, valid_slots)
    if slot_changes:
        all_changes.extend(slot_changes)
        content = new_content

    # Fix modifiers
    new_content = fix_modifiers(content, modifier_replacements)
    if new_content != content:
        all_changes.append("Fixed invalid modifiers")
        content = new_content

    # Fix tech references
    new_content = fix_tech_references(content, tech_replacements)
    if new_content != content:
        all_changes.append("Fixed invalid tech references")
        content = new_content

    # Process each section template
    lines = content.split("\n")
    result_lines = []
    i = 0

    while i < len(lines):
        line = lines[i]

        if "ship_section_template" in line and "=" in line and "{" in line:
            # Extract full section block
            brace_count = line.count("{") - line.count("}")
            section_lines = [line]
            i += 1

            while i < len(lines) and brace_count > 0:
                line = lines[i]
                brace_count += line.count("{") - line.count("}")
                section_lines.append(line)
                i += 1

            section_content = "\n".join(section_lines)
            fixed_content, changes = fix_section(
                section_content,
                entity_locators,
                locator_entities,
                ship_slot_entities,
                entity_to_ship_slot,
            )

            result_lines.append(fixed_content)
            all_changes.extend(changes)
        else:
            result_lines.append(line)
            i += 1

    content = "\n".join(result_lines)

    if content != original:
        filepath.write_text(content, encoding="utf-8")
        return True, all_changes
    return False, all_changes


def main():
    print("Stellaris Section Template Error Fixer")
    print("=" * 50)

    try:
        vanilla_data = load_vanilla_data()
        print(f"Loaded vanilla data from: {VANILLA_DATA_PATH.name}")
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        return 1

    # Build lookup tables
    entity_locators = build_entity_locator_map(vanilla_data)
    locator_entities = build_locator_entity_map(vanilla_data)
    ship_slot_entities = build_ship_slot_entities(vanilla_data)
    entity_to_ship_slot = build_entity_to_ship_slot(vanilla_data)
    valid_slots = build_valid_slots(vanilla_data)
    modifier_replacements = get_modifier_replacements(vanilla_data)
    tech_replacements = get_tech_replacements(vanilla_data)

    print(f"  Entity/locator mappings: {len(entity_locators)}")
    print(f"  Ship type/slot mappings: {len(ship_slot_entities)}")
    print(f"  Entity context mappings: {len(entity_to_ship_slot)}")
    print(f"  Valid slots mappings: {len(valid_slots)}")

    if not SECTION_DIR.exists():
        print(f"ERROR: Section directory not found: {SECTION_DIR}")
        return 1

    files = list(SECTION_DIR.glob("*.txt"))
    print(f"\nProcessing {len(files)} section files...\n")

    total_modified = 0
    for filepath in sorted(files):
        modified, changes = process_file(
            filepath,
            entity_locators,
            locator_entities,
            ship_slot_entities,
            entity_to_ship_slot,
            modifier_replacements,
            tech_replacements,
            valid_slots,
        )
        if modified:
            total_modified += 1
            print(f"✓ {filepath.name}")
            for change in changes[:10]:  # Limit output
                print(f"  - {change}")
            if len(changes) > 10:
                print(f"  ... and {len(changes) - 10} more changes")

    print(f"\n{'=' * 50}")
    print(f"Modified {total_modified} files")

    return 0


if __name__ == "__main__":
    exit(main())
