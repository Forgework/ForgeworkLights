"""
Countdown bar widget using Braille block characters
"""
from textual.widgets import Static
from textual.reactive import reactive
from textual.timer import Timer

from ..theme import THEME


class CountdownBar(Static):
    """
    A countdown progress bar using Braille characters.
    Shows ⣿ transitioning to ⣀ over time.
    """
    
    progress = reactive(1.0)  # 1.0 = full, 0.0 = empty
    
    def __init__(self, width: int = 20, color: str | None = None, **kwargs):
        super().__init__(**kwargs)
        self.bar_width = width
        self.bar_color = color or THEME["button_fg"]
        self.timer: Timer | None = None
    
    def render(self) -> str:
        """Render the countdown bar with smooth height transition"""
        # Braille characters for smooth vertical transition (4 dots → 1 dot)
        # ⣿ full → ⣾ → ⣼ → ⣸ → ⣰ → ⣠ → ⣀ minimal
        transition_chars = ["⣀", "⣠", "⣰", "⣸", "⣼", "⣾", "⣿"]
        
        result = []
        for i in range(self.bar_width):
            # Calculate position-based progress (0.0 to 1.0)
            pos_progress = (i / self.bar_width) if self.bar_width > 0 else 0
            
            # If we're past the current progress point, show minimal (⣀)
            if pos_progress > self.progress:
                result.append("⣀")
            else:
                # Calculate how "full" this position should be
                # The closer to the progress edge, the more transition
                distance_from_edge = self.progress - pos_progress
                relative_fullness = min(1.0, distance_from_edge * self.bar_width / 3)
                
                # Pick character based on fullness
                char_index = int(relative_fullness * (len(transition_chars) - 1))
                result.append(transition_chars[char_index])
        
        bar = "".join(result)
        return f"[{self.bar_color}]{bar}[/]"
    
    def start_countdown(self, duration_seconds: float, on_complete=None):
        """
        Start countdown from full to empty over duration_seconds.
        
        Args:
            duration_seconds: Total time for countdown
            on_complete: Optional callback when countdown finishes
        """
        self.progress = 1.0
        self.on_complete_callback = on_complete
        
        # Update every 100ms for smooth animation
        update_interval = 0.1
        self.total_steps = int(duration_seconds / update_interval)
        self.current_step = 0
        
        # Cancel existing timer if any
        if self.timer:
            self.timer.stop()
        
        # Start new timer
        self.timer = self.set_interval(update_interval, self._update_progress)
    
    def _update_progress(self):
        """Update progress bar"""
        self.current_step += 1
        self.progress = max(0.0, 1.0 - (self.current_step / self.total_steps))
        
        if self.current_step >= self.total_steps:
            # Countdown complete
            if self.timer:
                self.timer.stop()
                self.timer = None
            
            # Call completion callback if provided
            if hasattr(self, 'on_complete_callback') and self.on_complete_callback:
                self.on_complete_callback()
    
    def stop(self):
        """Stop countdown and reset"""
        if self.timer:
            self.timer.stop()
            self.timer = None
        self.progress = 1.0
