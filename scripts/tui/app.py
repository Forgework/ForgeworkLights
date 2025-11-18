"""
Main ForgeworkLights TUI Application
"""
import json
import subprocess
import sys
import time
from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Container
from textual.timer import Timer
from textual.worker import Worker, WorkerState
import os
import select
import struct
import traceback

from .constants import (
    STATE_FILE,
    BRIGHTNESS_FILE,
    THEMES_DB_PATH,
    THEME_SYMLINK,
    LED_THEME_FILE,
    ANIMATION_FILE,
    DAEMON_BINARY,
    AUTO_REFRESH_INTERVAL
)
from .styles import CSS
from .widgets import (
    BorderTop,
    BorderMiddle,
    CollapsibleBorderMiddle,
    Spacer,
    Filler,
    ControlFooterBorder,
    StatusPanel,
    GradientPanel,
    BrightnessPanel,
    LogsModal,
    ThemeCreator,
    AnimationsPanel
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
        
        self.update_timer = None
        self.inotify_fd = None
        self.inotify_worker = None
        self.last_omarchy_theme = None
    
    def compose(self) -> ComposeResult:
        with Container(id="main-panel"):
            # Scrollable content area
            with Container(id="content-area"):
                yield BorderTop("ForgeworkLights Control Panel")
                yield Spacer()
                yield StatusPanel(id="status-panel")
                yield Spacer()
                yield BorderMiddle("Theme Selection")
                yield GradientPanel(id="gradient-panel")
                yield CollapsibleBorderMiddle("Create Custom Theme", section_id="theme-creator", is_expanded=False, id="theme-creator-border")
                yield ThemeCreator(THEMES_DB_PATH, id="theme-creator")
                yield BorderMiddle("Animations")
                yield AnimationsPanel(id="animations-panel")
                yield Spacer(id="animations-end-spacer")
            
            # Bottom section (docked)
            with Container(id="bottom-section"):
                yield BorderMiddle("Brightness")
                yield Spacer()
                yield BrightnessPanel(id="brightness-panel")
                yield Spacer()
                yield ControlFooterBorder()
    
    def on_mount(self) -> None:
        """Initialize the app"""
        self.title = "ForgeworkLights"
        self.sub_title = "[Tab] Switch  [↑↓←→] Navigate  [Enter] Apply  [S] Save  [C] Clear  [L] Logs  [Ctrl+Q] Quit"
        self.refresh_status()
        # Start periodic update every 2 seconds (only for daemon status now)
        # Brightness, theme, and themes.json are all handled by inotify
        self.update_timer = self.set_interval(AUTO_REFRESH_INTERVAL, self._refresh_daemon_status)
        
        # Start watching for Omarchy theme changes (inotify-based)
        self._start_theme_watcher()
        
        # Hide theme creator initially (collapsed state)
        theme_creator = self.query_one("#theme-creator", ThemeCreator)
        theme_creator.display = False
        
        # Focus the gradient panel for keyboard navigation
        gradient_panel = self.query_one("#gradient-panel", GradientPanel)
        gradient_panel.focus()
    
    def _refresh_daemon_status(self) -> None:
        """Refresh only daemon status (polling - can't use inotify for process check)"""
        try:
            result = subprocess.run(["pgrep", "-x", "omarchy-argb"], capture_output=True)
            daemon_status = "Running " if result.returncode == 0 else "Stopped "
        except:
            daemon_status = "Unknown"
        
        status_panel = self.query_one("#status-panel", StatusPanel)
        status_panel.daemon_status = daemon_status
    
    def refresh_status(self) -> None:
        """Refresh all status info (called manually, not on timer)"""
        print(f"[TUI] refresh_status() called", file=sys.stderr)
        
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
                        print(f"[TUI] Status bar theme resolved: {theme}", file=sys.stderr)
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
            
            # Theme change will trigger daemon reload via inotify
            # No need to do anything else - daemon handles animations
            
            # Force immediate refresh of status after a short delay
            self.set_timer(0.5, self.refresh_status)
            
        except Exception as e:
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
    
    def on_collapsible_border_middle_toggled(self, message: CollapsibleBorderMiddle.Toggled) -> None:
        """Handle collapsible border toggle"""
        if message.section_id == "theme-creator":
            theme_creator = self.query_one("#theme-creator", ThemeCreator)
            theme_creator.display = message.is_expanded
    
    def on_theme_creator_theme_created(self, message: ThemeCreator.ThemeCreated) -> None:
        """Handle custom theme creation"""
        print(f"Theme created: {message.theme_name}", file=sys.stderr)
        # Refresh the gradient panel to show the new theme
        gradient_panel = self.query_one("#gradient-panel", GradientPanel)
        gradient_panel._theme_list = []  # Reset list to force reload
        gradient_panel._update_display()
        
        # Theme change will trigger daemon to reload animation colors via inotify
    
    def on_gradient_panel_theme_edit_requested(self, message: GradientPanel.ThemeEditRequested) -> None:
        """Handle theme edit request from gradient panel"""
        print(f"Edit requested for theme: {message.theme_key}", file=sys.stderr)
        # Expand the theme creator section if collapsed
        border = self.query_one("#theme-creator-border", CollapsibleBorderMiddle)
        theme_creator = self.query_one("#theme-creator", ThemeCreator)
        if not border.is_expanded:
            border.is_expanded = True
            border.refresh()
            theme_creator.display = True
        # Load the theme into the theme creator
        theme_creator.load_theme_for_editing(message.theme_key, message.theme_name, message.colors)
    
    def on_gradient_panel_theme_delete_requested(self, message: GradientPanel.ThemeDeleteRequested) -> None:
        """Handle theme delete request from gradient panel"""
        print(f"Delete requested for theme: {message.theme_key}", file=sys.stderr)
        
        try:
            # Load themes database
            if not THEMES_DB_PATH.exists():
                print("Themes database not found", file=sys.stderr)
                return
            
            db_data = json.loads(THEMES_DB_PATH.read_text())
            
            if "themes" in db_data and message.theme_key in db_data["themes"]:
                # Delete the theme
                del db_data["themes"][message.theme_key]
                
                # Save back to file
                THEMES_DB_PATH.write_text(json.dumps(db_data, indent=2))
                print(f"Deleted theme: {message.theme_name}", file=sys.stderr)
                
                # Refresh the gradient panel to update the list
                gradient_panel = self.query_one("#gradient-panel", GradientPanel)
                gradient_panel._theme_list = []
                gradient_panel._update_display()
                self.refresh_status()
            else:
                print(f"Theme not found in database: {message.theme_key}", file=sys.stderr)
        except Exception as e:
            print(f"Error deleting theme: {e}", file=sys.stderr)
            traceback.print_exc()
    
    def on_gradient_panel_theme_sync_requested(self, message: GradientPanel.ThemeSyncRequested) -> None:
        """Handle theme sync request from gradient panel"""
        print("\n=== Theme sync requested ===", file=sys.stderr)
        
        try:
            # Import and run sync_themes directly
            sys.path.insert(0, str(Path(__file__).parent.parent))
            from sync_themes import sync_themes
            
            changes = sync_themes(verbose=True)
            print(f"Sync completed: {changes} themes added/updated", file=sys.stderr)
            
            # Refresh the gradient panel to show new themes
            print("Refreshing theme list...", file=sys.stderr)
            gradient_panel = self.query_one("#gradient-panel", GradientPanel)
            gradient_panel._theme_list = []
            gradient_panel._update_display()
            self.refresh_status()
            print("Theme list refreshed", file=sys.stderr)
            
        except Exception as e:
            print(f"ERROR: Exception during sync: {e}", file=sys.stderr)
            traceback.print_exc()
    
    def on_animations_panel_animation_selected(self, message: AnimationsPanel.AnimationSelected) -> None:
        """Handle animation selection - save choice for daemon to execute"""
        params_str = f" with params {message.params}" if message.params else ""
        print(f"[TUI] Animation selected: {message.animation_name}{params_str}", file=sys.stderr)
        
        try:
            # Save animation preference to config file
            # Daemon will detect this change via inotify and switch animations
            # Parameters are already saved by AnimationsPanel to animation-params.json
            ANIMATION_FILE.parent.mkdir(parents=True, exist_ok=True)
            ANIMATION_FILE.write_text(f"{message.animation_name}\n")
            print(f"[TUI] Saved animation preference - daemon will handle execution", file=sys.stderr)
            
        except Exception as e:
            print(f"[TUI] Failed to save animation: {e}", file=sys.stderr)
            traceback.print_exc()
    
    # Animation execution is handled by the daemon
    # TUI only saves user's animation choice to config file
    
    def _start_theme_watcher(self):
        """Start inotify-based watcher for config file changes"""
        try:
            # Create inotify instance
            self.inotify_fd = os.inotify_init1(os.O_NONBLOCK | os.O_CLOEXEC)
            
            # Watch Omarchy theme directory
            omarchy_dir = THEME_SYMLINK.parent
            if omarchy_dir.exists():
                os.inotify_add_watch(
                    self.inotify_fd,
                    str(omarchy_dir),
                    os.IN_ATTRIB | os.IN_CLOSE_WRITE | os.IN_MOVE_SELF | os.IN_DELETE_SELF | 
                    os.IN_CREATE | os.IN_DELETE | os.IN_MOVED_TO | os.IN_MOVED_FROM
                )
                print(f"Started inotify watcher on {omarchy_dir}", file=sys.stderr)
            
            # Watch omarchy-argb config directory
            config_dir = LED_THEME_FILE.parent
            if config_dir.exists():
                config_dir.mkdir(parents=True, exist_ok=True)
                os.inotify_add_watch(
                    self.inotify_fd,
                    str(config_dir),
                    os.IN_ATTRIB | os.IN_CLOSE_WRITE | os.IN_MOVE_SELF | os.IN_DELETE_SELF | 
                    os.IN_CREATE | os.IN_DELETE | os.IN_MOVED_TO | os.IN_MOVED_FROM
                )
                print(f"Started inotify watcher on {config_dir}", file=sys.stderr)
            
            # Initialize current theme
            if THEME_SYMLINK.exists() and THEME_SYMLINK.is_symlink():
                current_theme_dir = THEME_SYMLINK.resolve()
                self.last_omarchy_theme = current_theme_dir.name
            
            # Start worker to read inotify events
            self.inotify_worker = self.run_worker(
                self._inotify_loop,
                name="inotify_worker",
                group="watchers",
                thread=True
            )
            
        except Exception as e:
            print(f"Failed to start config watcher: {e}", file=sys.stderr)
            traceback.print_exc()
    
    def _inotify_loop(self):
        """Background loop to process inotify events"""
        print("[TUI] inotify loop started", file=sys.stderr)
        
        while self.inotify_fd is not None and self.inotify_worker and not self.inotify_worker.is_cancelled:
            try:
                # Wait for events with a timeout
                readable, _, _ = select.select([self.inotify_fd], [], [], 1.0)
                
                if not readable:
                    continue
                
                # Read events
                events = os.read(self.inotify_fd, 4096)
                offset = 0
                
                while offset < len(events):
                    # Parse inotify event structure
                    wd, mask, cookie, name_len = struct.unpack_from('iIII', events, offset)
                    offset += struct.calcsize('iIII')
                    
                    name = events[offset:offset + name_len].rstrip(b'\x00').decode('utf-8')
                    offset += name_len
                    
                    # Debug logging
                    print(f"inotify event: {name} (mask: {mask})", file=sys.stderr)
                    
                    # Handle different file changes
                    if name == "theme" or "theme" in name:
                        print(f"Detected Omarchy theme change: {name}", file=sys.stderr)
                        self.call_from_thread(self._on_omarchy_theme_changed)
                    elif name == LED_THEME_FILE.name:
                        print(f"Detected led-theme change", file=sys.stderr)
                        self.call_from_thread(self.refresh_status)
                    elif name == BRIGHTNESS_FILE.name:
                        print(f"Detected brightness change", file=sys.stderr)
                        self.call_from_thread(self._on_brightness_changed)
                    elif name == THEMES_DB_PATH.name:
                        print(f"Detected themes.json change", file=sys.stderr)
                        self.call_from_thread(self._on_themes_db_changed)
                
            except OSError:
                # FD was closed, exit gracefully
                break
            except Exception as e:
                # Other errors, log and continue
                print(f"[TUI] inotify loop error: {e}", file=sys.stderr)
                pass
        
        print("[TUI] inotify loop exited", file=sys.stderr)
    
    def _on_omarchy_theme_changed(self):
        """Handle Omarchy theme change event (from inotify)"""
        try:
            # Get new theme FIRST before checking anything
            if THEME_SYMLINK.exists() and THEME_SYMLINK.is_symlink():
                current_theme_dir = THEME_SYMLINK.resolve()
                current_theme = current_theme_dir.name
            else:
                return
            
            # Check if it actually changed
            if self.last_omarchy_theme == current_theme:
                return  # No change
            
            print(f"[TUI] Omarchy theme changed: {self.last_omarchy_theme} -> {current_theme}", file=sys.stderr)
            self.last_omarchy_theme = current_theme
            
            # Daemon will detect theme change via inotify and reload colors automatically
            
            # Always refresh status display to show new theme name
            self.refresh_status()
        
        except Exception as e:
            print(f"[TUI] Error handling theme change: {e}", file=sys.stderr)
            traceback.print_exc()
    
    def _on_brightness_changed(self):
        """Handle brightness file change (from inotify)"""
        try:
            # Read new brightness value
            if self.brightness_file.exists():
                brightness_pct = int(float(self.brightness_file.read_text().strip()) * 100)
            else:
                brightness_pct = 100
            
            # Update display only if not currently being adjusted by user
            panel = self.query_one("#brightness-panel", BrightnessPanel)
            if not hasattr(self, '_brightness_adjusting') or not self._brightness_adjusting:
                panel.brightness = brightness_pct
            
            # Update status panel
            status_panel = self.query_one("#status-panel", StatusPanel)
            status_panel.brightness_value = brightness_pct
        
        except Exception as e:
            pass  # Silently ignore
    
    def _on_themes_db_changed(self):
        """Handle themes database change (from inotify)"""
        try:
            # Refresh gradient panel to show new/updated themes
            gradient_panel = self.query_one("#gradient-panel", GradientPanel)
            gradient_panel._theme_list = []
            gradient_panel._update_display()
            
            # Theme update will trigger daemon to reload animation colors via inotify
        
        except Exception as e:
            pass  # Silently ignore
    
    def on_unmount(self):
        """Clean up when app exits"""
        print("[TUI] Shutting down, cleaning up workers...", file=sys.stderr)
        
        # Stop timers first
        if self.update_timer:
            self.update_timer.stop()
        
        # Stop inotify watcher worker
        if self.inotify_worker:
            print("[TUI] Cancelling inotify worker", file=sys.stderr)
            self.inotify_worker.cancel()
        
        # Close inotify fd (this will cause the worker loop to exit)
        if self.inotify_fd is not None:
            print("[TUI] Closing inotify fd", file=sys.stderr)
            try:
                os.close(self.inotify_fd)
            except:
                pass
            self.inotify_fd = None
        
        # Wait a moment for workers to finish
        time.sleep(0.1)
        
        print("[TUI] Cleanup complete", file=sys.stderr)
