#! /usr/bin/env python3
"""
Stellaris Section Generator - CLI-Based Design System

Usage:
    python generate_sections.py design battleship bow T1UL1 X1UL3 L2UL3 ...
    python generate_sections.py info battleship

Notation:
    Weapons: T=Titan, X=XL, L=Large, M=Medium, S=Small, PD=PointDefense, HB=Hangar, G=Guided
    Utility: UL=LargeUtility, US=SmallUtility, AUX=Auxiliary
    Example: T1UL1 = 1 Titan + 1 Large Utility = 16+4 = 20 pts (Common tier)
             T2X1UL2 = 2 Titan + 1 XL + 2 Large Utility = 32+8+8 = 48 pts (Ultimate tier)

Point System:
    S/PD = 1, M/G = 2, L/HB = 4, X = 8, T = 16
    UL = 4, US = 1, AUX = ship_aux_cost (varies by ship size)

Tier Auto-Categorization (by total points):
    Common: 0-24, Advanced: 25-32, Pro: 33-40, Ultra: 41-52, Ultimate: 53+
"""

import json
import re
from dataclasses import dataclass
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
VANILLA_DATA_PATH = SCRIPT_DIR / "vanilla_ship_data.json"

# Point costs
WEAPON_COSTS = {
    "S": 1,
    "PD": 1,
    "M": 2,
    "G": 2,
    "L": 4,
    "HB": 4,
    "X": 8,
    "T": 16,
    "W": 0,
}
UTILITY_COSTS = {"UL": 4, "US": 1}

# Ship aux costs
SHIP_AUX_COST = {
    "corvette": 1,
    "frigate": 1,
    "destroyer": 2,
    "cruiser": 4,
    "battleship": 8,
    "titan": 16,
    "juggernaut": 16,
    "colossus": 16,
    "star_eater": 32,
}

# Tier thresholds (min, max points)
TIER_THRESHOLDS = [
    ("common", 0, 24),
    ("advanced", 25, 32),
    ("pro", 33, 40),
    ("ultra", 41, 52),
    ("ultimate", 53, 999),
]

TIER_COST_MULT = {
    "common": 1.0,
    "advanced": 1.1,
    "pro": 1.25,
    "ultra": 1.4,
    "ultimate": 1.6,
}

# Weapon type -> template mapping
TEMPLATES = {
    "S": "small_turret",
    "PD": "point_defence_turret",
    "M": "medium_turret",
    "G": "medium_missile_turret",
    "L": "large_turret",
    "HB": "large_strike_craft",
    "X": "invisible_extra_large_fixed",
    "T": "invisible_titanic_fixed",
    "W": "invisible_planet_killer_fixed",
}

# Weapon type -> locator prefix mapping
LOCATOR_PREFIX = {
    "S": "small_gun",
    "PD": "small_gun",
    "M": "medium_gun",
    "G": "medium_gun",
    "L": "large_gun",
    "HB": "strike_craft_locator",
    "X": "xl_gun",
    "T": "xl_gun",
    "W": "core",
}


@dataclass
class ParsedDesign:
    """Parsed design notation."""

    notation: str
    weapons: dict  # {"T": 1, "X": 2, ...}
    large_utility: int
    small_utility: int
    aux: int
    total_points: int
    tier: str


