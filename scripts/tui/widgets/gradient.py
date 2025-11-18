"""
Gradient panel widget for ForgeworkLights TUI
"""
import json
import re
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
    
    class ThemeEditRequested(Message):
        """Message when a theme edit is requested"""
        def __init__(self, theme_key: str, theme_name: str, colors: list):
            super().__init__()
            self.theme_key = theme_key
            self.theme_name = theme_name
            self.colors = colors
    
    class ThemeDeleteRequested(Message):
        """Message when a theme delete is requested"""
        def __init__(self, theme_key: str, theme_name: str):
            super().__init__()
            self.theme_key = theme_key
            self.theme_name = theme_name
    
    class ThemeSyncRequested(Message):
        """Message when theme sync is requested"""
        pass
    
    current_theme = reactive("")
    selected_index = reactive(0)
    selected_element = reactive("name")  # 'name', 'edit', or 'delete'
    is_focused = reactive(False)
    pending_delete_key = reactive(None)  # Track which theme is pending deletion
    
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
            # Add instruction line at top (below Theme Selection border)
            instruction = "[dim]↑↓ navigate, Enter apply, E edit, D delete[/]"
            clean_instruction = re.sub(r'\[.*?\]', '', instruction)
            padding = max(1, width - len(clean_instruction) - 2)  # -2 for borders
            lines.append(f"[cyan]│{instruction}{' ' * padding}│[/]")
            
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
                            
                            # Format: "→ Theme Name    ▄▄▄▄▄    #hex1 #hex2 #hex3 ... ✎ 🗑│"
                            hex_str = f"{key_colors[0]} {key_colors[1]} {key_colors[2]}"
                            name_padded = f"{theme_name[:18]:<18}"
                            
                            # Show confirmation message if this theme is pending deletion
                            # Note: 🗑 emoji and ✓ both take 2 char widths in most terminals, ✎ takes 1 char
                            if self.pending_delete_key == theme_key:
                                icons = " ✎ ✓"  # space(1) + edit(1) + space(1) + check(2) = 5, need 1 more space before border
                                icons_width = 5
                                trailing_spaces = 1
                            else:
                                icons = " ✎ 🗑"  # space(1) + edit(1) + space(1) + trash(2) = 5, need 1 more space before border
                                icons_width = 5
                                trailing_spaces = 1
                            
                            # Calculate visible content length (without Rich markup)
                            # marker(1) + space(1) + name(18) + space(1) + gradient(width) + space(1) + hex_str(23) + icons(width) + trailing_spaces + borders(2)
                            visible_len = 1 + 1 + 18 + 1 + gradient_width + 1 + 23 + icons_width + trailing_spaces + 2
                            padding_needed = max(1, width - visible_len)
                            
                            # Build line with selection highlight (only when focused)
                            # Highlight different parts based on selected_element
                            if is_selected and show_highlight:
                                if self.selected_element == "name":
                                    # Highlight theme name only
                                    line = f"│ {marker} [bold yellow on #3b4261]{name_padded}[/] {gradient} {hex_str}{' ' * padding_needed}{icons}{' ' * trailing_spaces}│"
                                elif self.selected_element == "edit":
                                    # Highlight edit icon with background (2 chars wide)
                                    if self.pending_delete_key == theme_key:
                                        # " ✎ ✓ " with edit highlighted (check is 2 chars wide)
                                        line = f"│ {marker} {name_padded} {gradient} {hex_str}{' ' * padding_needed} [bold yellow on #3b4261]✎ [/]✓ │"
                                    else:
                                        # " ✎ 🗑 " with edit highlighted
                                        line = f"│ {marker} {name_padded} {gradient} {hex_str}{' ' * padding_needed} [bold yellow on #3b4261]✎ [/]🗑 │"
                                elif self.selected_element == "delete":
                                    # Highlight delete icon with background (2 chars wide)
                                    if self.pending_delete_key == theme_key:
                                        # " ✎ ✓ " with checkmark highlighted (check is 2 chars wide)
                                        line = f"│ {marker} {name_padded} {gradient} {hex_str}{' ' * padding_needed} ✎ [bold yellow on #3b4261]✓[/] │"
                                    else:
                                        # " ✎ 🗑 " with trash highlighted (edit in normal color)
                                        line = f"│ {marker} {name_padded} {gradient} {hex_str}{' ' * padding_needed} ✎ [bold yellow on #3b4261]🗑[/] │"
                            else:
                                line = f"│ {marker} {name_padded} {gradient} {hex_str}{' ' * padding_needed}{icons}{' ' * trailing_spaces}│"
                            
                            lines.append(f"[cyan]{line}[/]")
                    
                    # Add blank line after theme list
                    if self._theme_list:  # Only if themes were added
                        blank_padding = max(1, width - 2)  # -2 for borders
                        lines.append(f"[cyan]│{' ' * blank_padding}│[/]")
                    
                    # Add Sync button in bottom right
                    sync_text = "Sync"
                    # Total visible length: sync_text + borders(2)
                    sync_padding = max(1, width - len(sync_text) - 2)
                    # Check if Sync is the selected element (last item in list)
                    is_sync_selected = (len(self._theme_list) > 0 and 
                                       self.selected_index == len(self._theme_list) and
                                       self.selected_element == "name")
                    
                    if is_sync_selected and show_highlight:
                        # Highlighted - yellow background
                        sync_line = f"[cyan]│{' ' * sync_padding}[bold yellow on #3b4261]{sync_text}[/]│[/]"
                    else:
                        # Normal - cyan text to match app theme
                        sync_line = f"[cyan]│{' ' * sync_padding}{sync_text}│[/]"
                    
                    lines.append(sync_line)
            
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
    
    def watch_selected_element(self, element: str) -> None:
        """Update display when selected element type changes"""
        self._update_display()
    
    def watch_is_focused(self, focused: bool) -> None:
        """Update display when focus state changes"""
        self._update_display()
    
    def watch_pending_delete_key(self, key: str) -> None:
        """Update display when pending deletion changes"""
        self._update_display()
    
    def on_focus(self) -> None:
        """Update focus state when gaining focus"""
        self.is_focused = True
    
    def on_blur(self) -> None:
        """Update focus state when losing focus"""
        self.is_focused = False
    
    def action_select_previous(self) -> None:
        """Select previous element (cycles through name, edit, delete for each theme)"""
        if not self._theme_list:
            return
        
        # Check if we're on the Sync button
        if self.selected_index == len(self._theme_list):
            # Go to last theme's delete icon
            self.selected_index = len(self._theme_list) - 1
            last_theme = self._theme_list[self.selected_index]
            if last_theme == "__MATCH_OMARCHY__":
                # Match Omarchy has no delete icon, stay on name
                self.selected_element = "name"
            else:
                self.selected_element = "delete"
            self.pending_delete_key = None
            return
        
        # Navigate backwards through elements
        if self.selected_element == "name":
            # Move to previous theme's delete icon (or name if Match Omarchy)
            if self.selected_index == 0:
                # Wrap to Sync button
                self.selected_index = len(self._theme_list)
                self.selected_element = "name"
            else:
                self.selected_index -= 1
                prev_theme = self._theme_list[self.selected_index]
                if prev_theme == "__MATCH_OMARCHY__":
                    # Match Omarchy has no delete icon, stay on name
                    self.selected_element = "name"
                else:
                    self.selected_element = "delete"
        elif self.selected_element == "edit":
            # Move to same theme's name
            self.selected_element = "name"
        elif self.selected_element == "delete":
            # Move to same theme's edit icon
            self.selected_element = "edit"
        
        # Clear pending deletion when navigating away
        if self.selected_index < len(self._theme_list) and self._theme_list[self.selected_index] != self.pending_delete_key:
            self.pending_delete_key = None
    
    def action_select_next(self) -> None:
        """Select next element (cycles through name, edit, delete for each theme, then Sync button)"""
        if not self._theme_list:
            return
        
        # Check if we're on the Sync button
        if self.selected_index == len(self._theme_list):
            # Wrap around to first theme
            self.selected_index = 0
            self.selected_element = "name"
            self.pending_delete_key = None
            return
        
        current_theme = self._theme_list[self.selected_index]
        is_match_omarchy = (current_theme == "__MATCH_OMARCHY__")
        
        # Navigate forwards through elements
        if self.selected_element == "name":
            if is_match_omarchy:
                # Match Omarchy has no edit/delete, skip to next theme
                self.selected_index = (self.selected_index + 1) % len(self._theme_list)
                # Check if we wrapped to end - go to Sync button
                if self.selected_index == 0:
                    self.selected_index = len(self._theme_list)
            else:
                # Move to same theme's edit icon
                self.selected_element = "edit"
        elif self.selected_element == "edit":
            # Move to same theme's delete icon
            self.selected_element = "delete"
        elif self.selected_element == "delete":
            # Move to next theme's name, or Sync button if at end
            if self.selected_index == len(self._theme_list) - 1:
                # Last theme - go to Sync button
                self.selected_index = len(self._theme_list)
                self.selected_element = "name"
            else:
                # Move to next theme
                self.selected_index += 1
                self.selected_element = "name"
        
        # Clear pending deletion when navigating away
        if self.selected_index < len(self._theme_list) and self._theme_list[self.selected_index] != self.pending_delete_key:
            self.pending_delete_key = None
    
    def action_apply_theme(self) -> None:
        """Apply action based on currently selected element"""
        if not self._theme_list:
            return
        
        # Check if Sync button is selected
        if self.selected_index == len(self._theme_list):
            self.post_message(self.ThemeSyncRequested())
            return
        
        if self.selected_index >= len(self._theme_list):
            return
        
        theme_idx = self.selected_index
        
        # Perform action based on which element is selected
        if self.selected_element == "name":
            # Apply the theme
            self.pending_delete_key = None
            selected_theme = self._theme_list[theme_idx]
            if selected_theme == "__MATCH_OMARCHY__":
                self.post_message(self.ThemeSelected("", match_omarchy=True))
            else:
                self.post_message(self.ThemeSelected(selected_theme, match_omarchy=False))
        elif self.selected_element == "edit":
            # Edit the theme
            self._handle_edit_click(theme_idx)
        elif self.selected_element == "delete":
            # Delete the theme (or confirm deletion)
            self._handle_delete_click(theme_idx)
    
    def on_click(self, event) -> None:
        """Handle clicks on theme items"""
        # Calculate which line was clicked
        # Layout: blank line (0), Match Omarchy (1), blank line (2), themes start at (3)
        y = event.y
        x = event.x
        
        width = max(60, self.size.width if self.size.width > 0 else 70)
        
        # Adjust for padding: 1 blank line + 1 match omarchy + 1 blank line = 3 lines offset
        # But Match Omarchy is at y=1 (index 0)
        # First real theme is at y=3 (index 1)
        if y == 0:
            # Blank line at top, ignore
            return
        elif y == 1:
            # Match Omarchy option - only trigger on theme name (first ~25 chars)
            if x < 30:  # Approximate end of "Match Omarchy (theme-name)" text
                self.selected_index = 0
                self.action_apply_theme()
            return
        elif y == 2:
            # Blank line after Match Omarchy, ignore
            return
        elif 3 <= y < len(self._theme_list) + 2:
            # Theme list starts at y=3, which is index 1
            theme_idx = y - 2
            
            # Icons are at the far right: " ✎ 🗑 │"
            # Edit icon (✎) is at approximately width-5
            # Delete icon (🗑) is at approximately width-3
            delete_icon_x = width - 3
            edit_icon_x = width - 5
            
            if x >= delete_icon_x and x < width - 1:
                # Clicked on delete icon
                self._handle_delete_click(theme_idx)
            elif x >= edit_icon_x and x < delete_icon_x:
                # Clicked on edit icon
                self._handle_edit_click(theme_idx)
            elif x >= 2 and x <= 22:  # Only clicking on theme name (marker + space + name)
                # Clicked on theme name only - apply theme
                self.selected_index = theme_idx
                self.action_apply_theme()
        else:
            # Beyond theme list - could be Sync button
            # Sync button is at y = 3 + len(themes) + 1 (blank line) = len(themes) + 4
            sync_button_y = len(self._theme_list) + 4
            if y == sync_button_y:
                # Clicked on Sync button (right side of screen)
                # Sync button text "[Sync]" is 6 chars at the right edge
                if x >= width - 8:  # Right-aligned button area
                    self.selected_index = len(self._theme_list)
                    self.selected_element = "name"
                    self.action_apply_theme()
    
    def _handle_edit_click(self, theme_idx: int) -> None:
        """Handle edit button click for a theme"""
        if theme_idx >= len(self._theme_list):
            return
        
        theme_key = self._theme_list[theme_idx]
        if theme_key == "__MATCH_OMARCHY__":
            return  # Can't edit Match Omarchy option
        
        # Load theme data from database
        try:
            if THEMES_DB_PATH.exists():
                db_data = json.loads(THEMES_DB_PATH.read_text())
                if "themes" in db_data and theme_key in db_data["themes"]:
                    theme_data = db_data["themes"][theme_key]
                    colors = theme_data.get("colors", [])
                    theme_name = theme_data.get("name", theme_key)
                    
                    # Post message to load theme for editing
                    self.post_message(self.ThemeEditRequested(theme_key, theme_name, colors))
        except Exception as e:
            import sys
            print(f"Error loading theme for editing: {e}", file=sys.stderr)
    
    def _handle_delete_click(self, theme_idx: int) -> None:
        """Handle delete button click for a theme - requires two clicks to confirm"""
        if theme_idx >= len(self._theme_list):
            return
        
        theme_key = self._theme_list[theme_idx]
        if theme_key == "__MATCH_OMARCHY__":
            return  # Can't delete Match Omarchy option
        
        # Check if this theme is already pending deletion
        if self.pending_delete_key == theme_key:
            # Second click - confirm deletion
            try:
                if THEMES_DB_PATH.exists():
                    db_data = json.loads(THEMES_DB_PATH.read_text())
                    if "themes" in db_data and theme_key in db_data["themes"]:
                        theme_data = db_data["themes"][theme_key]
                        theme_name = theme_data.get("name", theme_key)
                        
                        # Post message to request theme deletion
                        self.post_message(self.ThemeDeleteRequested(theme_key, theme_name))
                        
                        # Clear pending deletion state
                        self.pending_delete_key = None
            except Exception as e:
                import sys
                print(f"Error loading theme for deletion: {e}", file=sys.stderr)
                self.pending_delete_key = None
        else:
            # First click - mark for deletion
            self.pending_delete_key = theme_key
    
    def _create_gradient_preview(self, colors: list, width: int) -> str:
        """Create a visual gradient using colored blocks (matches daemon interpolation)"""
        from ..utils.colors import hex_to_rgb, rgb_to_hex
        
        blocks = []
        
        # Use shared color conversion utilities
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
