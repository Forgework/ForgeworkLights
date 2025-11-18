"""
TUI Theme loader - loads colors from tui-theme.toml
"""
import tomllib
from pathlib import Path
from typing import Dict
from .constants import CONFIG_DIR, SHARE_DIR

# Default fallback colors
DEFAULT_COLORS = {
    "main_bg": "#091819",
    "main_fg": "#ffffff",
    "title": "#93c7d2",
    "hi_fg": "#C3DDDF",
    "selected_bg": "#345254",
    "selected_fg": "#ffffff",
    "inactive_fg": "#345254",
    "div_line": "#345254",
    "box_outline": "#79beae",
    "button_fg": "#79beae",
    "secondary_bg": "#0d2324",
    "hover_bg": "#1a3536",
}

def load_theme() -> Dict[str, str]:
    """Load theme colors from config file or use defaults"""
    config_paths = [
        CONFIG_DIR / "tui-theme.toml",
        SHARE_DIR / "tui-theme.toml",
        Path(__file__).parent.parent.parent / "config" / "tui-theme.toml",
    ]
    
    for path in config_paths:
        if path.exists():
            try:
                with open(path, "rb") as f:
                    theme = tomllib.load(f)
                    # Merge with defaults (in case some keys are missing)
                    return {**DEFAULT_COLORS, **theme}
            except Exception as e:
                print(f"Warning: Failed to load theme from {path}: {e}")
                continue
    
    # Return defaults if no config found
    return DEFAULT_COLORS

# Load theme once at module import
THEME = load_theme()