def parse_notation(notation: str, ship_type: str = "battleship") -> ParsedDesign:
    """Parse design notation like T1UL1, X1L2UL3AUX2."""
    weapons = {}
    large_utility = 0
    small_utility = 0
    aux = 0

    # First remove utility patterns to avoid false matches (UL contains L, US contains S)
    work = notation

    # Parse utility: UL3, US2, AUX2 (must be done first!)
    ul_match = re.search(r"UL(\d+)", work)
    if ul_match:
        large_utility = int(ul_match.group(1))
        work = work.replace(ul_match.group(0), "")

    us_match = re.search(r"US(\d+)", work)
    if us_match:
        small_utility = int(us_match.group(1))
        work = work.replace(us_match.group(0), "")

    aux_match = re.search(r"AUX(\d+)", work)
    if aux_match:
        aux = int(aux_match.group(1))
        work = work.replace(aux_match.group(0), "")

    # Now parse weapons from remaining string: T1, X2, L3, M4, S2, PD2, HB1, G1
    for match in re.finditer(r"(PD|HB|T|X|L|M|S|G|W)(\d+)", work):
        weapon_type, count = match.groups()
        weapons[weapon_type] = int(count)

    # Calculate points
    weapon_pts = sum(WEAPON_COSTS.get(w, 0) * c for w, c in weapons.items())
    utility_pts = (
        large_utility * UTILITY_COSTS["UL"] + small_utility * UTILITY_COSTS["US"]
    )
    aux_cost = SHIP_AUX_COST.get(ship_type, 4)
    aux_pts = aux * aux_cost
    total_points = weapon_pts + utility_pts + aux_pts

    # Determine tier
    tier = "common"
    for tier_name, min_pts, max_pts in TIER_THRESHOLDS:
        if min_pts <= total_points <= max_pts:
            tier = tier_name
            break

    return ParsedDesign(
        notation=notation,
        weapons=weapons,
        large_utility=large_utility,
        small_utility=small_utility,
        aux=aux,
        total_points=total_points,
        tier=tier,
    )


def load_vanilla_data() -> dict:
    """Load vanilla ship data."""
    if not VANILLA_DATA_PATH.exists():
        print(
            f"ERROR: {VANILLA_DATA_PATH} not found. Run extract_vanilla_data.py first."
        )
        return {}
    return json.loads(VANILLA_DATA_PATH.read_text(encoding="utf-8"))


def find_entity_for_design(
    vanilla_data: dict, ship_type: str, slot: str, weapons: dict
) -> tuple:
    """Find best entity for the given weapon configuration. Returns (entity_name, locator_map).

    Aggressive mode: If no perfect match, use any available locator for all weapon types.
    This allows "Perfectly Balanced" designs like corvettes with Large guns.
    """
    ship_data = vanilla_data.get("ship_types", {}).get(ship_type, {})
    slot_data = ship_data.get("slots", {}).get(slot, {})
    entities = slot_data.get("entities", {})

    if not entities:
        return None, {}

    best_entity = None
    best_score = -1
    best_locators = {}
    fallback_entity = None
    fallback_locators = {}

    for entity_name, entity_data in entities.items():
        locators = entity_data.get("locators", [])
        templates = entity_data.get("templates", [])

        # Track entity with most locators as fallback
        if not fallback_entity or len(locators) > len(fallback_locators.get("all", [])):
            fallback_entity = entity_name
            # Use first locator as universal fallback
            fallback_loc = locators[0] if locators else "root"
            fallback_locators = {
                "all": locators,
                "large_gun": [fallback_loc],
                "medium_gun": [fallback_loc],
                "small_gun": locators if locators else [fallback_loc],
                "xl_gun": [fallback_loc],
                "strike_craft": [fallback_loc],
                "planet_killer": [fallback_loc],
            }

        # Check for universal locator (turret_01, weapon_01, etc.) - used by organic/special ships
        # Also treat planet_killer locators as universal for colossus-type ships
        universal_loc = None
        for loc in locators:
            if (
                loc in ("turret_01", "weapon_01", "weapon_02", "root", "core")
                or "turret_" in loc
                or "planet_killer" in loc
            ):
                universal_loc = loc
                break

        if universal_loc:
            # Universal locator - can support any weapon, use it for everything
            best_entity = entity_name
            best_locators = {
                "large_gun": [universal_loc],
                "medium_gun": [universal_loc],
                "small_gun": [universal_loc],
                "xl_gun": [universal_loc],
                "strike_craft": [universal_loc],
                "planet_killer": [universal_loc],
            }
            return best_entity, best_locators

        # Count available locators by type
        loc_counts = {
            "large_gun": len([l for l in locators if "large_gun" in l]),
            "medium_gun": len([l for l in locators if "medium_gun" in l]),
            "small_gun": len([l for l in locators if "small_gun" in l]),
            "xl_gun": len([l for l in locators if "xl_gun" in l]),
            "strike_craft": len([l for l in locators if "strike_craft" in l]),
            "planet_killer": len(
                [l for l in locators if "planet_killer" in l or l in ("core", "root")]
            ),
        }

        # Check if entity can support the weapons
        score = 0
        can_support = True

        # Map weapon types to locator types
        weapon_to_loc = {
            "L": "large_gun",
            "M": "medium_gun",
            "S": "small_gun",
            "PD": "small_gun",
            "G": "medium_gun",
            "X": "xl_gun",
            "T": "xl_gun",
            "HB": "strike_craft",
            "W": "planet_killer",
        }

        for weapon_type, count in weapons.items():
            loc_type = weapon_to_loc.get(weapon_type)
            if loc_type:
                available = loc_counts.get(loc_type, 0)
                if available >= count:
                    score += count * 10  # Bonus for exact match
                elif available > 0:
                    score += available  # Partial match
                else:
                    can_support = False

        if can_support and score > best_score:
            best_score = score
            best_entity = entity_name
            best_locators = {
                "large_gun": [l for l in locators if "large_gun" in l],
                "medium_gun": [l for l in locators if "medium_gun" in l],
                "small_gun": [l for l in locators if "small_gun" in l],
                "xl_gun": [l for l in locators if "xl_gun" in l],
                "strike_craft": [l for l in locators if "strike_craft" in l],
                "planet_killer": [
                    l for l in locators if "planet_killer" in l or l in ("core", "root")
                ],
            }

    # AGGRESSIVE MODE: If no perfect match found, use fallback entity with any locator
    if not best_entity and fallback_entity:
        return fallback_entity, fallback_locators

    return best_entity, best_locators


