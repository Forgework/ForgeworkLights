"""
TUI Theme loader - loads colors from tui_themes.json based on the current
Omarchy theme (THEME_SYMLINK).
"""
import json
from pathlib import Path
from typing import Dict
from .constants import TUI_THEMES_DB_PATH, THEME_SYMLINK

# Default fallback colors
DEFAULT_COLORS = {
    "main_bg": "#091819",
    "main_fg": "#ffffff",
    "title": "#93c7d2",
    "hi_fg": "#C3DDDF",
    "selected_bg": "#345254",
    "inactive_fg": "#345254",
    "div_line": "#345254",
    "box_outline": "#79beae",
    "button_fg": "#79beae",
    "secondary_bg": "#0d2324",
    "hover_bg": "#1a3536",
}


def _load_themes_db() -> Dict:
    """Load the TUI themes database JSON from TUI_THEMES_DB_PATH.

    Returns a dict with at least a "themes" key; on error, returns
    {"themes": {}}.
    """

    try:
        if TUI_THEMES_DB_PATH.exists():
            with open(TUI_THEMES_DB_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    data.setdefault("themes", {})
                    return data
    except Exception:
        pass

    return {"themes": {}}


def _resolve_active_theme_key(data: Dict) -> str | None:
    """Resolve the active theme key from THEME_SYMLINK only.

    The TUI always visually tracks the current Omarchy theme. It does not
    consider LED_THEME_FILE when choosing which entry from themes.json to
    use.

    Resolution strategy:
    - If THEME_SYMLINK points to a valid directory whose name exists as a
      key in data["themes"], use that key.
    - Otherwise, fall back to the first key in data["themes"] if any.
    - If there are no themes at all, return None so callers can fall back
      to DEFAULT_COLORS.
    """

    themes = data.get("themes", {})

    # 1) Match Omarchy theme via symlink
    try:
        if THEME_SYMLINK.exists() and THEME_SYMLINK.is_symlink():
            omarchy_theme_dir = THEME_SYMLINK.resolve(strict=False)
            omarchy_key = omarchy_theme_dir.name
            if omarchy_key in themes:
                return omarchy_key
    except Exception:
        pass

    # 2) Fallback: first available theme key, if any
    if themes:
        return next(iter(themes.keys()))

    return None


def load_theme() -> Dict[str, str]:
    """Load TUI theme colors from themes.json or use defaults.

    Reads the themes database at THEMES_DB_PATH, resolves the active theme
    key using LED_THEME_FILE / THEME_SYMLINK, and then loads that theme's
    palette. Any missing keys are filled from DEFAULT_COLORS.
    """

    data = _load_themes_db()
    theme_key = _resolve_active_theme_key(data)

    if not theme_key:
        return DEFAULT_COLORS

    themes = data.get("themes", {})
    theme_entry = themes.get(theme_key, {})

    # Merge loaded values with defaults in case some keys are missing
    return {**DEFAULT_COLORS, **theme_entry}

# Load theme once at module import
THEME = load_theme()
