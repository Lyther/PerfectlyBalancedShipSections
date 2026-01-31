# Perfectly Balanced Ship Sections

A Stellaris mod that provides additional ship sections for enhanced ship building options.

## Features

- Additional ship sections for all original Stellaris ships
- Planned support for ACOT (Another Crusade of Truth) ships
- Clean source-dist separation for development

## Development Setup

1. Source files go in `src/`
2. Run `python scripts/build.py` to build to `dist/`
3. The built mod is automatically installed to your Stellaris mod directory

## Directory Structure

- `src/` - Source files (what you edit)
- `dist/` - Built mod files (auto-generated)
- `scripts/` - Build tools
- `ref/` - Reference documentation

## Building

```bash
python scripts/build.py
```

This will:
- Clean the dist directory
- Copy source to dist
- Fix UTF-8-BOM encoding for localisation files
- Remove development files
- Install to Stellaris mod directory