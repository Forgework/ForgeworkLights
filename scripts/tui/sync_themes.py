#!/usr/bin/env python3
"""Theme sync utilities for ForgeworkLights TUI.

Shared logic for syncing themes from Omarchy theme directories into the
ForgeworkLights themes database. This module is used both by the TUI and by
the CLI wrapper script installed as forgeworklights-sync-themes.
"""

import json
import re
from pathlib import Path

from .utils.colors import generate_gradient
from .constants import THEMES_DB_PATH, TUI_THEMES_DB_PATH, OMARCHY_THEME_DIRS, SHARE_DIR
from .theme import DEFAULT_COLORS


def extract_colors_from_btop(btop_file: Path):
    """Extract temp_start, temp_mid, temp_end colors from btop.theme."""
    try:
        data = btop_file.read_text()
        start = re.search(r'theme\[cpu_start\]\s*=\s*"#([0-9a-fA-F]{6})"', data)
        mid = re.search(r'theme\[cpu_mid\]\s*=\s*"#([0-9a-fA-F]{6})"', data)
        end = re.search(r'theme\[cpu_end\]\s*=\s*"#([0-9a-fA-F]{6})"', data)

        if start and mid and end:
            return [f"#{start.group(1)}", f"#{mid.group(1)}", f"#{end.group(1)}"]
    except Exception:
        pass
    return None


def _extract_tui_palette_from_btop(btop_file: Path):
    """Extract a rich TUI palette from a btop.theme file.

    Uses theme[main_bg], main_fg, title, hi_fg, selected_bg, inactive_fg,
    div_line, meter_bg, proc_box. Missing values fall back to DEFAULT_COLORS.
    """

    try:
        data = btop_file.read_text()

        def _color(key: str):
            m = re.search(
                rf'theme\[{key}\]\s*=\s*"#([0-9a-fA-F]{{6}})"',
                data,
            )
            return f"#{m.group(1)}" if m else None

        main_bg = _color("main_bg") or DEFAULT_COLORS["main_bg"]
        main_fg = _color("main_fg") or DEFAULT_COLORS["main_fg"]
        title = _color("title") or DEFAULT_COLORS["title"]
        hi_fg = _color("hi_fg") or DEFAULT_COLORS["hi_fg"]
        selected_bg = _color("selected_bg") or DEFAULT_COLORS["selected_bg"]
        inactive_fg = _color("inactive_fg") or DEFAULT_COLORS["inactive_fg"]
        div_line = _color("div_line") or DEFAULT_COLORS["div_line"]

        # Good candidate for secondary background
        secondary_bg = _color("meter_bg") or DEFAULT_COLORS["secondary_bg"]

        # Outline / button accent – prefer proc_box, else hi_fg
        box_outline = _color("proc_box") or hi_fg
        button_fg = box_outline

        # Hover background: reuse selected_bg
        hover_bg = selected_bg

        return {
            "main_bg": main_bg,
            "main_fg": main_fg,
            "title": title,
            "hi_fg": hi_fg,
            "selected_bg": selected_bg,
            "inactive_fg": inactive_fg,
            "div_line": div_line,
            "box_outline": box_outline,
            "button_fg": button_fg,
            "secondary_bg": secondary_bg,
            "hover_bg": hover_bg,
        }
    except Exception:
        return None


#def extract_colors_from_json(json_file: Path):
#    """Extract accent colors from palette.json or theme.json."""
#    try:
#        data = json.loads(json_file.read_text())
#        if "accent" in data and "accent2" in data and "accent3" in data:
#            return [data["accent"], data["accent2"], data["accent3"]]
#    except Exception:
#        pass
#    return None


def scan_theme_directory(theme_dir: Path):
    """Scan a theme directory for color information.

    Returns a dict containing at least "name" and "colors". When
    possible, also includes a "tui" key with a per-theme TUI palette
    suitable for the ForgeworkLights TUI.
    """

    theme_name = theme_dir.name

    # Try palette files in priority order
    palette_files = [
        #("palette.json", extract_colors_from_json),
        #("theme.json", extract_colors_from_json),
        ("btop.theme", extract_colors_from_btop),
    ]

    for filename, extractor in palette_files:
        filepath = theme_dir / filename
        if filepath.exists():
            colors = extractor(filepath)
            if colors:
                entry = {
                    "name": theme_name.replace("-", " ").title(),
                    "colors": generate_gradient(colors, 14),
                }

                # Attempt to enrich with a TUI palette when using btop.theme
                if filename == "btop.theme":
                    tui_palette = _extract_tui_palette_from_btop(filepath)
                    if tui_palette:
                        entry["tui"] = tui_palette

                return entry

    return None




