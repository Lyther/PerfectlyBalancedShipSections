# Perfectly Balanced Ship Sections

[![Stellaris Version](https://img.shields.io/badge/Stellaris-4.2.*-blue.svg)](https://store.steampowered.com/app/281990/Stellaris/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**A comprehensive ship section expansion mod for Stellaris that adds hundreds of new ship building options while maintaining perfect balance and strategic depth.**

## ✨ Features

### 🚀 Complete Ship Coverage

- **Military Ships**: Corvettes, Destroyers, Cruisers, Battleships, Titans
- **Special Capital Ships**: Juggernauts, Bio-Titans, Colossus
- **Crisis & Biological Ships**: Crisis ships, Star Eaters, Harbingers, Maulers, Stingers, Weavers, Offspring variants
- **Defensive Structures**: Military Stations, Ion Cannons
- **Total Sections Added**: 450+ new ship section variants

### ⚖️ Balanced Design Philosophy

- **4-Tier Progression**: Common (default unlock) → Advanced (tech requirements) → Pro (multiple prerequisites) → Ultra (insane requirements)
- **Weapon Slot Balance**: P=S, 2S=1M, 2M=1L, 1L=1HB, 2L=1X, 2X=1T
- **Player-Only OP Sections**: Advanced/Pro/Ultra sections restricted to players only to maintain AI balance
- **Strategic Trade-offs**: Powerful weapons require meaningful sacrifices (reduced utility, armor, or negative modifiers)

### 🌍 Multilingual Support

- **10 Languages**: English, Simplified Chinese, Brazilian Portuguese, French, German, Polish, Russian, Spanish, Japanese, Korean
- **UTF-8 BOM Encoding**: Proper encoding for all Stellaris versions

### 🎮 Enhanced Gameplay Experience

- **Tactical Depth**: Bow (offense), Mid (core/utility), Stern (defense/support) create meaningful ship design choices
- **Economic Balance**: Ultra sections cost 2-4x base alloys to justify massive bonuses
- **Biological Mechanics**: Food costs, regeneration bonuses, and unique organic capabilities
- **DLC Integration**: Full support for biological ships, crisis events, and special vessels

## 📦 Installation

### Method 1: Direct Download

1. Download the mod archive
2. Extract to `Documents/Paradox Interactive/Stellaris/mod/`
3. Enable the mod in the Stellaris launcher

### Method 2: Steam Workshop (Recommended)

1. Subscribe to [Perfectly Balanced Ship Sections](https://steamcommunity.com/sharedfiles/filedetails/?id=XXXXXXX) on Steam Workshop
2. Enable the mod in the Stellaris launcher

### Method 3: Manual Build (For Developers)

```bash
git clone https://github.com/yourusername/perfectly-balanced-ship-sections.git
cd perfectly-balanced-ship-sections
python scripts/build.py
```

## 🔧 Compatibility

- **Stellaris Version**: 4.2.*
- **Required DLC**: None (works with base game)
- **Recommended DLC**: All DLC supported
- **Other Mods**: Compatible with most ship design mods
- **Save Games**: Safe to add/remove from existing saves

## 🎯 Ship Section Examples

### Battleship Sections (10 per slot type)

```text
┌─ Bow Sections ──────────────────────┬─ Mid Sections ──────────────────────┬─ Stern Sections ─────────────────────┐
│ Artillery Command                  │ Command Nexus                      │ Rear Guard                          │
│ Carrier Command                    │ Shield Matrix                      │ Missile Defense                     │
│ Plasma Devastation (Advanced)      │ Armor Bastion (Advanced)           │ Citadel Defense (Advanced)          │
│ Guided Assault Center (Pro)        │ Fleet Coordinator (Advanced)       │ Carrier Support (Advanced)          │
│ Apocalypse Artillery (Pro)         │ Strike Craft Hub (Advanced)        │ Armored Citadel (Advanced)          │
│ Stellar Devastator (Ultra)         │ Quantum Overload (Ultra)           │ Omega Defense (Ultra)               │
│ Void Reaver (Ultra)                │ Nexus of Destruction (Ultra)       │ Titanic Armageddon (Ultra)          │
└────────────────────────────────────┴────────────────────────────────────┴────────────────────────────────────┘
```

### Biological Ship Sections (10 total)

```text
┌─ Harbinger Sections ────────────────┬─ Mauler Sections ──────────────────┬─ Stinger Sections ──────────────────┐
│ Enhanced Picket                     │ Enhanced Swarm                     │ Enhanced Artillery                  │
│ Enhanced Artillery                  │ Enhanced Picket                    │ Enhanced Bombardment                │
│ Advanced Picket (Stage 2)           │ Advanced Swarm (Stage 2)           │ Advanced Artillery (Stage 2)        │
│ Advanced Artillery (Stage 2)        │ Advanced Picket (Stage 2)          │ Advanced Bombardment (Stage 2)      │
│ Elite Swarm Picket (Stage 3)        │ Elite Swarm Predator (Stage 3)     │ Elite Artillery Swarm (Stage 3)     │
│ Elite Support Picket (Stage 3)      │ Elite Artillery Predator (Stage 3) │ Elite Siege Artillery (Stage 3)     │
│ Elite Artillery Swarm (Stage 3)     │ Elite Assault Bruiser (Stage 3)    │ Elite Siege Breaker (Stage 3)       │
└────────────────────────────────────┴────────────────────────────────────┴────────────────────────────────────┘
```

## 🛠️ Development

### Project Structure

```text
├── src/                    # Source files (what you edit)
│   ├── common/
│   │   ├── section_templates/    # Ship section definitions
│   │   └── component_templates/  # Weapon definitions
│   ├── localisation/             # Translation files
│   └── descriptor.mod            # Mod metadata
├── dist/                   # Built mod files (auto-generated)
├── scripts/                # Build tools
│   └── build.py           # Main build script
├── ref/                   # Reference documentation
└── .cursor/               # Development notes
```

### Building from Source

```bash
# Clean and build
python scripts/build.py

# The script will:
# - Clean dist directory
# - Copy source files
# - Fix UTF-8-BOM encoding for localization
# - Install to Stellaris mod directory
```

### Adding New Sections

1. Create new section template in `src/common/section_templates/`
2. Add localization keys to `src/localisation/english/`
3. Run build script to update all language files
4. Test in Stellaris

### Weapon Slot Balance Rules

- **Point Defense (PD)**: Anti-strike craft defense
- **Small (S)**: Basic guns, balanced utility
- **Medium (M)**: Versatile weapons, good balance
- **Large (L)**: Heavy hitting, some utility sacrifice
- **Extra Large (X)**: Devastating power, major trade-offs
- **Titanic (T)**: Ultimate weapons, extreme requirements

## 🤝 Contributing

### How to Contribute

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-ship-sections`)
3. Make your changes
4. Add localization keys for new sections
5. Test thoroughly in Stellaris
6. Submit a pull request

### Guidelines

- **Balance First**: New sections must fit the established balance framework
- **No AI Exploitation**: Powerful sections must be player-only if they unbalance AI
- **Consistent Naming**: Follow PBSS_[SHIP_TYPE]_[SLOT]_[ROLE]_[TIER] pattern
- **Documentation**: Update this README for new features

### Testing Checklist

- [ ] All sections load without errors
- [ ] Localization displays correctly in all 10 languages
- [ ] AI cannot build player-only sections
- [ ] Balance feels appropriate for tier
- [ ] No conflicts with vanilla sections

## 📋 Changelog

### Version 1.0.0

- ✅ Complete ship section coverage (23 ship types)
- ✅ 450+ new section variants
- ✅ 4-tier progression system
- ✅ Full multilingual support
- ✅ Player-only restrictions on OP sections
- ✅ T-slot weapon compatibility
- ✅ Biological ship mechanics

## 🙏 Credits & Acknowledgments

- **Paradox Interactive**: For creating Stellaris
- **Stellaris Modding Community**: For inspiration and reference materials
- **Open Source Contributors**: For feedback and improvements

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔗 Links

- **Steam Workshop**: [Perfectly Balanced Ship Sections](https://steamcommunity.com/sharedfiles/filedetails/?id=XXXXXXX)
- **GitHub Repository**: [github.com/yourusername/perfectly-balanced-ship-sections](https://github.com/yourusername/perfectly-balanced-ship-sections)
- **Stellaris Modding Forum**: [forum.paradoxplaza.com](https://forum.paradoxplaza.com)
- **Stellaris Wiki**: [stellaris.paradoxwikis.com](https://stellaris.paradoxwikis.com)

---

**Made with ❤️ for the Stellaris community**
