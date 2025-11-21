"""
Reusable slider widget for ForgeworkLights TUI
"""
from textual.widgets import Static
from textual.reactive import reactive
from textual.message import Message
import re
import sys
import traceback


class Slider(Static):
    """Horizontal slider widget with value display"""
    
    class ValueChanged(Message):
        """Message when slider value is changed"""
        def __init__(self, value: int):
            super().__init__()
            self.value = value
    
    BINDINGS = [
        ("left", "decrease", "Decrease value"),
        ("right", "increase", "Increase value"),
    ]
    
    value = reactive(0)
    
    def __init__(self, min_value: int = 0, max_value: int = 100, 
                 label: str = "", suffix: str = "", color: str = "yellow",
                 width: int = 20, **kwargs):
        super().__init__(**kwargs)
        self.min_value = min_value
        self.max_value = max_value
        self.label = label
        self.suffix = suffix
        self.color = color
        self.slider_width = width
        self.can_focus = True
        self.step = max(1, (max_value - min_value) // 20)  # 5% increments
    
    def render(self) -> str:
        # Calculate filled portion
        range_val = self.max_value - self.min_value
        if range_val > 0:
            filled_ratio = (self.value - self.min_value) / range_val
        else:
            filled_ratio = 0
        
        filled = int(filled_ratio * self.slider_width)
        empty = self.slider_width - filled
        
        # Create slider bar
        bar = f"[{self.color}]{'━' * filled}[/][dim]{'━' * empty}[/dim]"
        
        # Format label and value
        if self.label:
            label_text = f"{self.label}:"
            if len(label_text) < 4:
                label_text = label_text.ljust(4)
        else:
            label_text = ""
        
        value_text = f"{self.value}{self.suffix}"
        
        # Compact format: "R:255 ━━━━━"
        content = f"{label_text}{value_text.rjust(4)} {bar}"
        return content
    
    def on_click(self, event) -> None:
        """Handle clicks on the slider"""
        try:
            # Find where the bar starts in the rendered output (must match render() logic)
            if self.label:
                label_text = f"{self.label}:"
                if len(label_text) < 4:
                    label_text = label_text.ljust(4)
            else:
                label_text = ""
            
            value_text = f"{self.value}{self.suffix}"
            # The rjust(4) pads with spaces on the left to make it 4 chars total
            value_rjusted = value_text.rjust(4)
            prefix_len = len(label_text) + len(value_rjusted) + 1  # +1 for space before bar
            
            print(f"[SLIDER {self.label}] Click at x={event.x}, prefix_len={prefix_len}, slider_width={self.slider_width}", file=sys.stderr)
            print(f"  label_text='{label_text}' (len={len(label_text)})", file=sys.stderr)
            print(f"  value_text='{value_text}', rjusted='{value_rjusted}' (len={len(value_rjusted)})", file=sys.stderr)
            
            # Check if click is within slider bounds
            if event.x >= prefix_len and event.x < prefix_len + self.slider_width:
                # Calculate value from click position
                click_pos = event.x - prefix_len
                ratio = click_pos / self.slider_width
                new_value = self.min_value + int(ratio * (self.max_value - self.min_value))
                new_value = max(self.min_value, min(self.max_value, new_value))
                
                print(f"  click_pos={click_pos}, ratio={ratio:.3f}, new_value={new_value}", file=sys.stderr)
                
                self.value = new_value
                self.post_message(self.ValueChanged(new_value))
                self.refresh()
            else:
                print(f"  Click outside bounds (prefix_len={prefix_len}, max={prefix_len + self.slider_width})", file=sys.stderr)
        except Exception as e:
            print(f"Slider click error: {e}", file=sys.stderr)
            traceback.print_exc()
    
    def action_increase(self) -> None:
        """Increase value"""
        new_value = min(self.max_value, self.value + self.step)
        if new_value != self.value:
            self.value = new_value
            self.post_message(self.ValueChanged(new_value))
            self.refresh()
    
    def action_decrease(self) -> None:
        """Decrease value"""
        new_value = max(self.min_value, self.value - self.step)
        if new_value != self.value:
            self.value = new_value
            self.post_message(self.ValueChanged(new_value))
            self.refresh()
