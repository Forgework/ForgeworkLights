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
THEMES_DB_PATH = CONFIG_DIR / "themes.json"
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

# UI Settings
MIN_WIDTH = 60
AUTO_REFRESH_INTERVAL = 2.0  # seconds

# Logs Settings
DAEMON_SERVICE_NAME = "forgeworklights"
LOGS_MAX_LINES = 200  # Maximum lines to keep in memory
LOGS_INITIAL_LINES = 50  # Number of lines to fetch initially
LOGS_FETCH_TIMEOUT = 2  # seconds
LOGS_DEFAULT_WIDTH = 100  # fallback width if terminal size unavailable
