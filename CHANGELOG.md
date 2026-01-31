# Changelog

All notable changes to **Perfectly Balanced Ship Sections** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2024-01-XX - Initial Release 🚀

### Added

- **Complete Ship Coverage**: 23 different ship types with 450+ new section variants
- **4-Tier Progression System**:
  - Common sections (default unlock)
  - Advanced sections (technology requirements)
  - Pro sections (multiple prerequisites)
  - Ultra sections (insane requirements and costs)
- **Player-Only Restrictions**: Advanced/Pro/Ultra sections restricted to players to maintain AI balance
- **Weapon Slot Balance**: Implemented P=S, 2S=1M, 2M=1L, 1L=1HB, 2L=1X, 2X=1T conversion rules
- **Multilingual Support**: Full localization for 10 languages (English, Simplified Chinese, Brazilian Portuguese, French, German, Polish, Russian, Spanish, Japanese, Korean)
- **Biological Ship Mechanics**: Food costs, regeneration bonuses, and stage progression
- **T-Slot Compatibility**: Custom titanic weapons compatible with all ship sizes
- **Strategic Depth**: Bow offense, Mid utility, Stern defense creates meaningful tactical choices

### Ship Types Implemented

#### Military Ships

- **Corvettes**: 16 section variants
- **Destroyers**: 23 section variants (10 bow + 13 stern)
- **Cruisers**: 24 section variants (8 bow + 10 mid + 6 stern)
- **Battleships**: 30 section variants (10 per slot)
- **Titans**: 30 section variants (10 per slot)

#### Special Capital Ships

- **Juggernauts**: 10 section variants
- **Bio-Titans**: 30 section variants (10 per slot)
- **Colossus**: 8 section variants (including planet-killer compatibility)

#### Crisis & Biological Ships

- **Harbingers**: 10 section variants
- **Maulers**: 10 section variants
- **Stingers**: 10 section variants
- **Weavers**: 10 section variants
- **Offspring Harbingers**: 10 section variants
- **Offspring Maulers**: 10 section variants
- **Offspring Stingers**: 10 section variants
- **Offspring Weavers**: 10 section variants
- **Offspring General**: 24 section variants
- **Crisis Ships**: 25 section variants
- **Cosmo Crisis**: 25 section variants
- **Star Eaters**: 6 section variants

#### Defensive Structures

- **Military Stations**: 6 section variants
- **Ion Cannons**: 10 section variants

### Technical Features

- **UTF-8 BOM Encoding**: All localization files properly encoded for Stellaris compatibility
- **Build System**: Python-based build script with automatic UTF-8 BOM fixing
- **Modular Architecture**: Clean source/dist separation for development
- **Reference Documentation**: Extensive vanilla syntax and game modifier references included

### Balance Features

- **Economic Scaling**: Ultra sections cost 2-4x base alloys to justify massive bonuses
- **Power Progression**: Each tier provides meaningful combat/utility improvements
- **Strategic Trade-offs**: Powerful weapons require armor, shield, or utility sacrifices
- **AI Protection**: Overpowered sections automatically restricted to player use

## [Unreleased] - Future Updates

### Planned Features

- **ACOT Compatibility**: Support for Another Crusade of Truth ship designs
- **Additional Crisis Ships**: More variants for end-game crisis scenarios
- **Custom Icons**: Unique visual indicators for different section tiers
- **Balance Tweaks**: Community feedback-driven balance adjustments

### Technical Improvements

- **Performance Optimization**: Further optimization of section loading
- **Mod Compatibility**: Enhanced compatibility checking with other ship mods
- **Documentation**: Expanded developer documentation and contribution guidelines

---

## Development Notes

### Version Numbering

This project uses [Semantic Versioning](https://semver.org/):

- **MAJOR** version for incompatible API changes
- **MINOR** version for backwards-compatible functionality additions
- **PATCH** version for backwards-compatible bug fixes

### Contribution Guidelines

- Balance changes require extensive testing
- New sections must follow established weapon slot conversion rules
- All new features require localization keys
- Player-only restrictions for sections with >30% damage/range bonuses

---

**Legend:**

- 🚀 Major feature release
- ✨ New feature
- 🐛 Bug fix
- ⚖️ Balance change
- 📚 Documentation
- 🛠️ Technical improvement
