# PBSS Scripts Toolkit

Scripts for managing and validating Stellaris ship section templates.

## Architecture

```text
vanilla_ship_data.json    <- Source of truth (extracted from game)
       │
       ├── extract_vanilla_data.py   <- Extracts data from game files
       ├── validate_sections.py      <- Validates mod against vanilla
       ├── fix_section_errors.py     <- Fixes common errors
       └── generate_sections.py      <- Point-based section analysis
```

## Data Hierarchy

The toolkit enforces a strict hierarchy based on vanilla game data:

```text
Ship Type (corvette, cruiser, titan, star_eater, etc.)
  └── Slot (bow, mid, stern)
        └── Entity (titan_mid_entity, cruiser_bow_L1_entity)
              └── Locators (large_gun_01, weapon_01, root, etc.)
```

Entities are **only valid** for the ship_type/slot combinations where they are defined in vanilla. Using an entity in the wrong context causes game crashes or graphical bugs.

## Scripts

### 1. extract_vanilla_data.py

Extracts ship section data from **all** vanilla Stellaris section templates into `vanilla_ship_data.json`.

```bash
python scripts/extract_vanilla_data.py
```

**Run when**: Game updates, new DLC releases

**Output**: `vanilla_ship_data.json` containing:

- Ship type → slot → entity → locator hierarchy
- Entity → valid (ship_type, slot) context mappings
- Valid ship modifiers
- Valid technology prerequisites
- Invalid → valid replacement maps

### 2. validate_sections.py

Validates mod section templates against vanilla data without making changes.

```bash
python scripts/validate_sections.py
```

**Reports**:

- ❌ `invalid_ship_type`: Unknown ship type
- ❌ `invalid_slot`: Slot not valid for ship type
- ❌ `wrong_entity_context`: Entity used in wrong ship_type/slot (causes crashes)
- ❌ `invalid_locator`: Locator not defined on entity
- ⚠️ `unknown_entity`: Entity not found in vanilla data
- ⚠️ `invalid_modifier`: Invalid ship modifier
- ⚠️ `invalid_tech`: Invalid technology prerequisite

### 3. fix_section_errors.py

Automatically fixes errors using vanilla data as reference.

```bash
python scripts/fix_section_errors.py
```

**Fixes**:

- **Wrong entity context**: Replaces entities used in wrong ship_type/slot with valid ones
- **Invalid slot names**: Normalizes aliases (`ship` → `mid`, `core` → `mid`)
- **Unknown entities**: Replaces with appropriate entity for ship_type/slot
- **Invalid modifiers**: Maps to valid equivalents or removes
- **Invalid technologies**: Maps to valid equivalents
- **Invalid locators**: Maps to valid locators on the entity

**Fix Strategies** (in priority order):

1. Check entity context validity for ship_type/slot
2. Replace wrong-context entities with valid alternatives
3. Replace unknown entities with defaults
4. Find better entity with all needed locators
5. Map invalid locators to valid ones

### 4. generate_sections.py

Analyzes existing sections using a point-based balancing system.

```bash
python scripts/generate_sections.py analyze <file>
python scripts/generate_sections.py analyze-all
python scripts/generate_sections.py vanilla-baselines
python scripts/generate_sections.py ship-types
```

**Point System**:

| Slot Type | Points |
|-----------|--------|
| S (Small) | 1 |
| PD (Point Defense) | 1 |
| M (Medium) | 2 |
| G (Guided) | 2 |
| L (Large) | 4 |
| HB (Hangar Bay) | 4 |
| X (Extra Large) | 8 |
| T (Titan) | 16 |
| W (World Cracker) | Special |

**Aux Slot Costs** (scaled by ship size):

| Ship Size | Aux Cost |
|-----------|----------|
| Corvette | 1 |
| Frigate | 1 |
| Destroyer | 2 |
| Cruiser | 4 |
| Battlecruiser | 6 |
| Battleship | 8 |
| Carrier | 10 |
| Dreadnought | 12 |
| Titan | 16 |
| Juggernaut | 24 |
| Colossus | 24 |
| Star Eater | 32 |

**Tier Multipliers**:

- Common: 1.00x
- Advanced: 1.25x
- Pro: 1.50x
- Ultra: 1.75x
- Ultimate: 2.00x

## Entity/Locator Reference

### Common Ship Entities

| Entity | Ship Type | Slot | Valid Locators |
|--------|-----------|------|----------------|
| `titan_bow_entity` | titan | bow | `xl_gun_01` |
| `titan_mid_entity` | titan | mid | `large_gun_01-04` |
| `titan_stern_entity` | titan | stern | `large_gun_01-02` |
| `cruiser_bow_L1_entity` | cruiser | bow | `large_gun_01` |
| `cruiser_bow_M2_entity` | cruiser | bow | `medium_gun_01-02` |
| `star_eater_ship_entity` | star_eater | ship | `core`, `root` |
| `colossus_ship_entity` | colossus | mid | `planet_killer_gun_01` |

### Invalid Modifier Mappings

| Invalid | Valid |
|---------|-------|
| `ship_weapon_damage_mult` | `ship_weapon_damage` |
| `fleet_command_limit_add` | (removed) |
| `ship_repair_mult` | `ship_repair_hull_mult` |
| `sensor_range_mult` | `ship_sensor_range_add` |

### Invalid Tech Mappings

| Invalid | Valid |
|---------|-------|
| `tech_railguns_1` | `tech_mass_drivers_2` |
| `tech_railguns_2` | `tech_mass_drivers_3` |
| `tech_railguns_3` | `tech_mass_drivers_4` |

## Notes

- **Context Matters**: An entity valid for one ship type (e.g., `stellarite_ship_section_entity`) will crash the game if used on another ship type (e.g., titan). Always use entities in their defined context.
- **Regenerate JSON**: After game updates, run `extract_vanilla_data.py` to refresh reference data.
- **Validation First**: Run `validate_sections.py` before and after fixes to verify compliance.
