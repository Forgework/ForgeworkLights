"""
Theme creator widget for custom gradient themes
"""
from textual.widgets import Static, Input
from textual.containers import Container, Horizontal, Vertical
from textual.reactive import reactive
from textual.app import ComposeResult
from textual.message import Message
from textual import events
from pathlib import Path
import json
import sys
import subprocess
from .color_selector import ColorSelector
from .countdown_bar import CountdownBar
from .theme_button import ThemeButton
from ..utils.colors import generate_gradient
from ..constants import LED_THEME_FILE, DAEMON_BINARY
from ..theme import THEME


class ThemeCreator(Container):
    """Widget for creating custom themes with 3-color gradients"""
    
    class ThemeCreated(Message):
        """Message when a new theme is created"""
        def __init__(self, theme_name: str):
            super().__init__()
            self.theme_name = theme_name
    
    color1 = reactive("#ffbe0b")
    color2 = reactive("#ff006e")
    color3 = reactive("#3a0ca3")
    theme_name = reactive("")
    active_color_input = reactive(None)  # Track which color input is being edited
    is_previewing = reactive(False)  # Track if currently previewing
    preview_duration = 5.0  # Preview duration in seconds
    
    def __init__(self, themes_db_path: Path, **kwargs):
        super().__init__(**kwargs)
        self.themes_db_path = themes_db_path
        self.can_focus = False  # Don't take focus, let inputs handle it
        self.editing_theme_key = None  # Track if we're editing an existing theme
    
    def on_mount(self) -> None:
        """Initialize preview and color picker"""
        try:
            # Clean up any leftover preview theme from previous session
            if self.themes_db_path.exists():
                db_data = json.loads(self.themes_db_path.read_text())
                if "__preview__" in db_data.get("themes", {}):
                    del db_data["themes"]["__preview__"]
                    self.themes_db_path.write_text(json.dumps(db_data, indent=2))
            
            self._update_preview()
            # Initialize color picker with first color
            picker = self.query_one("#theme-color-picker", ColorSelector)
            picker.set_color_from_hex(self.color1)
            self.active_color_input = "color1"
            # Hide countdown bar initially
            countdown = self.query_one("#preview-countdown", CountdownBar)
            countdown.display = False
        except Exception as e:
            print(f"Error initializing: {e}", file=sys.stderr)
    
    def compose(self) -> ComposeResult:
        """Compose the theme creator UI"""
        # Main vertical layout: combined color picker and theme controls in one section
        with Vertical(id="theme-creator-main"):
            # Keyboard hint directly under the "Create Custom Theme" border
            yield Static("[dim]↑↓←→ adjust color, r/g/b/h/s/v keys (shift=decrease), p=preview, s=save, c=clear[/]", id="hint-text")
            yield ColorSelector(width=60, height=20, id="theme-color-picker")
    
    def on_input_changed(self, event: Input.Changed) -> None:
        """Update colors and preview when inputs change"""
        if event.input.id == "theme-name-input":
            self.theme_name = event.value
        elif event.input.id == "color1-input":
            if self._is_valid_hex(event.value):
                self.color1 = event.value
        elif event.input.id == "color2-input":
            if self._is_valid_hex(event.value):
                self.color2 = event.value
        elif event.input.id == "color3-input":
            if self._is_valid_hex(event.value):
                self.color3 = event.value
        
        self._update_preview()
    
    def on_theme_button_button_clicked(self, message: ThemeButton.ButtonClicked) -> None:
        """Handle button clicks"""
        print(f"\n=== BUTTON CLICKED: {message.button_id} ===", file=sys.stderr)
        if message.button_id == "preview":
            print("Calling action_preview_theme()", file=sys.stderr)
            self.action_preview_theme()
            print("action_preview_theme() completed", file=sys.stderr)
        elif message.button_id == "save":
            print("Calling action_save_theme()", file=sys.stderr)
            self.action_save_theme()
            print("action_save_theme() completed", file=sys.stderr)
        elif message.button_id == "clear":
            print("Calling action_clear()", file=sys.stderr)
            self.action_clear()
            print("action_clear() completed", file=sys.stderr)
    
    def _is_valid_hex(self, color: str) -> bool:
        """Check if string is a valid hex color"""
        if not color.startswith('#'):
            return False
        if len(color) != 7:
            return False
        try:
            int(color[1:], 16)
            return True
        except ValueError:
            return False
    
    def _update_preview(self) -> None:
        """Update gradient preview"""
        preview = self.query_one("#gradient-preview", Static)
        
        # Create compact 2-line gradient preview - width should span 3 color inputs (14 chars each + spacing = ~45)
        gradient = self._create_gradient_preview([self.color1, self.color2, self.color3], 45)
        preview.update(gradient)
    
    def _create_gradient_preview(self, colors, width):
        """Create a gradient preview string with thick blocks"""
        lines = []
        # Create 2 lines of compact gradient
        for _ in range(2):
            result = []
            for i in range(width):
                # Interpolate between the three colors
                pos = i / (width - 1) if width > 1 else 0
                
                if pos <= 0.5:
                    # First half: interpolate between color1 and color2
                    t = pos * 2
                    color = self._interpolate_colors(colors[0], colors[1], t)
                else:
                    # Second half: interpolate between color2 and color3
                    t = (pos - 0.5) * 2
                    color = self._interpolate_colors(colors[1], colors[2], t)
                
                result.append(f"[{color}]█[/]")
            lines.append("".join(result))
        
        return "\n".join(lines)
    
    def _interpolate_colors(self, color1, color2, t):
        """Interpolate between two hex colors"""
        # Parse hex colors
        r1 = int(color1[1:3], 16)
        g1 = int(color1[3:5], 16)
        b1 = int(color1[5:7], 16)
        
        r2 = int(color2[1:3], 16)
        g2 = int(color2[3:5], 16)
        b2 = int(color2[5:7], 16)
        
        # Interpolate
        r = int(r1 + (r2 - r1) * t)
        g = int(g1 + (g2 - g1) * t)
        b = int(b1 + (b2 - b1) * t)
        
        return f"#{r:02x}{g:02x}{b:02x}"
    
    def load_theme_for_editing(self, theme_key: str, theme_name: str, colors: list) -> None:
        """Load a theme into the creator for editing"""
        print(f"\n*** Loading theme for editing: {theme_key} ***", file=sys.stderr)
        
        # Store the theme key for editing
        self.editing_theme_key = theme_key
        
        # Extract first, middle, and last colors from the 22-color gradient
        if len(colors) >= 3:
            self.color1 = colors[0]
            self.color2 = colors[len(colors) // 2]
            self.color3 = colors[-1]
        
        # Set the theme name
        self.theme_name = theme_name
        
        # Update UI inputs
        theme_input = self.query_one("#theme-name-input", Input)
        theme_input.value = theme_name
        theme_input.placeholder = f"Editing: {theme_name}"
        
        self.query_one("#color1-input", Input).value = self.color1
        self.query_one("#color2-input", Input).value = self.color2
        self.query_one("#color3-input", Input).value = self.color3
        
        # Update preview
        self._update_preview()
        
        # Focus the theme creator so user sees the loaded theme
        theme_input.focus()
    
    def action_preview_theme(self) -> None:
        """Preview the custom theme on LEDs for a few seconds"""
        if self.is_previewing:
            print("Already previewing, ignoring request", file=sys.stderr)
            return
        
        preview = self.query_one("#gradient-preview", Static)
        countdown = self.query_one("#preview-countdown", CountdownBar)
        
        # Validate colors
        if not all([self._is_valid_hex(c) for c in [self.color1, self.color2, self.color3]]):
            preview.update("✗ Invalid colors for preview")
            return
        
        try:
            # Generate the 22-color gradient
            colors_22 = generate_gradient([self.color1, self.color2, self.color3], 22)
            
            if len(colors_22) != 22:
                preview.update(f"✗ Got {len(colors_22)} colors, expected 22")
                return
            
            # Save current theme to restore later
            if LED_THEME_FILE.exists():
                self.saved_theme = LED_THEME_FILE.read_text().strip()
            else:
                self.saved_theme = "match"
            
            # Create temporary preview theme
            if self.themes_db_path.exists():
                db_data = json.loads(self.themes_db_path.read_text())
            else:
                db_data = {"themes": {}}
            
            db_data["themes"]["__preview__"] = {
                "name": "Preview",
                "colors": colors_22
            }
            
            # Save themes database with preview theme
            self.themes_db_path.write_text(json.dumps(db_data, indent=2))
            
            # Apply preview theme
            LED_THEME_FILE.parent.mkdir(parents=True, exist_ok=True)
            LED_THEME_FILE.write_text("__preview__\n")
            LED_THEME_FILE.touch()
            
            # Show countdown and mark as previewing
            self.is_previewing = True
            countdown.display = True
            # Hide static gradient preview + spacer while countdown is visible
            preview.display = False
            try:
                spacer = self.query_one("#gradient-spacer", Static)
                spacer.display = False
            except Exception:
                pass
            preview.update(f"👁 Previewing for {int(self.preview_duration)}s...")
            
            # Start countdown
            countdown.start_countdown(self.preview_duration, on_complete=self._end_preview)
            
        except Exception as e:
            preview.update(f"✗ Preview error: {str(e)[:40]}")
            print(f"Preview error: {e}", file=sys.stderr)
            self.is_previewing = False
    
    def _end_preview(self) -> None:
        """Restore original theme after preview"""
        try:
            countdown = self.query_one("#preview-countdown", CountdownBar)
            preview = self.query_one("#gradient-preview", Static)
            
            # Remove the temporary preview theme from database
            if self.themes_db_path.exists():
                db_data = json.loads(self.themes_db_path.read_text())
                if "__preview__" in db_data.get("themes", {}):
                    del db_data["themes"]["__preview__"]
                    self.themes_db_path.write_text(json.dumps(db_data, indent=2))
            
            # Restore original theme
            LED_THEME_FILE.write_text(f"{self.saved_theme}\n")
            LED_THEME_FILE.touch()
            
            # Hide countdown bar
            countdown.display = False
            self.is_previewing = False
            
            # Restore preview display and spacer
            preview.display = True
            try:
                spacer = self.query_one("#gradient-spacer", Static)
                spacer.display = True
            except Exception:
                pass
            self._update_preview()
            
            print("Preview ended, theme restored", file=sys.stderr)
            
        except Exception as e:
            print(f"Error ending preview: {e}", file=sys.stderr)
            self.is_previewing = False
    
    def action_save_theme(self) -> None:
        """Save the custom theme"""
        theme_input = self.query_one("#theme-name-input", Input)
        preview = self.query_one("#gradient-preview", Static)
        
        if not self.theme_name:
            theme_input.placeholder = "⚠ Please enter a theme name!"
            preview.update("⚠ Please enter a theme name!")
            return
        
        # Determine if we're saving or updating
        action_verb = "Updating" if self.editing_theme_key else "Saving"
        theme_input.placeholder = f"{action_verb}..."
        preview.update(f"{action_verb}...")
        
        # Validate colors
        if not all([self._is_valid_hex(c) for c in [self.color1, self.color2, self.color3]]):
            preview.update("✗ Invalid color format")
            return
        
        # Generate the 22-color gradient
        try:
            colors_22 = generate_gradient([self.color1, self.color2, self.color3], 22)
            
            if len(colors_22) != 22:
                preview.update(f"✗ Got {len(colors_22)} colors, expected 22")
                return
            
            # Load existing themes
            if self.themes_db_path.exists():
                db_data = json.loads(self.themes_db_path.read_text())
            else:
                db_data = {"themes": {}}
            
            # Add or update theme
            if self.editing_theme_key:
                theme_key = self.editing_theme_key
            else:
                theme_key = self.theme_name.lower().replace(' ', '-')
            
            db_data["themes"][theme_key] = {
                "name": self.theme_name.title(),
                "colors": colors_22
            }
            
            # Save back to file
            self.themes_db_path.write_text(json.dumps(db_data, indent=2))
            
            # Show success message
            action_verb = "Updated" if self.editing_theme_key else "Saved"
            theme_input.placeholder = f"✓ {action_verb} '{self.theme_name}'!"
            preview.update(f"✓ {action_verb} '{self.theme_name}' with {len(colors_22)} colors!")
            
            # Post message to notify app
            self.post_message(self.ThemeCreated(theme_key))
            
            # Clear inputs and exit editing mode
            self.action_clear()
            
        except Exception as e:
            theme_input.placeholder = f"✗ Error: {str(e)}"
            preview.update(f"✗ Error: {str(e)[:50]}")
    
    def action_clear(self) -> None:
        """Clear all inputs"""
        self.theme_name = ""
        self.color1 = "#ffbe0b"
        self.color2 = "#ff006e"
        self.color3 = "#3a0ca3"
        self.editing_theme_key = None  # Exit editing mode
        theme_input = self.query_one("#theme-name-input", Input)
        theme_input.value = ""
        theme_input.placeholder = "Theme Name"
        self.query_one("#color1-input", Input).value = self.color1
        self.query_one("#color2-input", Input).value = self.color2
        self.query_one("#color3-input", Input).value = self.color3
        self._update_preview()
    
    def on_key(self, event: events.Key) -> None:
        """Handle key presses - intercept arrow keys when hex inputs are focused"""
        try:
            focused = self.app.focused
            # Global shortcuts for the Create Custom Theme section
            if event.key in ["p", "P"]:
                self.action_preview_theme()
                event.prevent_default()
                event.stop()
                return
            if event.key in ["s", "S"]:
                self.action_save_theme()
                event.prevent_default()
                event.stop()
                return
            if event.key in ["c", "C"]:
                self.action_clear()
                event.prevent_default()
                event.stop()
                return

            if focused and hasattr(focused, 'id'):
                # Check if a color input has focus
                if focused.id in ["color1-input", "color2-input", "color3-input"]:
                    # Arrow keys and RGB/HSV shortcut keys should control the color selector
                    slider_keys = {"r", "R", "g", "G", "b", "B", "h", "H", "s", "S", "v", "V"}
                    if event.key in ["up", "down", "left", "right"] or event.key in slider_keys:
                        picker = self.query_one("#theme-color-picker", ColorSelector)
                        # Forward the key event to the color selector
                        picker.on_key(event)
                        # Prevent the input from handling the key
                        event.prevent_default()
                        event.stop()
        except Exception as e:
            print(f"Error handling key: {e}", file=sys.stderr)
    
    def on_descendant_focus(self, event: events.DescendantFocus) -> None:
        """Handle when any descendant widget gains focus (mouse or keyboard)"""
        # When a color input gains focus, update the picker to show that color
        try:
            # Check if the focused widget is one of our color inputs
            focused = event.widget
            if focused and hasattr(focused, 'id'):
                picker = self.query_one("#theme-color-picker", ColorSelector)
                if focused.id == "color1-input":
                    self.active_color_input = "color1"
                    picker.set_color_from_hex(self.color1)
                elif focused.id == "color2-input":
                    self.active_color_input = "color2"
                    picker.set_color_from_hex(self.color2)
                elif focused.id == "color3-input":
                    self.active_color_input = "color3"
                    picker.set_color_from_hex(self.color3)
        except Exception as e:
            print(f"Error handling input focus: {e}", file=sys.stderr)
    
    def on_color_selector_color_selected(self, message: ColorSelector.ColorSelected) -> None:
        """Handle color selection from picker"""
        if self.active_color_input == "color1":
            self.color1 = message.hex_color
            self.query_one("#color1-input", Input).value = message.hex_color
        elif self.active_color_input == "color2":
            self.color2 = message.hex_color
            self.query_one("#color2-input", Input).value = message.hex_color
        elif self.active_color_input == "color3":
            self.color3 = message.hex_color
            self.query_one("#color3-input", Input).value = message.hex_color
        
        self._update_preview()
