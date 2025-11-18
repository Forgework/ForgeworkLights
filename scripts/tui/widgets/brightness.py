"""
Brightness panel widget for ForgeworkLights TUI
"""
from textual.widgets import Static
from textual.reactive import reactive
from textual.message import Message
import re


class BrightnessPanel(Static):
    """Brightness controls with borders"""
    
    class BrightnessChanged(Message):
        """Message when brightness is changed via click"""
        def __init__(self, value: int):
            super().__init__()
            self.value = value
    
    brightness = reactive(100)
    
    def render(self) -> str:
        width = max(60, self.size.width if self.size.width > 0 else 70)
        content_width = width - 2  # Account for │  │
        
        # Calculate slider bar width
        label = f" {self.brightness:3d}%"
        prefix = " [dim](click to adjust)[/] "
        clean_prefix = re.sub(r'\[.*?\]', '', prefix)
        slider_width = max(10, content_width - len(clean_prefix) - len(label) - 1)
        
        # Calculate filled portion
        filled = int((self.brightness / 100) * slider_width)
        empty = slider_width - filled
        
        # Create slider bar
        bar = f"[yellow]{'━' * filled}[/][dim]{'━' * empty}[/dim]"
        
        # Format with proper padding
        content = f"{prefix}{bar}{label}"
        # Strip Rich markup to get actual display length
        clean_content = re.sub(r'\[.*?\]', '', content)
        padding = max(0, content_width - len(clean_content))
        
        line = f"│{content}{' ' * padding}│"
        return f"[cyan]{line}[/]"
    
    def on_click(self, event) -> None:
        """Handle clicks on the brightness slider"""
        x = event.x
        width = max(60, self.size.width if self.size.width > 0 else 70)
        content_width = width - 2
        
        # Calculate slider position
        label = f" {self.brightness:3d}%"
        prefix = " [dim](click to adjust)[/] "
        clean_prefix = re.sub(r'\[.*?\]', '', prefix)
        slider_width = max(10, content_width - len(clean_prefix) - len(label) - 1)
        
        # Slider starts after: │ (1) + prefix
        slider_start = 1 + len(clean_prefix)
        slider_end = slider_start + slider_width
        
        # Check if click is within slider bounds
        if slider_start <= x < slider_end:
            # Calculate brightness from click position
            click_pos = x - slider_start
            new_brightness = int((click_pos / slider_width) * 100)
            new_brightness = max(0, min(100, new_brightness))  # Clamp to 0-100
            
            # Post message to parent app
            self.post_message(self.BrightnessChanged(new_brightness))