def generate_section_template(
    key: str,
    ship_type: str,
    slot: str,
    entity: str,
    design: ParsedDesign,
    locator_map: dict,
) -> str:
    """Generate a single section template string."""
    lines = [
        "ship_section_template = {",
        f'\tkey = "{key}"',
        f"\tship_size = {ship_type}",
        f"\tfits_on_slot = {slot}",
        "\tshould_draw_components = yes",
        f'\tentity = "{entity}"',
    ]

    # Icon
    icon_map = {
        "bow": "GFX_ship_part_core_bow",
        "mid": "GFX_ship_part_core_mid",
        "stern": "GFX_ship_part_core_stern",
    }
    lines.append(f'\ticon = "{icon_map.get(slot, "GFX_ship_part_core_mid")}"')

    # AI tags based on weapons
    ai_tags = []
    if design.weapons.get("HB", 0) > 0:
        ai_tags.append("carrier")
    if (
        design.weapons.get("T", 0) > 0
        or design.weapons.get("X", 0) > 0
        or design.weapons.get("L", 0) > 0
    ):
        ai_tags.append("artillery")
    if design.weapons.get("M", 0) > 0 or design.weapons.get("S", 0) > 0:
        ai_tags.append("gunship")
    if ai_tags:
        lines.append(f'\tai_tags = {{ {" ".join(ai_tags)} }}')

    # Player only
    lines.append("\tai_weight = {")
    lines.append("\t\tfactor = 0")
    lines.append("\t}")

    # Component slots
    weapon_to_loc_type = {
        "L": "large_gun",
        "M": "medium_gun",
        "S": "small_gun",
        "PD": "small_gun",
        "G": "medium_gun",
        "X": "xl_gun",
        "T": "xl_gun",
        "HB": "strike_craft",
        "W": "planet_killer",
    }
    weapon_to_slot_name = {
        "L": "LARGE_GUN",
        "M": "MEDIUM_GUN",
        "S": "SMALL_GUN",
        "PD": "PD",
        "G": "TORPEDO",
        "X": "EXTRA_LARGE",
        "T": "TITANIC",
        "HB": "STRIKE_CRAFT",
        "W": "PLANET_KILLER_GUN",
    }

    slot_counter = {}
    for weapon_type in ["W", "T", "X", "HB", "L", "M", "G", "S", "PD"]:
        count = design.weapons.get(weapon_type, 0)
        if count == 0:
            continue

        loc_type = weapon_to_loc_type[weapon_type]
        available_locs = locator_map.get(loc_type, [])
        template = TEMPLATES[weapon_type]
        slot_name_base = weapon_to_slot_name[weapon_type]

        for i in range(count):
            slot_counter[slot_name_base] = slot_counter.get(slot_name_base, 0) + 1
            slot_num = slot_counter[slot_name_base]
            slot_name = f"{slot_name_base}_{slot_num:02d}"

            # Get locator
            if available_locs:
                loc = available_locs[i % len(available_locs)]
            else:
                loc = f"{LOCATOR_PREFIX[weapon_type]}_{i+1:02d}"

            lines.append("\tcomponent_slot = {")
            lines.append(f'\t\tname = "{slot_name}"')
            lines.append(f'\t\ttemplate = "{template}"')
            if weapon_type == "HB":
                rotation = 90 if slot_num % 2 == 1 else -90
                lines.append(f"\t\trotation = {rotation}")
            lines.append(f'\t\tlocatorname = "{loc}"')
            lines.append("\t}")

    # Utility slots
    if design.small_utility > 0:
        lines.append(f"\tsmall_utility_slots = {design.small_utility}")
    if design.large_utility > 0:
        lines.append(f"\tlarge_utility_slots = {design.large_utility}")
    if design.aux > 0:
        lines.append(f"\taux_utility_slots = {design.aux}")

    # Resources
    base_cost = int(80 * TIER_COST_MULT[design.tier])
    lines.append("\tresources = {")
    lines.append("\t\tcategory = ship_sections")
    lines.append("\t\tcost = {")
    lines.append(f"\t\t\talloys = {base_cost}")
    lines.append("\t\t}")
    lines.append("\t}")

    lines.append("}")
    return "\n".join(lines)


