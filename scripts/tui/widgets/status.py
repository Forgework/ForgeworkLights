"""
Status panel widget for ForgeworkLights TUI
"""
from pathlib import Path
from textual.widgets import Static
from textual.reactive import reactive

from ..theme import THEME

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
        
        # Format status lines (brightness is shown via dedicated slider widget)
        hint_text = " TAB to switch sections (shift=reverse)"
        daemon_text = f"Daemon: {self.daemon_status}"
        theme_text = f"Theme: {theme_display}"
        
        border_color = THEME["box_outline"]
        text_color = THEME["main_fg"]

        # Hint line matches other hints: dimmed text with themed borders, padded to full width
        hint_body = f"{hint_text:<{content_width}}"
        hint_line = f"[{border_color}]│[/][dim]{hint_body}[/][{border_color}]│[/]"

        # Status lines use main_fg with themed borders, indented by 3 spaces
        daemon_body = f"   {daemon_text:<{content_width-3}}"
        theme_body = f"   {theme_text:<{content_width-3}}"
        daemon_line = f"[{border_color}]│[/][{text_color}]{daemon_body}[/][{border_color}]│[/]"
        theme_line = f"[{border_color}]│[/][{text_color}]{theme_body}[/][{border_color}]│[/]"

        return f"{hint_line}\n{daemon_line}\n{theme_line}"
