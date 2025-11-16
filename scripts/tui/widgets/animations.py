"""
Animations Panel - Select and apply LED animations with parameters
"""
from textual.widgets import Static
from textual.containers import Vertical, Horizontal, VerticalScroll
from textual.reactive import reactive
from textual.app import ComposeResult
from textual.message import Message
from textual import events
import json
import sys
from ..animations import ANIMATIONS, ANIMATIONS_LIST
from ..constants import ANIMATION_FILE, ANIMATION_PARAMS_FILE
from .parameter_slider import ParameterSlider
from ..theme import THEME


class AnimationsList(Vertical):
    """Focusable container for animation list"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.can_focus = True
    
    def on_key(self, event: events.Key) -> None:
        """Handle keyboard navigation in list"""
        # Get parent to access current state
        panel = self.parent
        while panel and not isinstance(panel, AnimationsPanel):
            panel = panel.parent
        
        if not panel:
            return
        
        if event.key == "up":
            new_index = max(0, panel.focused_index - 1)
            self.post_message(AnimationsPanel.ListNavigated(new_index))
            event.stop()
        elif event.key == "down":
            max_index = len(panel.ANIMATIONS_LIST) - 1
            new_index = min(max_index, panel.focused_index + 1)
            self.post_message(AnimationsPanel.ListNavigated(new_index))
            event.stop()
        elif event.key == "enter":
            self.post_message(AnimationsPanel.ListSelected(panel.focused_index))
            event.stop()


class ParametersContainer(VerticalScroll):
    """Container for parameter sliders"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.can_focus = False  # Container doesn't take focus, sliders do


