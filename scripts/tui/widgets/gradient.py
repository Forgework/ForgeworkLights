"""
Gradient panel widget for ForgeworkLights TUI
"""
import json
from pathlib import Path
from textual.containers import ScrollableContainer
from textual.widgets import Static
from textual.reactive import reactive
from textual.app import ComposeResult
from textual.message import Message

from ..constants import THEMES_DB_PATH, THEME_SYMLINK, LED_THEME_FILE


class GradientPanel(ScrollableContainer):
    """Display all themes with their gradients and key colors - interactive selection"""
    
    class ThemeSelected(Message):
        """Message when a theme is selected"""
        def __init__(self, theme_name: str, match_omarchy: bool = False):
            super().__init__()
            self.theme_name = theme_name
            self.match_omarchy = match_omarchy
    
    current_theme = reactive("")
    selected_index = reactive(0)
    is_focused = reactive(False)
    
    BINDINGS = [
        ("up", "select_previous", "Previous theme"),
        ("down", "select_next", "Next theme"),
        ("enter", "apply_theme", "Apply theme"),
    ]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._content = Static("", id="gradient-content")
        self._content.can_focus = False  # Prevent inner widget from stealing focus
        self._theme_list = []  # Store theme keys for navigation
        self.can_focus = True
    
    def compose(self) -> ComposeResult:
        yield self._content
    
    def watch_current_theme(self, theme: str) -> None:
        """Update display when theme changes"""
        self._update_display()
    
    def on_mount(self) -> None:
        """Initial display"""
        self._update_display()
    
    def on_resize(self) -> None:
        """Refresh display on resize"""
        self._update_display()
    
    def _update_display(self) -> None:
        """Render theme list with selection highlighting"""
        width = max(60, self.size.width if self.size.width > 0 else 70)
        content_width = width - 4  # Account for borders │  │
        
        lines = []
        self._theme_list = []
        
        # Use reactive focus state - only show selection highlight if focused
        show_highlight = self.is_focused
        
        # Get current Omarchy theme
        omarchy_theme_name = "Unknown"
        try:
            if THEME_SYMLINK.exists() and THEME_SYMLINK.is_symlink():
                theme_dir = THEME_SYMLINK.resolve()
                omarchy_theme_name = theme_dir.name
        except:
            pass
        
        # Get current LED theme setting
        led_theme = "match"
        try:
            if LED_THEME_FILE.exists():
                led_theme = LED_THEME_FILE.read_text().strip()
        except:
            pass
        
        try:
            # Add blank line at top (below Theme Selection border)
            blank_padding = max(1, width - 2)  # -2 for borders
            lines.append(f"[cyan]│{' ' * blank_padding}│[/]")
            
            # Add "Match Omarchy Theme" option at the top
            self._theme_list.append("__MATCH_OMARCHY__")
            is_selected = self.selected_index == 0
            marker = "→" if led_theme == "match" else " "
            
            display_name = f"Match Omarchy ({omarchy_theme_name})"
            
            # Calculate visible content length: marker(1) + space(1) + display_name + space(1)
            visible_len = 1 + 1 + len(display_name) + 1
            padding_needed = max(1, width - visible_len - 2)  # -2 for borders
            
            # Highlight if selected AND focused
            if is_selected and show_highlight:
                line = f"│[bold yellow on #3b4261] {marker} {display_name}{' ' * padding_needed}[/]│"
            else:
                line = f"│ {marker} {display_name}{' ' * padding_needed}│"
            
            lines.append(f"[cyan]{line}[/]")
            
            # Add blank line after Match Omarchy
            blank_padding = max(1, width - 2)  # -2 for borders
            lines.append(f"[cyan]│{' ' * blank_padding}│[/]")
            
            # Load and display themes from database
            if THEMES_DB_PATH.exists():
                db_data = json.loads(THEMES_DB_PATH.read_text())
                if "themes" in db_data:
                    for idx, theme_key in enumerate(sorted(db_data["themes"].keys()), start=1):
                        theme_data = db_data["themes"][theme_key]
                        colors = theme_data.get("colors", [])
                        theme_name = theme_data.get("name", theme_key)
                        
                        if len(colors) >= 3:
                            self._theme_list.append(theme_key)
                            
                            # Extract key colors (first, middle, last)
                            key_colors = [colors[0], colors[len(colors)//2], colors[-1]]
                            
                            # Mark current LED theme (not Omarchy theme)
                            marker = "→" if theme_key == led_theme else " "
                            is_selected = self.selected_index == idx
                            
                            # Create mini gradient (shorter for list view)
                            gradient_width = min(30, content_width - 40)
                            gradient = self._create_gradient_preview(colors, gradient_width)
                            
                            # Format: "→ Theme Name    ▄▄▄▄▄    #hex1 #hex2 #hex3"
                            hex_str = f"{key_colors[0]} {key_colors[1]} {key_colors[2]}"
                            name_padded = f"{theme_name[:18]:<18}"
                            
                            # Calculate visible content length (without Rich markup)
                            # marker(1) + space(1) + name(18) + space(1) + gradient(width) + space(1) + hex_str(23) + space(1)
                            visible_len = 1 + 1 + 18 + 1 + gradient_width + 1 + 23 + 1
                            padding_needed = max(1, width - visible_len - 2)  # -2 for borders
                            
                            # Build line with selection highlight (only when focused)
                            if is_selected and show_highlight:
                                line = f"│[bold yellow on #3b4261] {marker} {name_padded} {gradient} {hex_str}{' ' * padding_needed}[/]│"
                            else:
                                line = f"│ {marker} {name_padded} {gradient} {hex_str}{' ' * padding_needed}│"
                            
                            lines.append(f"[cyan]{line}[/]")
                    
                    # Add blank line after theme list
                    if self._theme_list:  # Only if themes were added
                        blank_padding = max(1, width - 2)  # -2 for borders
                        lines.append(f"[cyan]│{' ' * blank_padding}│[/]")
            
            if len(lines) <= 1:
                empty_text = "No themes found"
                padding = max(0, width - len(empty_text) - 3)
                lines.append(f"[cyan]│ {empty_text}{' ' * padding}│[/]")
                
        except Exception as e:
            error_text = f"Error loading themes: {e}"
            padding = max(0, width - len(error_text) - 3)
            lines.append(f"[cyan]│ {error_text}{' ' * padding}│[/]")
        
        self._content.update("\n".join(lines))
    
    def watch_selected_index(self, index: int) -> None:
        """Update display when selection changes"""
        self._update_display()
    
    def watch_is_focused(self, focused: bool) -> None:
        """Update display when focus state changes"""
        self._update_display()
    
    def on_focus(self) -> None:
        """Update focus state when gaining focus"""
        self.is_focused = True
    
    def on_blur(self) -> None:
        """Update focus state when losing focus"""
        self.is_focused = False
    
    def action_select_previous(self) -> None:
        """Select previous theme"""
        if self._theme_list:
            self.selected_index = (self.selected_index - 1) % len(self._theme_list)
    
    def action_select_next(self) -> None:
        """Select next theme"""
        if self._theme_list:
            self.selected_index = (self.selected_index + 1) % len(self._theme_list)
    
    def action_apply_theme(self) -> None:
        """Apply the selected theme"""
        if not self._theme_list or self.selected_index >= len(self._theme_list):
            return
        
        selected_theme = self._theme_list[self.selected_index]
        if selected_theme == "__MATCH_OMARCHY__":
            self.post_message(self.ThemeSelected("", match_omarchy=True))
        else:
            self.post_message(self.ThemeSelected(selected_theme, match_omarchy=False))
    
    def on_click(self, event) -> None:
        """Handle clicks on theme items"""
        # Calculate which line was clicked
        # Layout: blank line (0), Match Omarchy (1), blank line (2), themes start at (3)
        y = event.y
        
        # Adjust for padding: 1 blank line + 1 match omarchy + 1 blank line = 3 lines offset
        # But Match Omarchy is at y=1 (index 0)
        # First real theme is at y=3 (index 1)
        if y == 0:
            # Blank line at top, ignore
            return
        elif y == 1:
            # Match Omarchy option
            self.selected_index = 0
            self.action_apply_theme()
        elif y == 2:
            # Blank line after Match Omarchy, ignore
            return
        elif 3 <= y < len(self._theme_list) + 2:
            # Theme list starts at y=3, which is index 1
            self.selected_index = y - 2
            self.action_apply_theme()
    
    def _create_gradient_preview(self, colors: list, width: int) -> str:
        """Create a visual gradient using colored blocks (matches daemon interpolation)"""
        blocks = []
        
        # Parse hex colors to RGB
        def hex_to_rgb(hex_color):
            hex_color = hex_color.lstrip('#')
            return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        
        def rgb_to_hex(r, g, b):
            return f"#{int(r):02x}{int(g):02x}{int(b):02x}"
        
        rgb_colors = [hex_to_rgb(c) for c in colors]
        num_colors = len(rgb_colors)
        
        if num_colors < 2:
            # Single color or no colors
            hex_color = colors[0] if colors else "#808080"
            return f"[{hex_color}]▄[/]" * width
        
        for i in range(width):
            # Map LED position to color gradient (same algorithm as daemon)
            pos = i / (width - 1) if width > 1 else 0  # 0.0 to 1.0
            color_pos = pos * (num_colors - 1)  # 0.0 to (num_colors-1)
            
            idx = int(color_pos)
            frac = color_pos - idx
            
            if idx >= num_colors - 1:
                # Last color
                r, g, b = rgb_colors[num_colors - 1]
            else:
                # Interpolate between idx and idx+1
                c1 = rgb_colors[idx]
                c2 = rgb_colors[idx + 1]
                r = c1[0] + (c2[0] - c1[0]) * frac
                g = c1[1] + (c2[1] - c1[1]) * frac
                b = c1[2] + (c2[2] - c1[2]) * frac
            
            hex_color = rgb_to_hex(r, g, b)
            blocks.append(f"[{hex_color}]▄[/]")
        
        return "".join(blocks)