def cmd_design(args: list[str]) -> int:
    """Generate sections from CLI notation."""
    if len(args) < 3:
        print(
            "Usage: python generate_sections.py design <ship_type> <slot> <notation1> [notation2] ..."
        )
        print(
            "Example: python generate_sections.py design battleship bow T1UL1 X1UL3 L2UL3"
        )
        return 1

    ship_type = args[0]
    slot = args[1]
    notations = args[2:]

    vanilla_data = load_vanilla_data()
    if not vanilla_data:
        return 1

    # Check ship type exists
    if ship_type not in vanilla_data.get("ship_types", {}):
        print(f"ERROR: Unknown ship type '{ship_type}'")
        return 1

    print(f"\n{'=' * 60}")
    print(f"Generating: {ship_type} {slot}")
    print(f"{'=' * 60}")

    sections = []
    for notation in notations:
        design = parse_notation(notation, ship_type)

        # Find entity
        entity, locator_map = find_entity_for_design(
            vanilla_data, ship_type, slot, design.weapons
        )
        if not entity:
            print(f"  SKIP: {notation} - no suitable entity found")
            continue

        # Generate key: BATTLESHIP_BOW_COMMON_T1UL1
        key = f"PBSS_{ship_type.upper()}_{slot.upper()}_{design.tier.upper()}_{notation.upper()}"

        # Generate template
        template = generate_section_template(
            key, ship_type, slot, entity, design, locator_map
        )
        sections.append(template)

        print(
            f"  {notation:15} -> {design.tier:10} ({design.total_points:2} pts) -> {entity}"
        )

    if sections:
        # Append to file (or create if not exists)
        section_dir = SCRIPT_DIR.parent / "src" / "common" / "section_templates"
        section_dir.mkdir(parents=True, exist_ok=True)
        output_file = section_dir / f"01_pbss_{ship_type}_{slot}_sections.txt"

        new_content = "\n\n".join(sections)

        if output_file.exists():
            # Append to existing file
            existing = output_file.read_text(encoding="utf-8-sig")
            # Update header comment with new designs
            if "# Generated designs:" in existing:
                lines = existing.split("\n")
                for i, line in enumerate(lines):
                    if line.startswith("# Generated designs:"):
                        lines[i] = line + ", " + ", ".join(notations)
                        break
                existing = "\n".join(lines)
            content = existing + "\n\n" + new_content
            print(f"\n  Appended: {output_file.name} (+{len(sections)} sections)")
        else:
            # Create new file
            content = f"# PBSS {ship_type.title()} {slot.title()} Sections\n"
            content += f"# Generated designs: {', '.join(notations)}\n\n"
            content += new_content
            print(f"\n  Created: {output_file.name} ({len(sections)} sections)")

        output_file.write_text(content, encoding="utf-8")

    return 0


