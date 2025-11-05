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
import subprocess
import sys
from .color_selector import ColorSelector


class ThemeButton(Static):
    """Individual clickable button widget"""
    
    class ButtonClicked(Message):
        def __init__(self, button_id: str):
            super().__init__()
            self.button_id = button_id
    
    def __init__(self, label: str, button_id: str, shortcut: str, **kwargs):
        super().__init__(**kwargs)
        self.label = label
        self.button_id = button_id
        self.shortcut = shortcut
        self.can_focus = False  # Not individually focusable
    
    def render(self) -> str:
        text = f"[{self.shortcut}] {self.label}"
        if self.has_focus:
            text = f"[bold yellow]{text}[/]"
        return text
    
    def on_click(self, event) -> None:
        self.post_message(self.ButtonClicked(self.button_id))
    
    def on_key(self, event) -> None:
        if event.key == "enter":
            self.post_message(self.ButtonClicked(self.button_id))


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
    show_color_picker = reactive(False)
    active_color_input = reactive(None)  # Track which color input is being edited
    
    def __init__(self, themes_db_path: Path, **kwargs):
        super().__init__(**kwargs)
        self.themes_db_path = themes_db_path
        self.can_focus = False  # Don't take focus, let inputs handle it
        self.editing_theme_key = None  # Track if we're editing an existing theme
        self.color_picker_active = False
    
    def on_mount(self) -> None:
        """Initialize preview"""
        try:
            self._update_preview()
        except Exception as e:
            print(f"Error updating preview: {e}", file=sys.stderr)
    
    def compose(self) -> ComposeResult:
        """Compose the theme creator UI"""
        # Main horizontal split: left controls, right color picker
        with Horizontal(id="theme-creator-main"):
            # Left side: All controls
            with Vertical(id="theme-controls"):
                # Theme name input
                with Horizontal(classes="compact-row"):
                    yield Input(placeholder="Theme Name", id="theme-name-input", classes="name-input")
                
                # Gradient preview centered over color inputs
                with Horizontal(classes="compact-row"):
                    yield Static("", id="gradient-preview", classes="preview-centered")
                
                # Color inputs in one row (no labels)
                with Horizontal(classes="compact-row"):
                    yield Input(placeholder="#ffbe0b", value=self.color1, id="color1-input", classes="color-input", max_length=7)
                    yield Input(placeholder="#ff006e", value=self.color2, id="color2-input", classes="color-input", max_length=7)
                    yield Input(placeholder="#3a0ca3", value=self.color3, id="color3-input", classes="color-input", max_length=7)
                
                # Buttons below hex inputs
                with Horizontal(id="button-row"):
                    yield ThemeButton("Save", "save", "S", id="save-button")
                    yield ThemeButton("Clear", "clear", "C", id="clear-button")
                    yield ThemeButton("Color Picker", "picker", "P", id="picker-button")
            
            # Right side: Color picker (initially hidden)
            yield ColorSelector(width=30, height=10, id="theme-color-picker")
    
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
        if message.button_id == "save":
            print("Calling action_save_theme()", file=sys.stderr)
            self.action_save_theme()
            print("action_save_theme() completed", file=sys.stderr)
        elif message.button_id == "clear":
            print("Calling action_clear()", file=sys.stderr)
            self.action_clear()
            print("action_clear() completed", file=sys.stderr)
        elif message.button_id == "picker":
            print("Calling action_toggle_color_picker()", file=sys.stderr)
            self.action_toggle_color_picker()
            print("action_toggle_color_picker() completed", file=sys.stderr)
    
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
        
        # Create thick 3-line gradient preview - width should span 3 color inputs (14 chars each + spacing = ~45)
        gradient = self._create_gradient_preview([self.color1, self.color2, self.color3], 45)
        preview.update(gradient)
    
    def _create_gradient_preview(self, colors, width):
        """Create a gradient preview string with thick blocks"""
        lines = []
        # Create 3 lines of thick gradient
        for _ in range(3):
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
        
        # Extract first, middle, and last colors from the 14-color gradient
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
    
    def action_save_theme(self) -> None:
        """Save the custom theme"""
        print(f"\n*** action_save_theme() CALLED ***", file=sys.stderr)
        print(f"*** Editing mode: {self.editing_theme_key is not None} ***", file=sys.stderr)
        print(f"*** Theme name: '{self.theme_name}' ***", file=sys.stderr)
        print(f"*** Color1: {self.color1} ***", file=sys.stderr)
        print(f"*** Color2: {self.color2} ***", file=sys.stderr)
        print(f"*** Color3: {self.color3} ***", file=sys.stderr)
        
        theme_input = self.query_one("#theme-name-input", Input)
        preview = self.query_one("#gradient-preview", Static)
        
        if not self.theme_name:
            print("*** ERROR: No theme name! ***", file=sys.stderr)
            theme_input.placeholder = "⚠ Please enter a theme name!"
            preview.update("⚠ Please enter a theme name!")
            return
        
        # Determine if we're saving or updating
        action_verb = "Updating" if self.editing_theme_key else "Saving"
        print(f"*** Updating UI to show '{action_verb}...' ***", file=sys.stderr)
        theme_input.placeholder = f"{action_verb}..."
        preview.update(f"{action_verb}...")
        
        # Validate colors
        print("*** Validating colors ***", file=sys.stderr)
        if not all([self._is_valid_hex(c) for c in [self.color1, self.color2, self.color3]]):
            print("*** ERROR: Invalid color format ***", file=sys.stderr)
            preview.update("✗ Invalid color format")
            return
        print("*** Colors are valid ***", file=sys.stderr)
        
        # Call generate-14-colors.py to expand the gradient
        try:
            # Try multiple possible locations for the script
            possible_paths = [
                Path(__file__).parent.parent.parent / "generate-14-colors.py",  # Development
                Path("/home/tmo/Work/ForgeWorkLights/scripts/generate-14-colors.py"),  # Absolute
                Path("/usr/local/bin/omarchy-argb-generate-14-colors"),  # Installed
            ]
            
            script_path = None
            for p in possible_paths:
                if p.exists():
                    script_path = p
                    break
            
            if not script_path:
                raise FileNotFoundError(f"Could not find generate-14-colors.py in any of: {possible_paths}")
            
            print(f"\n*** Calling generate-14-colors.py ***", file=sys.stderr)
            print(f"*** Script path: {script_path} ***", file=sys.stderr)
            print(f"*** Script exists: {script_path.exists()} ***", file=sys.stderr)
            print(f"*** Themes DB path: {self.themes_db_path} ***", file=sys.stderr)
            print(f"*** Command: python3 {script_path} {self.color1} {self.color2} {self.color3} ***", file=sys.stderr)
            result = subprocess.run(
                ["python3", str(script_path), self.color1, self.color2, self.color3],
                capture_output=True,
                text=True,
                check=True
            )
            
            # Parse the 14 colors from output
            print(f"*** Script output: {result.stdout[:200]} ***", file=sys.stderr)
            colors_14 = [line.strip() for line in result.stdout.strip().split('\n') if line.strip().startswith('#')]
            print(f"*** Got {len(colors_14)} colors ***", file=sys.stderr)
            
            if len(colors_14) != 14:
                print(f"*** ERROR: Expected 14 colors, got {len(colors_14)} ***", file=sys.stderr)
                preview.update(f"✗ Got {len(colors_14)} colors, expected 14")
                return
            
            # Load existing themes
            print(f"*** Loading existing themes from {self.themes_db_path} ***", file=sys.stderr)
            if self.themes_db_path.exists():
                db_data = json.loads(self.themes_db_path.read_text())
                print(f"*** Loaded {len(db_data.get('themes', {}))} existing themes ***", file=sys.stderr)
            else:
                print("*** Creating new themes.json ***", file=sys.stderr)
                db_data = {"themes": {}}
            
            # Add or update theme
            if self.editing_theme_key:
                # Editing existing theme - use the original key
                theme_key = self.editing_theme_key
                print(f"*** Updating existing theme with key: {theme_key} ***", file=sys.stderr)
            else:
                # Creating new theme - generate key from name
                theme_key = self.theme_name.lower().replace(' ', '-')
                print(f"*** Adding new theme with key: {theme_key} ***", file=sys.stderr)
            
            db_data["themes"][theme_key] = {
                "name": self.theme_name.title(),
                "colors": colors_14
            }
            
            # Save back to file
            print(f"*** Writing to {self.themes_db_path} ***", file=sys.stderr)
            self.themes_db_path.write_text(json.dumps(db_data, indent=2))
            print(f"*** SUCCESS! File written ***", file=sys.stderr)
            
            # Show success message
            action_verb = "Updated" if self.editing_theme_key else "Saved"
            theme_input.placeholder = f"✓ {action_verb} '{self.theme_name}'!"
            preview.update(f"✓ {action_verb} '{self.theme_name}' with {len(colors_14)} colors!")
            
            # Post message to notify app
            self.post_message(self.ThemeCreated(theme_key))
            
            # Clear inputs and exit editing mode
            print("*** Clearing inputs ***", file=sys.stderr)
            self.action_clear()
            
        except subprocess.CalledProcessError as e:
            print(f"\n*** SUBPROCESS ERROR ***", file=sys.stderr)
            print(f"*** Return code: {e.returncode} ***", file=sys.stderr)
            print(f"*** Stdout: {e.stdout} ***", file=sys.stderr)
            print(f"*** Stderr: {e.stderr} ***", file=sys.stderr)
            theme_input.placeholder = "✗ Error generating colors"
            preview.update(f"✗ Error: {e.stderr[:50]}")
        except Exception as e:
            print(f"\n*** EXCEPTION: {type(e).__name__} ***", file=sys.stderr)
            print(f"*** Message: {str(e)} ***", file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)
            theme_input.placeholder = f"✗ Error: {str(e)}"
            preview.update(f"✗ Error: {str(e)[:50]}")
        
        print(f"\n*** action_save_theme() FINISHED ***\n", file=sys.stderr)
    
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
    
    def action_toggle_color_picker(self) -> None:
        """Toggle the color picker display"""
        picker = self.query_one("#theme-color-picker", ColorSelector)
        
        if self.color_picker_active:
            # Hide color picker
            picker.display = False
            self.color_picker_active = False
        else:
            # Determine which color input has focus
            try:
                focused = self.app.focused
                if focused and hasattr(focused, 'id'):
                    if focused.id == "color1-input":
                        self.active_color_input = "color1"
                        picker.set_color_from_hex(self.color1)
                    elif focused.id == "color2-input":
                        self.active_color_input = "color2"
                        picker.set_color_from_hex(self.color2)
                    elif focused.id == "color3-input":
                        self.active_color_input = "color3"
                        picker.set_color_from_hex(self.color3)
                    else:
                        # Default to color1 if no color input is focused
                        self.active_color_input = "color1"
                        picker.set_color_from_hex(self.color1)
                else:
                    self.active_color_input = "color1"
                    picker.set_color_from_hex(self.color1)
            except:
                self.active_color_input = "color1"
                picker.set_color_from_hex(self.color1)
            
            # Show color picker
            picker.display = True
            self.color_picker_active = True
            picker.focus()
    
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
        
        # Hide picker after selection
        picker = self.query_one("#theme-color-picker", ColorSelector)
        picker.display = False
        self.color_picker_active = False
        
        # Return focus to the color input
        if self.active_color_input == "color1":
            self.query_one("#color1-input", Input).focus()
        elif self.active_color_input == "color2":
            self.query_one("#color2-input", Input).focus()
        elif self.active_color_input == "color3":
            self.query_one("#color3-input", Input).focus()
