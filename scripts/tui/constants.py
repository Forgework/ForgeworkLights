"""
Constants and configuration for ForgeworkLights TUI
"""
from pathlib import Path


# Directories
CONFIG_DIR = Path.home() / ".config/omarchy-argb"
CACHE_DIR = Path.home() / ".cache/omarchy-argb"

# File paths
STATE_FILE = CACHE_DIR / "state.json"
BRIGHTNESS_FILE = CONFIG_DIR / "brightness"
THEMES_DB_PATH = CONFIG_DIR / "themes.json"
THEME_SYMLINK = Path.home() / ".config/omarchy/current/theme"
LED_THEME_FILE = CONFIG_DIR / "led-theme"
ANIMATION_FILE = CONFIG_DIR / "animation"
ANIMATION_PARAMS_FILE = CONFIG_DIR / "animation-params.json"

# Daemon binary
DAEMON_BINARY = "/usr/local/bin/omarchy-argb"

# UI Settings
MIN_WIDTH = 60
AUTO_REFRESH_INTERVAL = 2.0  # seconds
