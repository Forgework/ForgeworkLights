"""
Theme creator widget for custom gradient themes
"""
from textual.widgets import Static, Input
from textual.containers import Container, Horizontal, Vertical
from textual.reactive import reactive
from textual.app import ComposeResult
from textual.message import Message
from pathlib import Path
import json
import subprocess
import sys


class ThemeCreator(Container):
    """Widget for creating custom themes with 3-color gradients"""
    
    class ThemeCreated(Message):
        """Message when a new theme is created"""
        def __init__(self, theme_name: str):
            super().__init__()
            self.theme_name = theme_name
    
    color1 = reactive("#a6d189")
    color2 = reactive("#e5c08f")
    color3 = reactive("#e78284")
    theme_name = reactive("")
    
    def __init__(self, themes_db_path: Path, **kwargs):
        super().__init__(**kwargs)
        self.themes_db_path = themes_db_path
        self.can_focus = True
    
    def on_mount(self) -> None:
        """Initialize preview on mount"""
        self._update_preview()
    
    def compose(self) -> ComposeResult:
        """Compose the theme creator UI"""
        with Vertical():
            # Theme name input
            with Horizontal(classes="compact-row"):
                yield Input(placeholder="Theme Name", id="theme-name-input", classes="name-input")
            
            # Gradient preview centered over color inputs
            with Horizontal(classes="compact-row"):
                yield Static("", id="gradient-preview", classes="preview-centered")
            
            # Color inputs in one row (no labels)
            with Horizontal(classes="compact-row"):
                yield Input(placeholder="#a6d189", value=self.color1, id="color1-input", classes="color-input", max_length=7)
                yield Input(placeholder="#e5c08f", value=self.color2, id="color2-input", classes="color-input", max_length=7)
                yield Input(placeholder="#e78284", value=self.color3, id="color3-input", classes="color-input", max_length=7)
            
            # Buttons below hex inputs
            with Horizontal(classes="compact-row"):
                yield Static("[S] Save  [C] Clear", id="button-area", classes="button-inline")
    
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
    
    def on_click(self, event) -> None:
        """Handle clicks on the button area"""
        # Check if click was on button area
        try:
            button_area = self.query_one("#button-area", Static)
            # Get the widget that was clicked
            if event.widget == button_area:
                # Buttons are just keyboard shortcuts, show message
                import sys
                print("Use [S] to save or [C] to clear", file=sys.stderr)
        except:
            pass
    
    def on_key(self, event) -> None:
        """Handle key presses for debug"""
        if event.key == "s":
            print("S key pressed, calling save_theme", file=sys.stderr)
        elif event.key == "c":
            print("C key pressed, calling clear", file=sys.stderr)
    
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
    
    def action_save_theme(self) -> None:
        """Save the custom theme"""
        print(f"Save action called. Theme name: '{self.theme_name}'", file=sys.stderr)
        if not self.theme_name:
            print("No theme name provided", file=sys.stderr)
            return
        
        # Validate colors
        if not all([self._is_valid_hex(c) for c in [self.color1, self.color2, self.color3]]):
            print("Invalid color format", file=sys.stderr)
            return
        
        # Call generate-14-colors.py to expand the gradient
        try:
            script_path = Path(__file__).parent.parent.parent / "scripts" / "generate-14-colors.py"
            print(f"Script path: {script_path}", file=sys.stderr)
            print(f"Script exists: {script_path.exists()}", file=sys.stderr)
            print(f"Themes DB path: {self.themes_db_path}", file=sys.stderr)
            result = subprocess.run(
                ["python3", str(script_path), self.color1, self.color2, self.color3],
                capture_output=True,
                text=True,
                check=True
            )
            
            # Parse the 14 colors from output
            colors_14 = [line.strip() for line in result.stdout.strip().split('\n') if line.strip().startswith('#')]
            
            if len(colors_14) != 14:
                print(f"Error: Expected 14 colors, got {len(colors_14)}", file=sys.stderr)
                return
            
            # Load existing themes
            if self.themes_db_path.exists():
                db_data = json.loads(self.themes_db_path.read_text())
            else:
                db_data = {"themes": {}}
            
            # Add new theme
            theme_key = self.theme_name.lower().replace(' ', '-')
            db_data["themes"][theme_key] = {
                "name": self.theme_name.title(),
                "colors": colors_14
            }
            
            # Save back to file
            self.themes_db_path.write_text(json.dumps(db_data, indent=2))
            
            print(f"✓ Created theme: {self.theme_name} (key: {theme_key})", file=sys.stderr)
            print(f"✓ Saved {len(colors_14)} colors to {self.themes_db_path}", file=sys.stderr)
            
            # Post message to notify app
            self.post_message(self.ThemeCreated(theme_key))
            
            # Clear inputs
            self.action_clear()
            
        except subprocess.CalledProcessError as e:
            print(f"Error generating colors: {e.stderr}", file=sys.stderr)
        except Exception as e:
            print(f"Error saving theme: {e}", file=sys.stderr)
    
    def action_clear(self) -> None:
        """Clear all inputs"""
        self.theme_name = ""
        self.color1 = "#a6d189"
        self.color2 = "#e5c08f"
        self.color3 = "#e78284"
        self.query_one("#theme-name-input", Input).value = ""
        self.query_one("#color1-input", Input).value = self.color1
        self.query_one("#color2-input", Input).value = self.color2
        self.query_one("#color3-input", Input).value = self.color3
        self._update_preview()
    
    BINDINGS = [
        ("s", "save_theme", "Save theme"),
        ("c", "clear", "Clear"),
    ]
