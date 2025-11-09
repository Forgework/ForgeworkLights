"""
Parameter Slider - Reusable slider widget for animation parameters
"""
from textual.widgets import Static
from textual.reactive import reactive
from textual.message import Message
import re


class ParameterSlider(Static):
    """Interactive slider for a single parameter"""
    
    class ValueChanged(Message):
        """Message when slider value is changed"""
        def __init__(self, param_name: str, value: float):
            super().__init__()
            self.param_name = param_name
            self.value = value
    
    value = reactive(0.0)
    is_focused = reactive(False)
    
    def __init__(
        self,
        param_name: str,
        display_name: str,
        min_val: float,
        max_val: float,
        default: float,
        step: float,
        unit: str,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.param_name = param_name
        self.display_name = display_name
        self.min_val = min_val
        self.max_val = max_val
        self.default = default
        self.step = step
        self.unit = unit
        self.value = default
        self.can_focus = True
    
    def render(self) -> str:
        """Render the slider"""
        width = max(40, self.size.width if self.size.width > 0 else 40)
        
        # Format value based on type
        if isinstance(self.default, int):
            value_str = f"{int(self.value)}"
        else:
            value_str = f"{self.value:.2f}"
        
        # Label and value display
        label = f"{self.display_name}: "
        suffix = f" {value_str} {self.unit}"
        slider_width = max(10, width - len(label) - len(suffix))
        
        # Calculate filled portion (normalized to 0-1)
        normalized = (self.value - self.min_val) / (self.max_val - self.min_val)
        filled = int(normalized * slider_width)
        empty = slider_width - filled
        
        # Choose color based on focus
        if self.is_focused:
            color = "yellow"
            bar_char = "━"
        else:
            color = "cyan"
            bar_char = "─"
        
        # Create slider bar
        bar = f"[{color}]{bar_char * filled}[/][dim]{bar_char * empty}[/dim]"
        
        return f"{label}{bar}{suffix}"
    
    def on_click(self, event) -> None:
        """Handle clicks on the slider"""
        # Take focus when clicked
        self.focus()
        
        # Stop event propagation to prevent parent from handling it
        event.stop()
        
        # Calculate slider position in the rendered output
        label = f"{self.display_name}: "
        
        if isinstance(self.default, int):
            value_str = f"{int(self.value)}"
        else:
            value_str = f"{self.value:.2f}"
        suffix = f" {value_str} {self.unit}"
        
        width = max(40, self.size.width if self.size.width > 0 else 40)
        slider_width = max(10, width - len(label) - len(suffix))
        
        slider_start = len(label)
        slider_end = slider_start + slider_width
        
        x = event.x
        
        # Check if click is within slider bounds
        if slider_start <= x < slider_end:
            # Calculate new value from click position
            click_pos = x - slider_start
            normalized = click_pos / slider_width
            new_value = self.min_val + (normalized * (self.max_val - self.min_val))
            
            # Snap to step increments
            new_value = round(new_value / self.step) * self.step
            new_value = max(self.min_val, min(self.max_val, new_value))
            
            self.value = new_value
            self.post_message(self.ValueChanged(self.param_name, new_value))
    
    def on_key(self, event) -> None:
        """Handle keyboard input for slider adjustment and navigation"""
        # Value adjustment keys
        if event.key in ("equals", "plus"):
            self._adjust_value(1)
            event.stop()
            return
        elif event.key in ("minus", "underscore"):
            self._adjust_value(-1)
            event.stop()
            return
        # Arrow key navigation between sliders
        elif event.key in ("up", "down"):
            # Find all sliders in parent container
            container = self.parent
            if container:
                sliders = list(container.query(ParameterSlider))
                if len(sliders) > 1:
                    try:
                        current_idx = sliders.index(self)
                        if event.key == "up" and current_idx > 0:
                            sliders[current_idx - 1].focus()
                            event.stop()
                        elif event.key == "down" and current_idx < len(sliders) - 1:
                            sliders[current_idx + 1].focus()
                            event.stop()
                    except ValueError:
                        pass
    
    def _adjust_value(self, direction: int) -> None:
        """Adjust value by step amount in given direction"""
        new_value = self.value + (direction * self.step)
        new_value = max(self.min_val, min(self.max_val, new_value))
        
        # Update value and trigger re-render
        old_value = self.value
        self.value = new_value
        
        # Only post message if value actually changed
        if old_value != new_value:
            self.post_message(self.ValueChanged(self.param_name, new_value))
            self.refresh()  # Force visual update
    
    def on_focus(self) -> None:
        """Mark as focused"""
        self.is_focused = True
    
    def on_blur(self) -> None:
        """Mark as unfocused"""
        self.is_focused = False
    
    def set_value(self, value: float) -> None:
        """Set the slider value programmatically"""
        self.value = max(self.min_val, min(self.max_val, value))
