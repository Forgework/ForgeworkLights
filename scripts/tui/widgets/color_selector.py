"""
Color Selector - A visual color picker widget for Textual TUI
"""
from textual.widgets import Static
from textual.containers import Vertical, Horizontal
from textual.reactive import reactive
from textual.app import ComposeResult
from textual.message import Message
from textual import events
import colorsys


class ColorSelector(Static):
    """
    A full-spectrum color picker widget for TUI applications.
    Displays a gradient with:
    - X-axis: Hue (0° to 360° - all colors)
    - Y-axis: White (bottom) → Saturated colors (middle) → Black (top)
    Navigation via keyboard (arrow keys) or mouse click.
    """
    
    class ColorSelected(Message):
        """Message sent when a color is selected"""
        def __init__(self, hex_color: str, rgb: tuple):
            super().__init__()
            self.hex_color = hex_color
            self.rgb = rgb
    
    selected_color = reactive((255, 0, 0))  # RGB tuple
    cursor_x = reactive(0)  # 0-1 normalized
    cursor_y = reactive(0)  # 0-1 normalized
    
    def __init__(self, width: int = 40, height: int = 12, **kwargs):
        super().__init__(**kwargs)
        self.grid_width = width
        self.grid_height = height
        self.can_focus = True
    
    def compose(self) -> ComposeResult:
        """Compose the color selector display"""
        with Horizontal():
            yield Static("", id="color-grid")
            yield Static("", id="color-info")
    
    def on_mount(self) -> None:
        """Initialize the color selector"""
        self._update_display()
    
    def render_color_grid(self) -> str:
        """Render the color gradient grid with white->saturated->black"""
        lines = []
        for y in range(self.grid_height):
            line_chars = []
            for x in range(self.grid_width):
                # Normalize coordinates
                nx = x / (self.grid_width - 1) if self.grid_width > 1 else 0
                ny = y / (self.grid_height - 1) if self.grid_height > 1 else 0
                
                # Hue along x-axis (0 to 1 = 0° to 360°)
                hue = nx
                
                # Y-axis: bottom=white, middle=saturated, top=black
                # ny=0 (top) -> black (V=0)
                # ny=0.5 (middle) -> saturated (S=1, V=1)
                # ny=1 (bottom) -> white (S=0, V=1)
                if ny <= 0.5:
                    # Top half: black to saturated
                    # ny: 0.0 -> 0.5 maps to V: 0.0 -> 1.0
                    saturation = 1.0
                    value = ny * 2  # 0 to 1
                else:
                    # Bottom half: saturated to white
                    # ny: 0.5 -> 1.0 maps to S: 1.0 -> 0.0
                    saturation = 2.0 - (ny * 2)  # 1 to 0
                    value = 1.0
                
                # Convert HSV to RGB
                r, g, b = colorsys.hsv_to_rgb(hue, saturation, value)
                r = int(r * 255)
                g = int(g * 255)
                b = int(b * 255)
                hex_color = f"#{r:02x}{g:02x}{b:02x}"
                
                # Show cursor position with special character
                if abs(nx - self.cursor_x) < 0.05 and abs(ny - self.cursor_y) < 0.05:
                    line_chars.append(f"[{hex_color}]◉[/]")
                else:
                    line_chars.append(f"[{hex_color}]█[/]")
            
            lines.append("".join(line_chars))
        
        return "\n".join(lines)
    
    def _update_display(self) -> None:
        """Update the color grid and info displays"""
        # Update grid
        grid = self.query_one("#color-grid", Static)
        grid.update(self.render_color_grid())
        
        # Update info
        r, g, b = self.selected_color
        hex_color = f"#{r:02x}{g:02x}{b:02x}"
        
        # Calculate HSV for display
        h, s, v = colorsys.rgb_to_hsv(r/255, g/255, b/255)
        h_deg = int(h * 360)
        s_pct = int(s * 100)
        v_pct = int(v * 100)
        
        # Create vertical info display with shorthand labels
        info_lines = [
            f"[{hex_color}]█████[/]",
            "",
            f"HEX:",
            f"{hex_color}",
            "",
            f"RGB:",
            f"R:{r}",
            f"G:{g}",
            f"B:{b}",
            "",
            f"HSV:",
            f"H:{h_deg}°",
            f"S:{s_pct}%",
            f"V:{v_pct}%",
        ]
        info_text = "\n".join(info_lines)
        
        info = self.query_one("#color-info", Static)
        info.update(info_text)
    
    def _calculate_color_at_cursor(self) -> tuple:
        """Calculate RGB color at current cursor position"""
        hue = self.cursor_x
        
        # Map cursor_y to saturation and value
        # cursor_y=0 (top) -> black (V=0)
        # cursor_y=0.5 (middle) -> saturated (S=1, V=1)
        # cursor_y=1 (bottom) -> white (S=0, V=1)
        if self.cursor_y <= 0.5:
            # Top half: black to saturated
            saturation = 1.0
            value = self.cursor_y * 2  # 0 to 1
        else:
            # Bottom half: saturated to white
            saturation = 2.0 - (self.cursor_y * 2)  # 1 to 0
            value = 1.0
        
        r, g, b = colorsys.hsv_to_rgb(hue, saturation, value)
        r = int(r * 255)
        g = int(g * 255)
        b = int(b * 255)
        
        return (r, g, b)
    
    def on_click(self, event: events.Click) -> None:
        """Handle mouse clicks on the color grid"""
        # Calculate position relative to grid
        # Note: This is approximate since we don't have exact widget positioning
        # In practice, keyboard navigation works better for TUI
        grid = self.query_one("#color-grid", Static)
        
        # Estimate cursor position based on click
        # This is simplified - exact positioning would need widget region info
        self.cursor_x = min(1.0, max(0.0, event.x / self.grid_width))
        self.cursor_y = min(1.0, max(0.0, event.y / self.grid_height))
        
        self.selected_color = self._calculate_color_at_cursor()
        self._update_display()
        self._emit_color_selected()
    
    def on_key(self, event: events.Key) -> None:
        """Handle keyboard navigation"""
        step = 0.05  # 5% movement per keypress
        
        if event.key == "left":
            self.cursor_x = max(0.0, self.cursor_x - step)
            event.prevent_default()
        elif event.key == "right":
            self.cursor_x = min(1.0, self.cursor_x + step)
            event.prevent_default()
        elif event.key == "up":
            self.cursor_y = max(0.0, self.cursor_y - step)
            event.prevent_default()
        elif event.key == "down":
            self.cursor_y = min(1.0, self.cursor_y + step)
            event.prevent_default()
        elif event.key == "enter":
            # Select current color
            self.selected_color = self._calculate_color_at_cursor()
            self._emit_color_selected()
            event.prevent_default()
            return
        else:
            return
        
        # Update color at new cursor position
        self.selected_color = self._calculate_color_at_cursor()
        self._update_display()
    
    def _emit_color_selected(self) -> None:
        """Emit color selection message"""
        r, g, b = self.selected_color
        hex_color = f"#{r:02x}{g:02x}{b:02x}"
        self.post_message(self.ColorSelected(hex_color, (r, g, b)))
    
    def set_color_from_hex(self, hex_color: str) -> None:
        """Set the selector to show a specific hex color"""
        if not hex_color.startswith('#') or len(hex_color) != 7:
            return
        
        try:
            r = int(hex_color[1:3], 16)
            g = int(hex_color[3:5], 16)
            b = int(hex_color[5:7], 16)
            
            # Convert to HSV to position cursor
            h, s, v = colorsys.rgb_to_hsv(r/255, g/255, b/255)
            self.cursor_x = h
            
            # Map HSV to cursor_y position
            # Need to find where on the gradient this color would be
            if v <= 0.5:
                # Dark colors: map V [0,0.5] to cursor_y [0,0.25]
                self.cursor_y = v / 2
            elif s >= 0.5:
                # Saturated colors: map V [0.5,1] and S [0.5,1] to cursor_y around middle
                # Position based on value, centered around 0.5
                self.cursor_y = v / 2
            else:
                # Light/white colors: map S [0,0.5] to cursor_y [0.75,1]
                self.cursor_y = 1.0 - (s / 2)
            
            self.selected_color = (r, g, b)
            self._update_display()
        except ValueError:
            pass
