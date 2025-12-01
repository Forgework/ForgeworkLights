"""Reusable slider widget for ForgeworkLights TUI"""
from textual.widgets import Static
from textual.reactive import reactive
from textual.message import Message
import re

from ..theme import THEME


class Slider(Static):
    """Horizontal slider widget with value display"""
    
    class ValueChanged(Message):
        """Message when slider value is changed"""
        bubble = True  # Allow message to bubble to parent widgets
        
        def __init__(self, value: int, sender):
            super().__init__()
            self.value = value
            self.sender = sender
    
    # No arrow key bindings to avoid conflicts with parent navigation
    BINDINGS = []
    
    value = reactive(0)
    
    def __init__(self, min_value: int = 0, max_value: int = 100, 
                 label: str = "", suffix: str = "", color: str = "yellow",
                 width: int = 20, boxed: bool = False, border_color: str = "cyan",
                 auto_width: bool = False,
                 label_color: str | None = None,
                 arrows_color: str | None = None,
                 label_indent: int = 0,
                 step_size: int | None = None,
                 **kwargs):
        super().__init__(**kwargs)
        self.min_value = min_value
        self.max_value = max_value
        self.label = label
        self.suffix = suffix
        self.color = color
        self.slider_width = width
        self.boxed = boxed
        self.border_color = border_color
        self.auto_width = auto_width
        self.label_color = label_color
        self.arrows_color = arrows_color
        self.label_indent = max(0, int(label_indent))
        self.can_focus = False  # Don't take focus to avoid navigation conflicts
        # Default step preserves previous behavior (approx 5% of range) unless overridden.
        if step_size is not None:
            self.step = max(1, int(step_size))
        else:
            self.step = max(1, (max_value - min_value) // 20)  # ~5% increments
        self._suppress_message = False
    
    def watch_value(self, old_value: int, new_value: int) -> None:
        """Watch for value changes and post message"""
        with open("/tmp/slider_debug.log", "a") as f:
            f.write(f"[SLIDER {self.label}] watch_value: {old_value} -> {new_value}, suppress={self._suppress_message}, mounted={self.is_mounted}\n")
        
        if old_value != new_value and not self._suppress_message:
            with open("/tmp/slider_debug.log", "a") as f:
                f.write(f"[SLIDER {self.label}] POSTING MESSAGE: ValueChanged({new_value})\n")
            self.post_message(self.ValueChanged(new_value, self))
        else:
            with open("/tmp/slider_debug.log", "a") as f:
                f.write(f"[SLIDER {self.label}] NOT posting message (no change or suppressed)\n")
            
        if self.is_mounted:
            self.refresh()
    
    def render(self) -> str:
        # Calculate filled portion
        range_val = self.max_value - self.min_value
        if range_val > 0:
            filled_ratio = (self.value - self.min_value) / range_val
        else:
            filled_ratio = 0
        
        # Determine bar width: fixed slider_width by default, or expand to widget width
        if self.auto_width and self.size.width > 0:
            # Reserve space for label, value, space, bar, arrows (" ◀ ▶")
            if self.label:
                label_text = f"{self.label}:"
                if len(label_text) < 4:
                    label_text = label_text.ljust(4)
            else:
                label_text = ""
            value_text = f"{self.value}{self.suffix}"
            value_rjusted = value_text.rjust(4)
            arrows = " ◀ ▶"
            # 1 space before bar
            reserved = len(label_text) + len(value_rjusted) + 1 + len(arrows)
            if self.boxed:
                # Account for left/right borders
                available = max(0, self.size.width - 2 - reserved)
            else:
                available = max(0, self.size.width - reserved)
            bar_width = max(4, available)
        else:
            bar_width = self.slider_width

        filled = int(filled_ratio * bar_width)
        empty = bar_width - filled

        # Create slider bar using braille-style characters for a smooth look.
        filled_blocks: list[str] = []
        if filled > 0:
            filled_blocks = ["⣿"] * filled
            filled_blocks[-1] = "⣆"
        empty_char = "⣀"

        bar = f"[{self.color}]{''.join(filled_blocks)}[/][dim]{empty_char * empty}[/dim]"
        
        # Store rendered bar width for click handling
        self._rendered_bar_width = bar_width

        # Format label and value
        if self.label:
            label_text = f"{self.label}:"
            if len(label_text) < 4:
                label_text = label_text.ljust(4)
        else:
            label_text = ""
        
        value_text = f"{self.value}{self.suffix}"
        
        # Add clickable arrows on the right side
        arrows = " ◀ ▶"

        # Apply theming to label and arrows
        label_color = self.label_color or THEME["main_fg"]
        arrows_color = self.arrows_color or THEME["hi_fg"]
        indent = " " * self.label_indent

        if label_text:
            label_part = f"[{label_color}]{label_text}[/]"
        else:
            label_part = ""

        arrows_part = f"[{arrows_color}]{arrows}[/]"
        
        # Compact format: "R:255 ━━━━━ ◀ ▶" with optional indent
        content = f"{indent}{label_part}{value_text.rjust(4)} {bar}{arrows_part}"
        
        # Optional vertical borders for boxed style (used by brightness bar)
        if self.boxed:
            total_width = self.size.width if self.size.width > 0 else len(re.sub(r"\[.*?\]", "", content)) + 2
            inner_width = max(0, total_width - 2)
            plain = re.sub(r"\[.*?\]", "", content)
            padding = max(0, inner_width - len(plain))
            padded = f"{content}{' ' * padding}"
            return f"[{self.border_color}]│[/]{padded}[{self.border_color}]│[/]"
        
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
            # prefix_len is: optional left indent + label + value + space before bar
            prefix_len = self.label_indent + len(label_text) + len(value_rjusted) + 1
            
            # Bar occupies the rendered bar width characters starting at prefix_len.
            # For boxed sliders, the actual content is shifted by 1 due to the left border "│".
            bar_start = prefix_len + (1 if self.boxed else 0)
            bar_width = getattr(self, "_rendered_bar_width", self.slider_width)
            bar_end = bar_start + bar_width
            
            # After the bar we render " ◀ ▶" (4 characters including leading space)
            arrows_start = bar_end
            arrows_left = arrows_start + 1  # position of '◀'
            arrows_right = arrows_start + 3 # position of '▶'
            
            x = event.x
            
            # Check if click is within slider bar bounds
            if x >= bar_start and x < bar_end:
                # Calculate value from click position using the rendered bar width.
                # Use (bar_width - 1) as denominator so the last cell maps to max_value.
                click_pos = x - bar_start
                if bar_width > 1:
                    ratio = click_pos / (bar_width - 1)
                else:
                    ratio = 0
                new_value = self.min_value + int(ratio * (self.max_value - self.min_value))
                new_value = max(self.min_value, min(self.max_value, new_value))
                
                self.value = new_value
                event.stop()  # Prevent event from bubbling up
            # Check clicks on arrows: left arrow decreases, right arrow increases
            elif x == arrows_left:
                self.action_decrease()
                event.stop()
            elif x == arrows_right:
                self.action_increase()
                event.stop()
        except Exception as e:
            with open("/tmp/slider_debug.log", "a") as f:
                f.write(f"[SLIDER {self.label}] CLICK ERROR: {e}\n")
                import traceback
                f.write(traceback.format_exc())
    
    def action_increase(self) -> None:
        """Increase value"""
        new_value = min(self.max_value, self.value + self.step)
        if new_value != self.value:
            self.value = new_value
    
    def action_decrease(self) -> None:
        """Decrease value"""
        new_value = max(self.min_value, self.value - self.step)
        if new_value != self.value:
            self.value = new_value
