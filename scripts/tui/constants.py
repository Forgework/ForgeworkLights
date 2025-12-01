"""
Constants and configuration for ForgeworkLights TUI
"""
from pathlib import Path


# Directories
CONFIG_DIR = Path.home() / ".config/forgeworklights"
CACHE_DIR = Path.home() / ".cache/forgeworklights"

# File paths
STATE_FILE = CACHE_DIR / "state.json"
BRIGHTNESS_FILE = CONFIG_DIR / "brightness"

# LED themes database (used by daemon and gradient selection)
THEMES_DB_PATH = CONFIG_DIR / "led_themes.json"

# TUI themes database (per-theme palettes for the TUI only)
TUI_THEMES_DB_PATH = CONFIG_DIR / "tui_themes.json"

THEME_SYMLINK = Path.home() / ".config/omarchy/current/theme"
LED_THEME_FILE = CONFIG_DIR / "led-theme"
ANIMATION_FILE = CONFIG_DIR / "animation"
ANIMATION_PARAMS_FILE = CONFIG_DIR / "animation-params.json"

# Binary and install paths
BIN_DIR = Path("/usr/local/bin")
DAEMON_BINARY = BIN_DIR / "forgeworklights"
SHARE_DIR = Path("/usr/local/share/forgeworklights")

# Omarchy theme directories
OMARCHY_THEME_DIRS = [
    Path.home() / ".config/omarchy/themes",
    Path.home() / ".local/share/omarchy/themes",
]

# Specific Omarchy theme paths
# Aether theme directory (watched for changes to update the Aether entry)
AETHER_THEME_DIR = Path.home() / ".config/omarchy/themes/aether"

# UI Settings
MIN_WIDTH = 60
AUTO_REFRESH_INTERVAL = 2.0  # seconds
