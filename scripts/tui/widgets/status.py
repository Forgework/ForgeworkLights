"""
Status panel widget for ForgeworkLights TUI
"""
from textual.widgets import Static
from textual.reactive import reactive


class StatusPanel(Static):
    """Display daemon status information"""
    
    daemon_status = reactive("Unknown")
    theme_name = reactive("Unknown")
    brightness_value = reactive(100)
    
    def render(self) -> str:
        width = max(60, self.size.width if self.size.width > 0 else 70)
        content_width = width - 2  # Account for │  │
        
        # Format status lines
        daemon_text = f"Daemon: {self.daemon_status}"
        theme_text = f"Theme: {self.theme_name}"
        brightness_text = f"Brightness: {self.brightness_value}%"
        
        # Pad each line to content width
        daemon_line = f"│ {daemon_text:<{content_width-1}}│"
        theme_line = f"│ {theme_text:<{content_width-1}}│"
        brightness_line = f"│ {brightness_text:<{content_width-1}}│"
        
        return f"[cyan]{daemon_line}[/]\n[cyan]{theme_line}[/]\n[cyan]{brightness_line}[/]"
