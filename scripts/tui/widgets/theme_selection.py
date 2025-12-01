"""
Theme selection panel widget for ForgeworkLights TUI
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
from ..theme import THEME


class ThemeSelectionPanel(ScrollableContainer):
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
        ("left", "move_left", "Move to previous element"),
        ("right", "move_right", "Move to next element"),
        ("enter", "apply_theme", "Apply theme"),
        ("e", "edit_theme", "Edit theme"),
        ("d", "delete_theme", "Delete theme"),
    ]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._content = Static("", id="theme-selection-content")
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
        
        # Get current LED theme setting
        led_theme = "match"
        try:
            if LED_THEME_FILE.exists():
                led_theme = LED_THEME_FILE.read_text().strip()
        except:
            pass
        
        try:
            # Add instruction line at top (below Theme Selection border)
            # Match StatusPanel hint style: dimmed text with themed borders.
            instruction_text = " ↑↓←→ navigate, Enter select, E edit, D delete"
            inner_width = width - 2  # characters between the two borders
            instr_body = f"{instruction_text:<{inner_width}}"
            instr_line = f"[{THEME['box_outline']}]│[/][dim]{instr_body}[/][{THEME['box_outline']}]│[/]"
            lines.append(instr_line)
            
            # Add "Match Omarchy Theme" option at the top
            self._theme_list.append("__MATCH_OMARCHY__")
            is_selected = self.selected_index == 0
            marker = "→" if led_theme == "match" else " "
            
            display_name = "Match Omarchy"
            
            # Calculate visible content length: marker(1) + space(1) + display_name + space(1)
            visible_len = 1 + 1 + len(display_name) + 1
            padding_needed = max(1, width - visible_len - 2)  # -2 for borders
            
            # Highlight if selected AND focused
            if is_selected and show_highlight:
                line = f"│[bold {THEME['hi_fg']} on {THEME['selected_bg']}] {marker} {display_name}{' ' * padding_needed}[/]│"
            else:
                line = f"│ [{THEME['main_fg']}]{marker} {display_name}{' ' * padding_needed}[/]│"
            
            lines.append(f"[{THEME['box_outline']}]{line}[/]")
            
            # Add blank line after Match Omarchy
            blank_padding = max(1, width - 2)  # -2 for borders
            lines.append(f"[{THEME['box_outline']}]│{' ' * blank_padding}│[/]")
            
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

                            # Mark current LED theme (not Omarchy theme)
                            marker = "→" if theme_key == led_theme else " "
                            is_selected = self.selected_index == idx

                            # Theme name column
                            name_padded = f"{theme_name[:18]:<18}"
                            
                            # Show confirmation message if this theme is pending deletion
                            # Note: 🗑 emoji and ✓ both take 2 char widths in most terminals, ✎ takes 1 char
                            if self.pending_delete_key == theme_key:
                                icons = " ✎ ✓"  # space(1) + edit(1) + space(1) + check(2)
                                icons_width = 5
                                trailing_spaces = 1
                            else:
                                icons = " ✎ 🗑"  # space(1) + edit(1) + space(1) + trash(2)
                                icons_width = 5
                                trailing_spaces = 1

                            # Use remaining content width for the gradient preview, leaving room for name and icons
                            # marker(1) + space(1) + name(18) + space(1) + gradient(width) + spaces + icons(width) + trailing_spaces + borders(2)
                            # First, choose a tentative maximum for gradient width based on available content width
                            max_gradient_width = max(10, content_width - (1 + 1 + 18 + 1 + icons_width + trailing_spaces + 4))
                            gradient_width = max_gradient_width
                            gradient = self._create_gradient_preview(colors, gradient_width)

                            # Recompute visible length including borders so we can pad out to full panel width
                            visible_len = 1 + 1 + 18 + 1 + gradient_width + icons_width + trailing_spaces + 2
                            padding_needed = max(1, width - visible_len)
                            
                            # Build line with selection highlight (only when focused)
                            # Highlight different parts based on selected_element
                            if is_selected and show_highlight:
                                if self.selected_element == "name":
                                    # Highlight theme name only
                                    line = f"│ {marker} [bold {THEME['hi_fg']} on {THEME['selected_bg']}]{name_padded}[/] {gradient}{' ' * padding_needed}{icons}{' ' * trailing_spaces}│"
                                elif self.selected_element == "edit":
                                    # Highlight edit icon with background (2 chars wide)
                                    if self.pending_delete_key == theme_key:
                                        # " ✎ ✓ " with edit highlighted (check is 2 chars wide)
                                        line = f"│ {marker} {name_padded} {gradient}{' ' * padding_needed} [bold {THEME['hi_fg']} on {THEME['selected_bg']}]✎ [/]✓ │"
                                    else:
                                        # " ✎ 🗑 " with edit highlighted
                                        line = f"│ {marker} {name_padded} {gradient}{' ' * padding_needed} [bold {THEME['hi_fg']} on {THEME['selected_bg']}]✎ [/]🗑 │"
                                elif self.selected_element == "delete":
                                    # Highlight delete icon with background (2 chars wide)
                                    if self.pending_delete_key == theme_key:
                                        # " ✎ ✓ " with checkmark highlighted (check is 2 chars wide)
                                        line = f"│ {marker} {name_padded} {gradient}{' ' * padding_needed} ✎ [bold {THEME['hi_fg']} on {THEME['selected_bg']}]✓[/] │"
                                    else:
                                        # " ✎ 🗑 " with trash highlighted (edit in normal color)
                                        line = f"│ {marker} {name_padded} {gradient}{' ' * padding_needed} ✎ [bold {THEME['hi_fg']} on {THEME['selected_bg']}]🗑[/] │"
                            else:
                                line = f"│ [{THEME['main_fg']}]{marker} {name_padded}[/] {gradient}{' ' * padding_needed}{icons}{' ' * trailing_spaces}│"
                            
                            lines.append(f"[{THEME['box_outline']}]{line}[/]")
                    
                    # Add blank line after theme list
                    if self._theme_list:  # Only if themes were added
                        blank_padding = max(1, width - 2)  # -2 for borders
                        lines.append(f"[{THEME['box_outline']}]│{' ' * blank_padding}│[/]")
                    
                    # Add Sync button in bottom right
                    sync_text = "Sync"
                    # Total visible length: sync_text + borders(2)
                    sync_padding = max(1, width - len(sync_text) - 2)
                    # Check if Sync is the selected element (last item in list)
                    is_sync_selected = (len(self._theme_list) > 0 and 
                                       self.selected_index == len(self._theme_list) and
                                       self.selected_element == "name")
                    
                    if is_sync_selected and show_highlight:
                        # Highlighted - use theme colors
                        sync_line = f"[{THEME['box_outline']}]│{' ' * sync_padding}[bold {THEME['hi_fg']} on {THEME['selected_bg']}]{sync_text}[/]│[/]"
                    else:
                        # Normal - use theme colors
                        sync_line = f"[{THEME['box_outline']}]│{' ' * sync_padding}[{THEME['main_fg']}]{sync_text}[/]│[/]"
                    
                    lines.append(sync_line)
            
            if len(lines) <= 1:
                empty_text = "No themes found"
                padding = max(0, width - len(empty_text) - 3)
                lines.append(f"[{THEME['box_outline']}]│ [{THEME['inactive_fg']}]{empty_text}[/]{' ' * padding}│[/]")
                
        except Exception as e:
            error_text = f"Error loading themes: {e}"
            padding = max(0, width - len(error_text) - 3)
            lines.append(f"[{THEME['box_outline']}]│ [{THEME['inactive_fg']}]{error_text}[/]{' ' * padding}│[/]")
        
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
        """Move selection to the previous theme row (Up key)."""
        if not self._theme_list:
            return

        max_index = len(self._theme_list)  # Themes plus Sync row

        if self.selected_index == 0:
            # Wrap to Sync row at bottom
            self.selected_index = max_index
        else:
            self.selected_index -= 1

        self._normalize_selection_after_vertical_move()

        # Clear pending deletion when moving to a different row
        if self.selected_index >= len(self._theme_list) or (
            self._theme_list[self.selected_index] != self.pending_delete_key
        ):
            self.pending_delete_key = None

    def action_select_next(self) -> None:
        """Move selection to the next theme row (Down key)."""
        if not self._theme_list:
            return

        max_index = len(self._theme_list)  # Themes plus Sync row

        if self.selected_index >= max_index:
            # From Sync, wrap to first theme
            self.selected_index = 0
        else:
            self.selected_index += 1
            if self.selected_index > max_index:
                self.selected_index = 0

        self._normalize_selection_after_vertical_move()

        # Clear pending deletion when moving to a different row
        if self.selected_index >= len(self._theme_list) or (
            self._theme_list[self.selected_index] != self.pending_delete_key
        ):
            self.pending_delete_key = None

    def action_move_left(self) -> None:
        """Move focus left between name, edit, and delete elements (Left key)."""
        if not self._theme_list:
            return

        # Sync row and Match Omarchy only have the name element
        if self.selected_index >= len(self._theme_list):
            return

        theme_key = self._theme_list[self.selected_index]
        if theme_key == "__MATCH_OMARCHY__":
            return

        if self.selected_element == "edit":
            self.selected_element = "name"
        elif self.selected_element == "delete":
            self.selected_element = "edit"

    def action_move_right(self) -> None:
        """Move focus right between name, edit, and delete elements (Right key)."""
        if not self._theme_list:
            return

        # Sync row and Match Omarchy only have the name element
        if self.selected_index >= len(self._theme_list):
            return

        theme_key = self._theme_list[self.selected_index]
        if theme_key == "__MATCH_OMARCHY__":
            return

        if self.selected_element == "name":
            self.selected_element = "edit"
        elif self.selected_element == "edit":
            self.selected_element = "delete"

    def _normalize_selection_after_vertical_move(self) -> None:
        """Ensure selected_element is valid for the current row after Up/Down."""
        # Sync row (last index) only has a name element
        if self.selected_index == len(self._theme_list):
            self.selected_element = "name"
            return

        if self.selected_index >= len(self._theme_list):
            return

        theme_key = self._theme_list[self.selected_index]

        # Match Omarchy row has only the name element
        if theme_key == "__MATCH_OMARCHY__" and self.selected_element in {"edit", "delete"}:
            self.selected_element = "name"
    
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
    
    def action_edit_theme(self) -> None:
        """Edit the currently selected theme"""
        if not self._theme_list or self.selected_index >= len(self._theme_list):
            return
        
        theme_key = self._theme_list[self.selected_index]
        if theme_key == "__MATCH_OMARCHY__":
            return  # Can't edit Match Omarchy option
        
        self._handle_edit_click(self.selected_index)
    
    def action_delete_theme(self) -> None:
        """Delete the currently selected theme"""
        if not self._theme_list or self.selected_index >= len(self._theme_list):
            return
        
        theme_key = self._theme_list[self.selected_index]
        if theme_key == "__MATCH_OMARCHY__":
            return  # Can't delete Match Omarchy option
        
        self._handle_delete_click(self.selected_index)
    
    def on_click(self, event) -> None:
        """Handle clicks on theme items"""
        # Calculate which line was clicked
        # Layout: blank line (0), Match Omarchy (1), blank line (2), themes start at (3)
        y = event.y
        x = event.x
        
        width = max(60, self.size.width if self.size.width > 0 else 70)
        
        # Adjust for padding: 1 blank line + 1 match omarchy + 1 blank line = 3 lines offset
        # Match Omarchy is at y=1 (index 0)
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
            # Sync button: last theme ends at y = len(_theme_list) + 1, then blank line, then Sync
            sync_button_y = len(self._theme_list) + 3
            if y == sync_button_y and x >= width - 6:
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
            return f"[{hex_color} on {THEME['main_bg']}]▄[/]" * width
        
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
            blocks.append(f"[{hex_color} on {THEME['main_bg']}]▄[/]")
        
        return "".join(blocks)
