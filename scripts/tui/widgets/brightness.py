"""
Brightness panel widget for ForgeworkLights TUI
"""
from textual.widgets import Static
from textual.reactive import reactive
from textual.message import Message

from .slider import Slider
from ..theme import THEME


class BrightnessPanel(Static):
    """Brightness controls with borders"""
    
    class BrightnessChanged(Message):
        """Message when brightness is changed via click"""
        def __init__(self, value: int):
            super().__init__()
            self.value = value
    
    BINDINGS = [
        ("left", "brightness_down", "Decrease brightness"),
        ("right", "brightness_up", "Increase brightness"),
    ]
    
    brightness = reactive(100)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.can_focus = True
    
    def compose(self):
        """Compose the brightness slider using the shared Slider widget."""
        yield Slider(
            min_value=0,
            max_value=100,
            label="Brightness",
            suffix="%",
            color=THEME["button_fg"],
            width=80,
            boxed=True,
            border_color=THEME["box_outline"],
            auto_width=False,
            label_color=THEME["main_fg"],
            arrows_color=THEME["hi_fg"],
            label_indent=3,
            step_size=1,
            id="brightness-slider",
        )
    
    def on_mount(self) -> None:
        """Initialize slider value from brightness reactive state."""
        try:
            slider = self.query_one("#brightness-slider", Slider)
            slider._suppress_message = True
            slider.value = int(self.brightness)
            slider._suppress_message = False
        except Exception:
            pass
    
    def watch_brightness(self, old_value: int, new_value: int) -> None:
        """Keep the internal Slider in sync when brightness is updated externally."""
        try:
            slider = self.query_one("#brightness-slider", Slider)
            slider._suppress_message = True
            slider.value = int(new_value)
            slider._suppress_message = False
        except Exception:
            pass
    
    def on_slider_value_changed(self, message: Slider.ValueChanged) -> None:
        """Handle changes from the embedded Slider and emit BrightnessChanged."""
        try:
            # Update reactive state
            self.brightness = int(message.value)
            # Re-emit in the existing BrightnessChanged format for the App handler
            self.post_message(self.BrightnessChanged(self.brightness))
        except Exception:
            pass
    
    def action_brightness_up(self) -> None:
        """Increase brightness by 1%"""
        new_brightness = min(100, int(self.brightness) + 1)
        self.brightness = new_brightness
        self.post_message(self.BrightnessChanged(new_brightness))
    
    def action_brightness_down(self) -> None:
        """Decrease brightness by 1%"""
        new_brightness = max(0, int(self.brightness) - 1)
        self.brightness = new_brightness
        self.post_message(self.BrightnessChanged(new_brightness))
