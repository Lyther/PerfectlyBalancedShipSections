#!/usr/bin/env python3
"""
Stellaris Mod Build Script

Cleans, copies, and prepares the mod for distribution.
Handles UTF-8-BOM encoding for localisation files.
"""

import os
import shutil
import sys
from pathlib import Path

def clean_dist():
    """Clean the dist directory."""
    dist_path = Path("dist")
    if dist_path.exists():
        shutil.rmtree(dist_path)
    dist_path.mkdir()

def copy_source_to_dist():
    """Copy src/ to dist/ recursively."""
    src_path = Path("src")
    dist_path = Path("dist")

    if not src_path.exists():
        print("Error: src/ directory not found")
        return False

    shutil.copytree(src_path, dist_path, dirs_exist_ok=True)
    return True

def enforce_utf8_bom():
    """Force UTF-8-BOM encoding on localisation .yml files."""
    localisation_path = Path("dist/localisation")

    if not localisation_path.exists():
        return

    for yml_file in localisation_path.rglob("*.yml"):
        try:
            # Read as UTF-8 (with or without BOM)
            content = yml_file.read_text(encoding='utf-8-sig')
            # Write back with BOM
            yml_file.write_text(content, encoding='utf-8-sig')
            print(f"Fixed encoding: {yml_file}")
        except Exception as e:
            print(f"Error processing {yml_file}: {e}")

def sanitize_files():
    """Remove development files."""
    dev_extensions = {'.psd', '.gitkeep', '.tmp', '.bak', '.orig'}

    for file_path in Path("dist").rglob("*"):
        if file_path.is_file() and file_path.suffix.lower() in dev_extensions:
            file_path.unlink()
            print(f"Removed: {file_path}")

def install_to_stellaris(mod_context):
    """Install descriptor.mod to Stellaris user directory."""
    stellaris_dir = mod_context.get("stellaris_user_dir")
    if not stellaris_dir:
        print("Warning: No Stellaris user directory configured")
        return

    descriptor_src = Path("src/descriptor.mod")
    descriptor_dst = Path(stellaris_dir) / "PerfectlyBalancedShipSections.mod"

    if descriptor_src.exists():
        try:
            shutil.copy2(descriptor_src, descriptor_dst)
            print(f"Installed descriptor to: {descriptor_dst}")
        except Exception as e:
            print(f"Error installing descriptor: {e}")
    else:
        print("Warning: src/descriptor.mod not found")

def load_mod_context():
    """Load mod context from .cursor/mod-context.json."""
    context_file = Path(".cursor/mod-context.json")
    if context_file.exists():
        try:
            import json
            with open(context_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading context: {e}")
    return {}

def main():
    """Main build process."""
    print("Building Stellaris mod...")

    # Load context
    mod_context = load_mod_context()

    # Phase 1: Clean
    print("Cleaning dist...")
    clean_dist()

    # Phase 2: Copy
    print("Copying source files...")
    if not copy_source_to_dist():
        sys.exit(1)

    # Phase 3: Enforce encoding
    print("Enforcing UTF-8-BOM for localisation...")
    enforce_utf8_bom()

    # Phase 4: Sanitize
    print("Removing development files...")
    sanitize_files()

    # Phase 5: Install
    print("Installing to Stellaris...")
    install_to_stellaris(mod_context)

    print("Build complete!")

if __name__ == "__main__":
    main()