class AnimationsPanel(Static):
    """
    Panel for selecting LED animations with parameter controls
    """
    
    class AnimationSelected(Message):
        """Message when an animation is selected"""
        def __init__(self, animation_name: str, params: dict):
            super().__init__()
            self.animation_name = animation_name
            self.params = params
    
    class ListNavigated(Message):
        """Internal message when list navigation occurs"""
        def __init__(self, index: int):
            super().__init__()
            self.index = index
    
    class ListSelected(Message):
        """Internal message when list item is selected"""
        def __init__(self, index: int):
            super().__init__()
            self.index = index
    
    selected_animation = reactive("static")
    focused_index = reactive(0)
    
    # Available animations
    ANIMATIONS_LIST = ANIMATIONS_LIST
    animation_params = {}
    sliders = []  # Track mounted sliders
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.can_focus = False  # Parent doesn't need focus - children handle it
    
    def compose(self) -> ComposeResult:
        """Compose split view: animations list (left) and parameters (right)"""
        with Horizontal(id="animations-content"):
            with AnimationsList(id="animations-left", classes="animations-section"):
                yield Static("", id="animations-list")
            with ParametersContainer(id="animations-right", classes="animations-section"):
                yield Static("", id="animations-params-header")
    
    def on_mount(self) -> None:
        """Initialize display and load current animation"""
        # Load parameters from file
        self._load_params()
        
        # Load current animation from config file
        if ANIMATION_FILE.exists():
            self.selected_animation = ANIMATION_FILE.read_text().strip()
        
        self._update_display()
    
    def _load_params(self) -> None:
        """Load animation parameters from JSON file"""
        if ANIMATION_PARAMS_FILE.exists():
            try:
                self.animation_params = json.loads(ANIMATION_PARAMS_FILE.read_text())
                print(f"[AnimationsPanel] Loaded params from {ANIMATION_PARAMS_FILE}", file=sys.stderr)
            except Exception as e:
                print(f"[AnimationsPanel] Failed to load params: {e}", file=sys.stderr)
                self.animation_params = {}
        else:
            self.animation_params = {}
    
    def _save_params(self) -> None:
        """Save animation parameters to JSON file"""
        try:
            ANIMATION_PARAMS_FILE.parent.mkdir(parents=True, exist_ok=True)
            ANIMATION_PARAMS_FILE.write_text(json.dumps(self.animation_params, indent=2))
            print(f"[AnimationsPanel] Saved params to {ANIMATION_PARAMS_FILE}", file=sys.stderr)
        except Exception as e:
            print(f"[AnimationsPanel] Failed to save params: {e}", file=sys.stderr)
    
    def _get_param_value(self, anim_id: str, param_name: str, default: float) -> float:
        """Get parameter value or default"""
        if anim_id in self.animation_params:
            return self.animation_params[anim_id].get(param_name, default)
        return default
    
    def _update_display(self) -> None:
        """Update the animations list and parameters display"""
        # Update left side - animations list
        lines = []
        # Check if left container is focused
        left_container = self.query_one("#animations-left", AnimationsList)
        list_has_focus = left_container.has_focus
        
        for idx, (anim_id, anim_name) in enumerate(self.ANIMATIONS_LIST):
            if anim_id == self.selected_animation:
                arrow = "→"
            else:
                arrow = " "
            
            if idx == self.focused_index and list_has_focus:
                # Focused item - use theme highlight colors
                line = f"[bold {THEME['hi_fg']} on {THEME['selected_bg']}] {arrow} {anim_name}[/]"
            elif anim_id == self.selected_animation:
                # Selected but not focused - use theme title color
                line = f"[{THEME['title']}] {arrow} {anim_name}[/]"
            else:
                # Unselected - use theme main foreground
                line = f"[{THEME['main_fg']}] {arrow} {anim_name}[/]"
            
            lines.append(line)
        
        animations_list = self.query_one("#animations-list", Static)
        animations_list.update("\n".join(lines))
        
        # Update right side - parameters
        self._update_params_display()
    
    def _update_params_display(self) -> None:
        """Update the parameters display for selected animation - mount sliders"""
        # Remove existing sliders
        for slider in self.sliders:
            slider.remove()
        self.sliders = []
        
        # Update header
        header = self.query_one("#animations-params-header", Static)
        
        if self.selected_animation not in ANIMATIONS:
            header.update(f"[{THEME['inactive_fg']}]No parameters[/]")
            return
        
        anim_data = ANIMATIONS[self.selected_animation]
        if not anim_data["params"]:
            header.update(f"[bold {THEME['title']}]{anim_data['name']}[/]\n[{THEME['inactive_fg']}]No adjustable parameters[/]")
            return
        
        header.update(f"[bold {THEME['title']}]{anim_data['name']} Parameters:[/]\n")
        
        # Mount sliders for each parameter
        params_container = self.query_one("#animations-right")
        for param_name, display_name, min_val, max_val, default, step, unit in anim_data["params"]:
            current = self._get_param_value(self.selected_animation, param_name, default)
            
            slider = ParameterSlider(
                param_name=param_name,
                display_name=display_name,
                min_val=min_val,
                max_val=max_val,
                default=default,
                step=step,
                unit=unit
            )
            slider.set_value(current)
            self.sliders.append(slider)
            params_container.mount(slider)
    
    def on_parameter_slider_value_changed(self, message: ParameterSlider.ValueChanged) -> None:
        """Handle slider value changes"""
        # Save to params dict
        if self.selected_animation not in self.animation_params:
            self.animation_params[self.selected_animation] = {}
        self.animation_params[self.selected_animation][message.param_name] = message.value
        
        # Save to file and apply
        self._save_params()
        self._apply_animation()
        message.stop()  # Prevent bubbling
    
    def on_animations_panel_list_navigated(self, message: ListNavigated) -> None:
        """Handle animation list navigation"""
        self.focused_index = message.index
        self._update_display()
        message.stop()
    
    def on_animations_panel_list_selected(self, message: ListSelected) -> None:
        """Handle animation list selection"""
        anim_id, anim_name = self.ANIMATIONS_LIST[message.index]
        self.selected_animation = anim_id
        self._apply_animation()
        message.stop()
    
    def _apply_animation(self) -> None:
        """Apply the current animation with parameters"""
        params = self.animation_params.get(self.selected_animation, {})
        self.post_message(self.AnimationSelected(self.selected_animation, params))
        self._update_display()
    
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
    
    def on_click(self, event) -> None:
        """Handle clicks on animation items - only in left half"""
        x = event.x
        y = event.y
        
        # Only handle clicks in the left half (animations list)
        width = self.size.width
        if x < width // 2 and 0 <= y < len(self.ANIMATIONS_LIST):
            anim_id, anim_name = self.ANIMATIONS_LIST[y]
            self.focused_index = y
            self.selected_animation = anim_id
            self._apply_animation()