def cmd_info(args: list[str]) -> int:
    """Show ship slot/entity info."""
    if not args:
        print("Usage: python generate_sections.py info <ship_type>")
        return 1

    ship_type = args[0]
    vanilla_data = load_vanilla_data()
    if not vanilla_data:
        return 1

    ship_data = vanilla_data.get("ship_types", {}).get(ship_type, {})
    if not ship_data:
        print(f"Unknown ship type: {ship_type}")
        return 1

    aux_cost = SHIP_AUX_COST.get(ship_type, 4)

    print(f"\n{'=' * 60}")
    print(f"Ship Type: {ship_type}")
    print(f"Aux Cost: {aux_cost}")
    print(f"{'=' * 60}")

    for slot_name, slot_data in ship_data.get("slots", {}).items():
        print(f"\n  Slot: {slot_name}")
        for entity_name, entity_data in slot_data.get("entities", {}).items():
            locators = entity_data.get("locators", [])
            templates = entity_data.get("templates", [])
            print(f"    Entity: {entity_name}")
            print(f"      Locators: {locators}")
            print(f"      Templates: {templates}")

    return 0


def cmd_calc(args: list[str]) -> int:
    """Calculate points for a notation."""
    if not args:
        print("Usage: python generate_sections.py calc <notation> [ship_type]")
        print("Example: python generate_sections.py calc T1UL1 battleship")
        return 1

    notation = args[0]
    ship_type = args[1] if len(args) > 1 else "battleship"

    design = parse_notation(notation, ship_type)

    print(f"\nNotation: {notation}")
    print(f"Ship: {ship_type}")
    print(f"Weapons: {design.weapons}")
    print(f"Large Utility: {design.large_utility}")
    print(f"Small Utility: {design.small_utility}")
    print(f"Aux: {design.aux}")
    print(f"Total Points: {design.total_points}")
    print(f"Tier: {design.tier}")

    return 0


def main():
    import sys

    if len(sys.argv) < 2:
        print("Usage: python generate_sections.py <command> [args]")
        print("\nCommands:")
        print("  design <ship> <slot> <notation...>  - Generate sections from notation")
        print("  info <ship_type>                    - Show ship slot/entity info")
        print("  calc <notation> [ship_type]         - Calculate points for notation")
        print("\nNotation:")
        print(
            "  Weapons: T=Titan, X=XL, L=Large, M=Medium, S=Small, PD=PointDef, HB=Hangar"
        )
        print("  Utility: UL=LargeUtility, US=SmallUtility, AUX=Auxiliary")
        print("\nExamples:")
        print("  design battleship bow T1UL1 X1UL3 L2UL3")
        print("  calc T2X1UL2 battleship")
        return 1

    cmd = sys.argv[1]

    if cmd == "design":
        return cmd_design(sys.argv[2:])
    elif cmd == "info":
        return cmd_info(sys.argv[2:])
    elif cmd == "calc":
        return cmd_calc(sys.argv[2:])
    else:
        print(f"Unknown command: {cmd}")
        return 1


if __name__ == "__main__":
    exit(main())
