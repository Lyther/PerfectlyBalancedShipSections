#!/usr/bin/env python3
"""
Stellaris Mod Build Script

Cleans, copies, and prepares the mod for distribution.
Handles UTF-8-BOM encoding for localisation files.
"""

import os
import shutil
import sys
import stat
import time
from pathlib import Path


def _remove_readonly(func, path, exc_info):
    """Remove readonly flag on Windows."""
    try:
        os.chmod(path, stat.S_IWRITE)
        func(path)
    except Exception:
        pass


def _rmtree_robust(path: Path, max_retries: int = 3):
    """Remove directory tree with retries for Windows permission issues."""
    if not path.exists():
        return

    for attempt in range(max_retries):
        try:
            # Make files writable first
            for root, dirs, files in os.walk(path):
                for d in dirs:
                    os.chmod(os.path.join(root, d), stat.S_IWRITE)
                for f in files:
                    os.chmod(os.path.join(root, f), stat.S_IWRITE)

            shutil.rmtree(path, onerror=_remove_readonly)
            return
        except PermissionError as e:
            if attempt < max_retries - 1:
                time.sleep(0.5 * (attempt + 1))
                continue
            raise


def clean_dist():
    """Clean the dist directory."""
    dist_path = Path("dist")
    if dist_path.exists():
        _rmtree_robust(dist_path)
    dist_path.mkdir(exist_ok=True)


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
            content = yml_file.read_text(encoding="utf-8-sig")
            # Write back with BOM
            yml_file.write_text(content, encoding="utf-8-sig")
            print(f"Fixed encoding: {yml_file}")
        except Exception as e:
            print(f"Error processing {yml_file}: {e}")


def sanitize_files():
    """Remove development files."""
    dev_extensions = {".psd", ".gitkeep", ".tmp", ".bak", ".orig"}

    for file_path in Path("dist").rglob("*"):
        if file_path.is_file() and file_path.suffix.lower() in dev_extensions:
            file_path.unlink()
            print(f"Removed: {file_path}")


def install_to_stellaris(mod_context):
    """Install descriptor.mod and dist to Stellaris user directory."""
    stellaris_dir = mod_context.get("stellaris_user_dir")
    if not stellaris_dir:
        print("Warning: No Stellaris user directory configured")
        return

    descriptor_dst = Path(stellaris_dir) / "PerfectlyBalancedShipSections.mod"
    mod_folder_name = Path.cwd().name
    install_path = mod_folder_name

    try:
        user_descriptor = _build_user_descriptor(
            Path("src/descriptor.mod"), Path(stellaris_dir), mod_folder_name
        )
        descriptor_dst.write_text(user_descriptor, encoding="utf-8")
        print(f"Installed descriptor to: {descriptor_dst}")
    except Exception as e:
        print(f"Error installing descriptor: {e}")
        return

    dist_src = Path("dist")
    dist_dst = Path(stellaris_dir) / install_path
    if dist_src.exists():
        if dist_dst.exists():
            _rmtree_robust(dist_dst)
        shutil.copytree(dist_src, dist_dst)
        print(f"Installed mod files to: {dist_dst}")


def _build_user_descriptor(
    descriptor_path: Path, stellaris_dir: Path, mod_folder_name: str
):
    """Build the user .mod descriptor with path (no picture)."""
    if not descriptor_path.exists():
        raise FileNotFoundError("src/descriptor.mod not found")

    lines = descriptor_path.read_text(encoding="utf-8").splitlines()
    tags_block = []
    in_tags = False
    fields = {}

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("tags="):
            in_tags = True
            tags_block.append(line)
            continue
        if in_tags:
            tags_block.append(line)
            if stripped.endswith("}"):
                in_tags = False
            continue
        if "=" in stripped:
            key, value = stripped.split("=", 1)
            fields[key.strip()] = value.strip()

    descriptor_lines = []
    for key in ("version",):
        if key in fields:
            descriptor_lines.append(f"{key}={fields[key]}")
    descriptor_lines.extend(tags_block)
    for key in ("name", "supported_version"):
        if key in fields:
            descriptor_lines.append(f"{key}={fields[key]}")

    mod_path = (stellaris_dir / mod_folder_name).as_posix()
    descriptor_lines.append(f'path="{mod_path}"')

    if "remote_file_id" in fields:
        descriptor_lines.append(f'remote_file_id={fields["remote_file_id"]}')
    else:
        descriptor_lines.append('remote_file_id=""')

    return "\n".join(descriptor_lines) + "\n"


def load_mod_context():
    """Load mod context from .cursor/mod-context.json."""
    context_file = Path(".cursor/mod-context.json")
    if context_file.exists():
        try:
            import json

            with open(context_file, "r", encoding="utf-8") as f:
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
