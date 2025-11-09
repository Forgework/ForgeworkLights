"""
Logs modal widget for ForgeworkLights TUI
"""
import subprocess
from textual.screen import ModalScreen
from textual.containers import Container, ScrollableContainer
from textual.widgets import Static
from textual.app import ComposeResult
from textual.timer import Timer
from textual.worker import Worker


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
        self._refresh_timer: Timer | None = None
        self._is_mounted = False
    
    def compose(self) -> ComposeResult:
        with Container(id="logs-modal"):
            with Container(id="logs-panel"):
                yield Static("[cyan]╭┤ Daemon Logs - ESC/Q Close ├─╮[/]", id="logs-header")
                yield LogsContent(id="logs-content")
                yield Static("[cyan]╰─────────────────────────────╯[/]", id="logs-footer")
    
    def on_mount(self) -> None:
        """Start log fetching and auto-refresh"""
        self._is_mounted = True
        self._fetch_logs()
        # Auto-refresh every 2 seconds
        self._refresh_timer = self.set_interval(2.0, self._fetch_logs)
    
    def _fetch_logs(self) -> None:
        """Fetch logs using worker"""
        if not self._is_mounted:
            return
        
        # Run fetch in worker
        self.run_worker(self._get_logs_worker, thread=True, group="logs")
    
    def _get_logs_worker(self) -> str:
        """Worker function to fetch logs (runs in thread)"""
        try:
            result = subprocess.run(
                ["journalctl", "--user", "-u", "omarchy-argb", "-n", "100", "--no-pager"],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0:
                return result.stdout.strip() or "No logs available"
            else:
                return f"Error fetching logs: {result.stderr}"
        except subprocess.TimeoutExpired:
            return "Error: Log fetch timed out"
        except Exception as e:
            return f"Error: {e}"
    
    def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        """Handle worker completion"""
        if event.worker.group == "logs" and event.worker.is_finished:
            if event.worker.result:
                self._update_logs(event.worker.result)
    
    def _update_logs(self, logs: str) -> None:
        """Update logs display (called from main thread)"""
        if not self._is_mounted:
            return
        
        try:
            content = self.query_one("#logs-content", LogsContent)
            content.set_logs(logs)
            # Auto-scroll to bottom to show latest logs
            content.scroll_end(animate=False)
        except Exception:
            pass  # Modal might have been closed
    
    def action_dismiss(self) -> None:
        """Close the modal"""
        self._is_mounted = False  # Stop any pending updates
        if self._refresh_timer:
            self._refresh_timer.stop()
            self._refresh_timer = None
        
        # Cancel any running workers
        self.workers.cancel_group(self, "logs")
        
        self.dismiss()
