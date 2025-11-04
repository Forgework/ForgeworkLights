"""
Constants and configuration for ForgeworkLights TUI
"""
from pathlib import Path


# File paths
STATE_FILE = Path.home() / ".cache/omarchy-argb/state.json"
BRIGHTNESS_FILE = Path.home() / ".config/omarchy-argb/brightness"
THEMES_DB_PATH = Path.home() / ".config/omarchy-argb/themes.json"
THEME_SYMLINK = Path.home() / ".config/omarchy/current/theme"
LED_THEME_FILE = Path.home() / ".config/omarchy-argb/led-theme"

# Daemon binary
DAEMON_BINARY = "/usr/local/bin/omarchy-argb"

# UI Settings
MIN_WIDTH = 60
AUTO_REFRESH_INTERVAL = 2.0  # seconds
