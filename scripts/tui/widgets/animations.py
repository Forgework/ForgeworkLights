"""
Animations Panel - Select and apply LED animations
"""
from textual.widgets import Static
from textual.containers import Vertical
from textual.reactive import reactive
from textual.app import ComposeResult
from textual.message import Message
from textual import events


class AnimationsPanel(Static):
    """
    Panel for selecting LED animations
    """
    
    class AnimationSelected(Message):
        """Message when an animation is selected"""
        def __init__(self, animation_name: str):
            super().__init__()
            self.animation_name = animation_name
    
    selected_animation = reactive("static")
    focused_index = reactive(0)
    
    # Available animations
    ANIMATIONS = [
        ("static", "Static - No animation"),
        ("breathe", "Breathe - Slow fade in/out"),
        ("wave", "Wave - Left to right flowing"),
        ("rainbow", "Rainbow - Cycling colors"),
        ("ripple", "Ripple - Center outward pulse"),
        ("meteor", "Meteor - Shooting stars"),
        ("bounce", "Bounce - Back and forth"),
        ("sparkle", "Sparkle - Random twinkling"),
        ("strobe", "Strobe - Fast flashing"),
        ("gradient-shift", "Gradient Shift - Smooth color transitions"),
    ]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.can_focus = True
    
    def compose(self) -> ComposeResult:
        """Compose the animations list"""
        with Vertical(id="animations-content"):
            yield Static("", id="animations-list")
    
    def on_mount(self) -> None:
        """Initialize display"""
        self._update_display()
    
    def _update_display(self) -> None:
        """Update the animations list display"""
        lines = []
        
        for idx, (anim_id, anim_name) in enumerate(self.ANIMATIONS):
            # Selection indicator
            if anim_id == self.selected_animation:
                arrow = "▶"
            else:
                arrow = " "
            
            # Focus indicator
            if idx == self.focused_index and self.has_focus:
                # Focused item - highlighted in yellow (matching app style)
                line = f"[bold #f9e2af]{arrow} {anim_name}[/]"
            elif anim_id == self.selected_animation:
                # Selected but not focused - green
                line = f"[#a6e3a1]{arrow} {anim_name}[/]"
            else:
                # Normal item - muted text
                line = f"[#6c7086]{arrow}[/] [#cdd6f4]{anim_name}[/]"
            
            lines.append(line)
        
        # Update display
        animations_list = self.query_one("#animations-list", Static)
        animations_list.update("\n".join(lines))
    
    def on_key(self, event: events.Key) -> None:
        """Handle keyboard navigation"""
        if event.key == "up":
            self.focused_index = max(0, self.focused_index - 1)
            self._update_display()
            event.prevent_default()
        elif event.key == "down":
            self.focused_index = min(len(self.ANIMATIONS) - 1, self.focused_index + 1)
            self._update_display()
            event.prevent_default()
        elif event.key == "enter":
            # Select the focused animation
            anim_id, anim_name = self.ANIMATIONS[self.focused_index]
            self.selected_animation = anim_id
            self._update_display()
            self.post_message(self.AnimationSelected(anim_id))
            event.prevent_default()
    
    def on_focus(self, event: events.Focus) -> None:
        """Update display when focused"""
        self._update_display()
    
    def on_blur(self, event: events.Blur) -> None:
        """Update display when focus lost"""
        self._update_display()
    
    def watch_selected_animation(self, new_value: str) -> None:
        """React to selection changes"""
        self._update_display()
    
    def watch_focused_index(self, new_value: int) -> None:
        """React to focus changes"""
        self._update_display()
