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
from textual.widgets import Static
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
    AUTO_REFRESH_INTERVAL,
    AETHER_THEME_DIR,
)
from .styles import CSS
from .theme import THEME
from . import theme as theme_module
from . import styles as styles_module
from .widgets import (
    ControlFooterBorder,
    BorderTop,
    BorderMiddle,
    Filler,
    Spacer,
    StatusPanel,
    ThemeSelectionPanel,
    BrightnessPanel,
    ThemeCreator,
    AnimationsPanel
)


class ForgeworkLightsTUI(App):
    """Main TUI application - BTOP style"""
    
    CSS = CSS
    
    BINDINGS = [
        ("ctrl+q", "quit", "Quit"),
        ("escape", "quit", "Quit"),
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
        self.omarchy_wd = None  # Watch descriptor for Omarchy theme directory
        self.config_wd = None   # Watch descriptor for config directory
        self.aether_wd = None   # Watch descriptor for Aether theme directory
    
    def compose(self) -> ComposeResult:
        with Container(id="main-panel"):
            # Scrollable content area
            with Container(id="content-area"):
                yield BorderTop("ForgeWorkLights")
                yield StatusPanel(id="status-panel") 
                yield BrightnessPanel(id="brightness-panel")
                yield Spacer()
                yield BorderMiddle("Theme Selection")
                yield ThemeSelectionPanel(id="theme-selection-panel")
                yield BorderMiddle("Create Custom Theme")
                yield ThemeCreator(THEMES_DB_PATH, id="theme-creator")
                yield BorderMiddle("Animations")
                yield AnimationsPanel(id="animations-panel")
                yield Filler()
            
            # Bottom section (docked)
            with Container(id="bottom-section"):
                yield ControlFooterBorder()
    
    def on_mount(self) -> None:
        """Initialize the app"""
        self.title = "ForgeWorkLights"
        self.sub_title = "[Tab] Switch  [↑↓←→] Navigate  [Enter] Apply  [S] Save  [C] Clear  [Ctrl+Q] Quit"
        self.refresh_status()
        # Start periodic update every 2 seconds (only for daemon status now)
        # Brightness, theme, and the LED themes database are all handled by inotify
        self.update_timer = self.set_interval(AUTO_REFRESH_INTERVAL, self._refresh_daemon_status)
        
        # Start watching for Omarchy theme changes (inotify-based)
        self._start_theme_watcher()
        
        # Start periodic status panel refresh (every 1 second when focused)
        self.set_interval(1.0, self._periodic_status_refresh)
        
        # Focus the theme selection panel for keyboard navigation
        gradient_panel = self.query_one("#theme-selection-panel", ThemeSelectionPanel)
        gradient_panel.focus()

    def _reload_tui_theme(self) -> None:
        """Reload theme colors and CSS so TUI updates without restart."""
        try:
            # Reload color palette from disk and update THEME in-place so existing imports see changes.
            new_theme = theme_module.load_theme()
            theme_module.THEME.clear()
            theme_module.THEME.update(new_theme)

            # Regenerate CSS with the updated theme and reload it into the running app.
            new_css = styles_module.get_css()
            self.stylesheet.read(new_css)
            
            # Explicitly refresh border widgets so horizontal and vertical borders
            # pick up the new box_outline color immediately.
            for border in self.query(BorderTop):
                border.refresh()
            for border in self.query(BorderMiddle):
                border.refresh()
            for border in self.query(ControlFooterBorder):
                border.refresh()

            # Also do a general refresh to repaint the rest of the UI.
            self.refresh()
            print("[TUI] Reloaded TUI theme and CSS", file=sys.stderr)
        except Exception as e:
            print(f"[TUI] Failed to reload TUI theme: {e}", file=sys.stderr)
            traceback.print_exc()
    
    def _periodic_status_refresh(self) -> None:
        """Refresh status panel periodically"""
        status_panel = self.query_one("#status-panel", StatusPanel)
        status_panel.refresh()
    
    def _refresh_daemon_status(self) -> None:
        """Refresh only daemon status (polling - can't use inotify for process check)"""
        try:
            result = subprocess.run(["pgrep", "-x", "forgeworklights"], capture_output=True)
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
            result = subprocess.run(["pgrep", "-x", "forgeworklights"], capture_output=True)
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
        
        # Update panels - reactive watchers will trigger refresh automatically
        print(f"[TUI] ===== UPDATING STATUS PANEL =====", file=sys.stderr)
        print(f"[TUI] Daemon: {daemon_status}", file=sys.stderr)
        print(f"[TUI] Theme: {theme}", file=sys.stderr)
        print(f"[TUI] Brightness: {brightness_pct}%", file=sys.stderr)
        
        status_panel = self.query_one("#status-panel", StatusPanel)
        status_panel.daemon_status = daemon_status
        status_panel.current_theme = theme  # Changed to match theme selection panel
        status_panel.brightness_value = brightness_pct
        
        gradient_panel = self.query_one("#theme-selection-panel", ThemeSelectionPanel)
        gradient_panel.current_theme = theme
        
        # Only update brightness display if not currently being adjusted by user
        panel = self.query_one("#brightness-panel", BrightnessPanel)
        if not hasattr(self, '_brightness_adjusting') or not self._brightness_adjusting:
            panel.brightness = brightness_pct
    
    
    def on_control_footer_border_control_clicked(self, message: ControlFooterBorder.ControlClicked) -> None:
        """Handle footer control clicks"""
        if message.action_id == "quit":
            self.exit()
    
    
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
    
    def on_theme_selection_panel_theme_selected(self, message: ThemeSelectionPanel.ThemeSelected) -> None:
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
            
            # Update the theme selection panel display to show new arrow position
            gradient_panel = self.query_one("#theme-selection-panel", ThemeSelectionPanel)
            gradient_panel._update_display()

            # Theme change will trigger daemon reload via inotify for LEDs.

            # Also reload TUI theme/CSS so colors update immediately.
            self._reload_tui_theme()

            # Force immediate refresh of status after a short delay
            self.set_timer(0.5, self.refresh_status)
            
        except Exception as e:
            print(f"Failed to apply theme: {e}", file=sys.stderr)
            traceback.print_exc()
    
    
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
        # Refresh the theme selection panel to show the new theme
        gradient_panel = self.query_one("#theme-selection-panel", ThemeSelectionPanel)
        gradient_panel._theme_list = []  # Reset list to force reload
        gradient_panel._update_display()
        
        # Theme change will trigger daemon to reload animation colors via inotify
    
    def on_theme_selection_panel_theme_edit_requested(self, message: ThemeSelectionPanel.ThemeEditRequested) -> None:
        """Handle theme edit request from gradient panel"""
        print(f"Edit requested for theme: {message.theme_key}", file=sys.stderr)
        # Load the theme into the theme creator
        theme_creator = self.query_one("#theme-creator", ThemeCreator)
        theme_creator.load_theme_for_editing(message.theme_key, message.theme_name, message.colors)
    
    def on_theme_selection_panel_theme_delete_requested(self, message: ThemeSelectionPanel.ThemeDeleteRequested) -> None:
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
                
                # Refresh the theme selection panel to update the list
                gradient_panel = self.query_one("#theme-selection-panel", ThemeSelectionPanel)
                gradient_panel._theme_list = []
                gradient_panel._update_display()
                self.refresh_status()
            else:
                print(f"Theme not found in database: {message.theme_key}", file=sys.stderr)
        except Exception as e:
            print(f"Error deleting theme: {e}", file=sys.stderr)
            traceback.print_exc()
    
    def on_theme_selection_panel_theme_sync_requested(self, message: ThemeSelectionPanel.ThemeSyncRequested) -> None:
        """Handle theme sync request from gradient panel"""
        print("\n=== Theme sync requested ===", file=sys.stderr)
        
        try:
            # Import and run sync_themes from local tui package
            from .sync_themes import sync_themes

            changes = sync_themes(verbose=True)
            print(f"Sync completed: {changes} themes added/updated", file=sys.stderr)
            
            # Refresh the theme selection panel to show new themes
            print("Refreshing theme list...", file=sys.stderr)
            gradient_panel = self.query_one("#theme-selection-panel", ThemeSelectionPanel)
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
                self.omarchy_wd = os.inotify_add_watch(
                    self.inotify_fd,
                    str(omarchy_dir),
                    os.IN_ATTRIB | os.IN_CLOSE_WRITE | os.IN_MOVE_SELF | os.IN_DELETE_SELF | 
                    os.IN_CREATE | os.IN_DELETE | os.IN_MOVED_TO | os.IN_MOVED_FROM
                )
                print(f"Started inotify watcher on {omarchy_dir} (wd={self.omarchy_wd})", file=sys.stderr)

            # Watch Aether theme directory directly so we can detect palette changes
            if AETHER_THEME_DIR.exists() and AETHER_THEME_DIR.is_dir():
                self.aether_wd = os.inotify_add_watch(
                    self.inotify_fd,
                    str(AETHER_THEME_DIR),
                    os.IN_ATTRIB | os.IN_CLOSE_WRITE | os.IN_MOVE_SELF | os.IN_DELETE_SELF |
                    os.IN_CREATE | os.IN_DELETE | os.IN_MOVED_TO | os.IN_MOVED_FROM,
                )
                print(f"Started inotify watcher on {AETHER_THEME_DIR} (wd={self.aether_wd})", file=sys.stderr)
            
            # Watch omarchy-argb config directory
            config_dir = LED_THEME_FILE.parent
            if config_dir.exists():
                config_dir.mkdir(parents=True, exist_ok=True)
                self.config_wd = os.inotify_add_watch(
                    self.inotify_fd,
                    str(config_dir),
                    os.IN_ATTRIB | os.IN_CLOSE_WRITE | os.IN_MOVE_SELF | os.IN_DELETE_SELF | 
                    os.IN_CREATE | os.IN_DELETE | os.IN_MOVED_TO | os.IN_MOVED_FROM
                )
                print(f"Started inotify watcher on {config_dir} (wd={self.config_wd})", file=sys.stderr)
            
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
                    print(f"inotify event: wd={wd}, name='{name}', mask={mask}", file=sys.stderr)
                    
                    # Handle different file changes based on watch descriptor
                    if wd == self.omarchy_wd:
                        # Event from Omarchy theme directory - check for any event
                        # The handler will verify if theme actually changed
                        print(f"Event in Omarchy directory: '{name}' - checking for theme change", file=sys.stderr)
                        self.call_from_thread(self._on_omarchy_theme_changed)
                    elif wd == self.aether_wd:
                        # Event from the Aether theme directory - resync themes so Aether entry updates
                        print(f"Event in Aether theme directory: '{name}' - syncing Aether theme", file=sys.stderr)
                        self.call_from_thread(self._on_aether_theme_changed)
                    elif wd == self.config_wd:
                        # Event from config directory
                        if name == LED_THEME_FILE.name:
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

    def _on_aether_theme_changed(self):
        """Handle changes inside the Aether theme directory.

        When the Aether Omarchy theme changes on disk (e.g. its btop.theme
        is edited), resync themes so the Aether entry in themes.json stays
        in sync. The sync logic is responsible for updating just that
        theme's data.
        """
        try:
            print("[TUI] _on_aether_theme_changed() called", file=sys.stderr)

            # Small delay to allow file writes to complete
            time.sleep(0.1)

            from .sync_themes import sync_themes

            changes = sync_themes(verbose=True)
            print(f"[TUI] Aether theme sync completed, {changes} themes added/updated", file=sys.stderr)

            # themes.json rewrite will trigger _on_themes_db_changed via inotify,
            # which refreshes the theme selection panel. We can still refresh the
            # status view to keep everything consistent.
            self.refresh_status()

        except Exception as e:
            print(f"[TUI] Error handling Aether theme change: {e}", file=sys.stderr)
            traceback.print_exc()

    
    def _on_omarchy_theme_changed(self):
        """Handle Omarchy theme change event (from inotify)"""
        try:
            print(f"[TUI] _on_omarchy_theme_changed() called", file=sys.stderr)
            
            # Small delay to ensure filesystem has settled
            import time
            time.sleep(0.1)
            
            # Get new theme FIRST before checking anything
            # Force re-read by not using cached resolution
            if THEME_SYMLINK.exists() and THEME_SYMLINK.is_symlink():
                current_theme_dir = THEME_SYMLINK.resolve(strict=False)
                current_theme = current_theme_dir.name
                print(f"[TUI] Current theme resolved: {current_theme}", file=sys.stderr)
            else:
                print(f"[TUI] Theme symlink does not exist or is not a symlink", file=sys.stderr)
                # Still refresh in case it was deleted
                self.refresh_status()
                return
            
            print(f"[TUI] Omarchy theme changed: {self.last_omarchy_theme} -> {current_theme}", file=sys.stderr)
            self.last_omarchy_theme = current_theme
            
            # Daemon will detect theme change via inotify and reload colors automatically.

            # Reload TUI theme/CSS so the interface matches the new Omarchy theme.
            self._reload_tui_theme()

            # Refresh status to update both status panel and gradient panel
            print(f"[TUI] Calling refresh_status() after theme change", file=sys.stderr)
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
            # Refresh theme selection panel to show new/updated themes
            gradient_panel = self.query_one("#theme-selection-panel", ThemeSelectionPanel)
            gradient_panel._theme_list = []
            gradient_panel._update_display()
            
            # Theme update will trigger daemon to reload animation colors via inotify.

            # Also reload TUI theme/CSS in case the current theme's palette changed.
            self._reload_tui_theme()
        
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
