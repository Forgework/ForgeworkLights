"""
Status panel widget for ForgeworkLights TUI
"""
from pathlib import Path
from textual.widgets import Static
from textual.reactive import reactive

# Import paths from constants
THEME_SYMLINK = Path.home() / ".config/omarchy/current/theme"
LED_THEME_FILE = Path.home() / ".config/forgeworklights/led-theme"


class StatusPanel(Static):
    """Display daemon status information"""
    
    daemon_status = reactive("Unknown")
    current_theme = reactive("")  # Changed to match gradient panel pattern
    brightness_value = reactive(100)
    
    def watch_daemon_status(self, status: str) -> None:
        """Update display when daemon status changes"""
        self.refresh()
    
    def watch_current_theme(self, theme: str) -> None:
        """Update display when theme changes - EXACT COPY from gradient panel"""
        self.refresh()
    
    def watch_brightness_value(self, brightness: int) -> None:
        """Update display when brightness changes"""
        self.refresh()
    
    def render(self) -> str:
        width = max(60, self.size.width if self.size.width > 0 else 70)
        content_width = width - 2  # Account for │  │
        
        # Read LED theme preference - match gradient panel pattern
        led_theme = "match"
        try:
            if LED_THEME_FILE.exists():
                led_theme = LED_THEME_FILE.read_text().strip()
        except:
            pass
        
        # Get theme display - read symlink directly like gradient panel does
        if led_theme == "match":
            # Get current Omarchy theme by reading symlink directly
            omarchy_theme_name = "Unknown"
            try:
                if THEME_SYMLINK.exists() and THEME_SYMLINK.is_symlink():
                    theme_dir = THEME_SYMLINK.resolve()
                    omarchy_theme_name = theme_dir.name.capitalize()
            except:
                pass
            theme_display = f"Match ({omarchy_theme_name})"
        else:
            # Use specific LED theme name
            theme_display = led_theme.capitalize()
        
        # Format status lines
        daemon_text = f"Daemon: {self.daemon_status}"
        theme_text = f"Theme: {theme_display}"
        brightness_text = f"Brightness: {self.brightness_value}%"
        
        # Pad each line to content width
        daemon_line = f"│ {daemon_text:<{content_width-1}}│"
        theme_line = f"│ {theme_text:<{content_width-1}}│"
        brightness_line = f"│ {brightness_text:<{content_width-1}}│"
        
        return f"[cyan]{daemon_line}[/]\n[cyan]{theme_line}[/]\n[cyan]{brightness_line}[/]"
