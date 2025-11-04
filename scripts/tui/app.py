"""
Main ForgeworkLights TUI Application
"""
import json
import subprocess
import sys
from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Container
from textual.timer import Timer

from .constants import (
    STATE_FILE,
    BRIGHTNESS_FILE,
    THEMES_DB_PATH,
    THEME_SYMLINK,
    LED_THEME_FILE,
    DAEMON_BINARY,
    AUTO_REFRESH_INTERVAL
)
from .styles import CSS
from .widgets import (
    BorderTop,
    BorderMiddle,
    Spacer,
    Filler,
    ControlFooterBorder,
    StatusPanel,
    GradientPanel,
    BrightnessPanel,
    LogsModal,
    ThemeCreator
)


class ForgeworkLightsTUI(App):
    """Main TUI application - BTOP style"""
    
    CSS = CSS
    
    BINDINGS = [
        ("ctrl+q", "quit", "Quit"),
        ("escape", "quit", "Quit"),
        ("l", "view_logs", "Logs"),
    ]
    
    def __init__(self):
        super().__init__()
        self.state_file = STATE_FILE
        self.brightness_file = BRIGHTNESS_FILE
        self.update_timer: Timer | None = None
    
    def compose(self) -> ComposeResult:
        with Container(id="main-panel"):
            yield BorderTop("ForgeworkLights Control Panel")
            yield Spacer()
            yield StatusPanel(id="status-panel")
            yield Spacer()
            yield BorderMiddle("Theme Selection")
            yield GradientPanel(id="gradient-panel")
            yield BorderMiddle("Create Custom Theme")
            yield ThemeCreator(THEMES_DB_PATH, id="theme-creator")
            yield BorderMiddle("Brightness")
            yield Spacer()
            yield BrightnessPanel(id="brightness-panel")
            yield Spacer()
            yield ControlFooterBorder()
    
    def on_mount(self) -> None:
        """Initialize and start auto-refresh"""
        self.title = "ForgeworkLights"
        self.sub_title = "[Tab] Switch  [↑↓←→] Navigate  [Enter] Apply  [S] Save Theme  [C] Clear  [L] Logs  [Ctrl+Q] Quit"
        self.refresh_status()
        # Auto-refresh every 2 seconds
        self.update_timer = self.set_interval(AUTO_REFRESH_INTERVAL, self.refresh_status)
        # Focus the gradient panel for keyboard navigation
        gradient_panel = self.query_one("#gradient-panel", GradientPanel)
        gradient_panel.focus()
    
    def refresh_status(self) -> None:
        """Refresh daemon status, theme, brightness, and gradient"""
        # Get daemon status
        try:
            result = subprocess.run(["pgrep", "-x", "omarchy-argb"], capture_output=True)
            daemon_status = "Running " if result.returncode == 0 else "Stopped "
        except:
            daemon_status = "Unknown"
        
        # Get LED theme name from config file
        theme = "None"
        try:
            if LED_THEME_FILE.exists():
                led_theme = LED_THEME_FILE.read_text().strip()
                if led_theme == "match":
                    # Show that we're matching Omarchy, with the current Omarchy theme name
                    if THEME_SYMLINK.exists() and THEME_SYMLINK.is_symlink():
                        omarchy_theme_dir = THEME_SYMLINK.resolve()
                        omarchy_theme_name = omarchy_theme_dir.name.capitalize()
                        theme = f"Match ({omarchy_theme_name})"
                    else:
                        theme = "Match Omarchy"
                else:
                    # Show the specific LED theme
                    theme = led_theme.capitalize()
            else:
                # Default to matching Omarchy if no preference set
                if THEME_SYMLINK.exists() and THEME_SYMLINK.is_symlink():
                    omarchy_theme_dir = THEME_SYMLINK.resolve()
                    omarchy_theme_name = omarchy_theme_dir.name.capitalize()
                    theme = f"Match ({omarchy_theme_name})"
                else:
                    theme = "Match Omarchy"
        except Exception as e:
            print(f"Error resolving LED theme: {e}", file=sys.stderr)
        
        # Get brightness - only update display, don't override user changes
        try:
            if self.brightness_file.exists():
                brightness_pct = int(float(self.brightness_file.read_text().strip()) * 100)
            else:
                brightness_pct = 100
        except:
            brightness_pct = 100
        
        # Update panels
        status_panel = self.query_one("#status-panel", StatusPanel)
        status_panel.daemon_status = daemon_status
        status_panel.theme_name = theme
        status_panel.brightness_value = brightness_pct
        
        gradient_panel = self.query_one("#gradient-panel", GradientPanel)
        gradient_panel.current_theme = theme
        
        # Only update brightness display if not currently being adjusted by user
        panel = self.query_one("#brightness-panel", BrightnessPanel)
        if not hasattr(self, '_brightness_adjusting') or not self._brightness_adjusting:
            panel.brightness = brightness_pct
    
    
    def on_control_footer_border_control_clicked(self, message: ControlFooterBorder.ControlClicked) -> None:
        """Handle footer control clicks"""
        if message.action_id == "quit":
            self.exit()
        elif message.action_id == "bright_down":
            self.action_brightness_down()
        elif message.action_id == "bright_up":
            self.action_brightness_up()
        elif message.action_id == "logs":
            self.action_view_logs()
    
    def action_view_logs(self) -> None:
        """Show logs modal"""
        self.push_screen(LogsModal())
    
    def on_brightness_panel_brightness_changed(self, message: BrightnessPanel.BrightnessChanged) -> None:
        """Handle brightness slider clicks"""
        try:
            self._brightness_adjusting = True
            panel = self.query_one("#brightness-panel", BrightnessPanel)
            panel.brightness = message.value
            self._apply_brightness(message.value)
            panel.refresh()
            self._brightness_adjusting = False
        except Exception:
            self._brightness_adjusting = False
    
    def on_gradient_panel_theme_selected(self, message: GradientPanel.ThemeSelected) -> None:
        """Handle theme selection"""
        import subprocess
        
        try:
            # Create config dir if it doesn't exist
            LED_THEME_FILE.parent.mkdir(parents=True, exist_ok=True)
            
            if message.match_omarchy:
                # Write "match" to led-theme file to follow Omarchy theme
                LED_THEME_FILE.write_text("match\n")
                print("Set LED theme to match Omarchy", file=sys.stderr)
                
                # Touch the symlink to trigger daemon reload via inotify
                if THEME_SYMLINK.exists():
                    THEME_SYMLINK.touch()
            else:
                # Write specific theme name to led-theme file
                LED_THEME_FILE.write_text(f"{message.theme_name}\n")
                print(f"Set LED theme to: {message.theme_name}", file=sys.stderr)
                
                # Touch the LED theme file to trigger daemon reload via inotify
                LED_THEME_FILE.touch()
            
            # Update the gradient panel display to show new arrow position
            gradient_panel = self.query_one("#gradient-panel", GradientPanel)
            gradient_panel._update_display()
            
            # Force immediate refresh of status after a short delay
            self.set_timer(0.5, self.refresh_status)
            
        except Exception as e:
            import traceback
            print(f"Failed to apply theme: {e}", file=sys.stderr)
            traceback.print_exc()
    
    def action_brightness_up(self) -> None:
        """Increase brightness by 5%"""
        try:
            self._brightness_adjusting = True
            panel = self.query_one("#brightness-panel", BrightnessPanel)
            new_brightness = min(100, panel.brightness + 5)
            panel.brightness = new_brightness
            self._apply_brightness(new_brightness)
            panel.refresh()
            self._brightness_adjusting = False
        except Exception:
            self._brightness_adjusting = False
    
    def action_brightness_down(self) -> None:
        """Decrease brightness by 5%"""
        try:
            self._brightness_adjusting = True
            panel = self.query_one("#brightness-panel", BrightnessPanel)
            new_brightness = max(0, panel.brightness - 5)
            panel.brightness = new_brightness
            self._apply_brightness(new_brightness)
            panel.refresh()
            self._brightness_adjusting = False
        except Exception:
            self._brightness_adjusting = False
    
    def _apply_brightness(self, brightness: int) -> None:
        """Apply brightness to daemon and save to file"""
        try:
            decimal = brightness / 100.0
            # Write to brightness file first
            self.brightness_file.parent.mkdir(parents=True, exist_ok=True)
            self.brightness_file.write_text(f"{decimal:.2f}\n")
            # Then apply to daemon
            result = subprocess.run(
                [DAEMON_BINARY, "brightness", str(decimal)],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode != 0:
                print(f"Brightness command failed: {result.stderr}", file=sys.stderr)
        except Exception as e:
            print(f"Failed to apply brightness: {e}", file=sys.stderr)
    
    def on_theme_creator_theme_created(self, message: ThemeCreator.ThemeCreated) -> None:
        """Handle custom theme creation"""
        print(f"Theme created: {message.theme_name}", file=sys.stderr)
        # Refresh the gradient panel to show the new theme
        gradient_panel = self.query_one("#gradient-panel", GradientPanel)
        # Force a complete refresh by rebuilding the theme list
        gradient_panel._theme_list = []  # Clear the list
        gradient_panel._update_display()  # This will rebuild the theme list
        self.refresh_status()
