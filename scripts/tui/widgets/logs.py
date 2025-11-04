"""
Logs modal widget for ForgeworkLights TUI
"""
import subprocess
import threading
from textual.screen import ModalScreen
from textual.containers import Container, ScrollableContainer
from textual.widgets import Static
from textual.app import ComposeResult
from textual.timer import Timer


class LogsContent(ScrollableContainer):
    """Scrollable logs content"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._text_widget = Static("Loading logs...", id="logs-text")
    
    def compose(self) -> ComposeResult:
        yield self._text_widget
    
    def set_logs(self, logs: str) -> None:
        """Update log content"""
        self._text_widget.update(logs)


class LogsModal(ModalScreen):
    """Modal screen for viewing daemon logs"""
    
    BINDINGS = [
        ("escape", "dismiss", "Close"),
        ("q", "dismiss", "Close"),
    ]
    
    def __init__(self):
        super().__init__()
        self._loading = True
        self._refresh_timer: Timer | None = None
    
    def compose(self) -> ComposeResult:
        with Container(id="logs-modal"):
            with Container(id="logs-panel"):
                yield Static("[cyan]╭┤ Daemon Logs - ESC/Q Close ├─╮[/]", id="logs-header")
                yield LogsContent(id="logs-content")
                yield Static("[cyan]╰─────────────────────────────╯[/]", id="logs-footer")
    
    def on_mount(self) -> None:
        """Start log fetching and auto-refresh"""
        self._loading = True
        self._fetch_logs()
        # Auto-refresh every 2 seconds
        self._refresh_timer = self.set_interval(2.0, self._fetch_logs)
    
    def _fetch_logs(self) -> None:
        """Fetch logs in background thread"""
        if not self._loading and hasattr(self, '_refresh_timer') and not self._refresh_timer:
            return
        
        def get_logs():
            try:
                result = subprocess.run(
                    ["journalctl", "--user", "-u", "omarchy-argb", "-n", "100", "--no-pager"],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                if result.returncode == 0:
                    logs = result.stdout.strip() or "No logs available"
                else:
                    logs = f"Error fetching logs: {result.stderr}"
            except subprocess.TimeoutExpired:
                logs = "Error: Log fetch timed out"
            except Exception as e:
                logs = f"Error: {e}"
            
            # Update UI on main thread
            self.app.call_from_thread(self._update_logs, logs)
        
        # Run in background thread
        thread = threading.Thread(target=get_logs, daemon=True)
        thread.start()
    
    def _update_logs(self, logs: str) -> None:
        """Update logs display (called from main thread)"""
        try:
            content = self.query_one("#logs-content", LogsContent)
            content.set_logs(logs)
            # Auto-scroll to bottom to show latest logs
            content.scroll_end(animate=False)
        except Exception as e:
            pass  # Modal might have been closed
    
    def action_dismiss(self) -> None:
        """Close the modal"""
        self._loading = False  # Stop any pending updates
        if self._refresh_timer:
            self._refresh_timer.stop()
        self.dismiss()