def sync_themes(verbose: bool = False) -> int:
    """Sync all themes from Omarchy directory to LED and TUI databases.

    - Restores any missing premade themes from SHARE_DIR/themes.json.
    - Adds new themes discovered in OMARCHY_THEME_DIRS that are not yet
      present in the themes database.
    - Never overwrites existing themes in the database.
    """

    # Locate Omarchy theme directories
    theme_dirs = []
    for location in OMARCHY_THEME_DIRS:
        if location.exists() and location.is_dir():
            theme_dirs.extend([d for d in location.iterdir() if d.is_dir()])

    # Load existing LED themes.json
    themes_path = THEMES_DB_PATH
    themes_path.parent.mkdir(parents=True, exist_ok=True)

    if themes_path.exists():
        try:
            with open(themes_path, "r") as f:
                data = json.load(f)
        except Exception:
            data = {"themes": {}}
    else:
        data = {"themes": {}}

    # Load existing TUI themes database (tui_themes.json)
    tui_themes_path = TUI_THEMES_DB_PATH
    if tui_themes_path.exists():
        try:
            with open(tui_themes_path, "r") as f:
                tui_data = json.load(f)
                if not isinstance(tui_data, dict):
                    tui_data = {"themes": {}}
        except Exception:
            tui_data = {"themes": {}}
    else:
        tui_data = {"themes": {}}

    # Load premade LED themes for restoring deleted LED defaults
    premade_themes_path = SHARE_DIR / "led_themes.json"
    premade_themes = {}

    if premade_themes_path.exists():
        try:
            with open(premade_themes_path, "r") as f:
                premade_data = json.load(f)
                premade_themes = premade_data.get("themes", {})
                if verbose:
                    print(
                        f"Loaded {len(premade_themes)} premade themes from {premade_themes_path}"
                    )
        except Exception as e:
            if verbose:
                print(f"Warning: Could not load premade themes: {e}")

    # Restore missing premade LED themes
    restored_count = 0
    for theme_key, theme_data in premade_themes.items():
        if theme_key not in data["themes"]:
            data["themes"][theme_key] = theme_data
            restored_count += 1
            if verbose:
                print(f"✓ Restored: {theme_key} (from premade)")

    if restored_count > 0 and verbose:
        print(f"Restored {restored_count} deleted default themes")

    if not theme_dirs:
        if verbose:
            print("No Omarchy theme directories found")
        return restored_count

    # Scan all theme directories
    new_count = 0
    updated_count = 0

    for theme_dir in theme_dirs:
        theme_key = theme_dir.name
        theme_data = scan_theme_directory(theme_dir)

        if theme_data:
            if theme_key not in data["themes"]:
                data["themes"][theme_key] = theme_data
                new_count += 1
                if verbose:
                    print(f"✓ Added: {theme_key}")
            else:
                # For most themes, keep the non-destructive behavior and never
                # overwrite existing entries. The Aether theme is special: we
                # want it to track the live Omarchy palette, so we allow it to
                # be updated when its source changes.
                if theme_key == "aether":
                    data["themes"][theme_key] = theme_data
                    updated_count += 1
                    if verbose:
                        print(f"✓ Updated: {theme_key} (Aether)")
                elif verbose:
                    print(f"⏭ Skipped: {theme_key} (already exists)")

            # Update TUI themes database for any Omarchy-backed theme
            if "tui" in theme_data:
                if "themes" not in tui_data or not isinstance(tui_data["themes"], dict):
                    tui_data["themes"] = {}
                tui_data["themes"][theme_key] = theme_data["tui"]

    # Save updated LED themes.json
    with open(themes_path, "w") as f:
        json.dump(data, f, indent=2)

    # Save updated TUI themes database
    with open(tui_themes_path, "w") as f:
        json.dump(tui_data, f, indent=2)

    if verbose:
        print("\nSync complete:")
        print(f"  Restored: {restored_count}")
        print(f"  New themes: {new_count}")
        print(f"  Updated: {updated_count}")
        print(f"  Total themes: {len(data['themes'])}")
        print(f"  Saved to: {themes_path}")

    return restored_count + new_count + updated_count


def main(argv=None) -> int:
    """CLI entry point for sync script."""
    import sys

    if argv is None:
        argv = sys.argv[1:]

    verbose = "--verbose" in argv or "-v" in argv
    changes = sync_themes(verbose=verbose)
    return 0 if changes >= 0 else 1
