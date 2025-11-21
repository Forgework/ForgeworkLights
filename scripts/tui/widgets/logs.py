"""
Logs modal widget for ForgeworkLights TUI
"""
import subprocess
import sys
from textual.screen import ModalScreen
from textual.containers import Container, ScrollableContainer
from textual.widgets import Static
from textual.app import ComposeResult
from textual.worker import Worker, WorkerState

from ..constants import (
    DAEMON_SERVICE_NAME,
    LOGS_MAX_LINES,
    LOGS_INITIAL_LINES,
    LOGS_FETCH_TIMEOUT,
    LOGS_DEFAULT_WIDTH,
)
from ..theme import THEME


class LogsContent(ScrollableContainer):
    """Scrollable logs content"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.log_lines = []
    
    def compose(self) -> ComposeResult:
        yield Static("Loading logs...", id="logs-text")
    
    def append_log(self, log: str) -> None:
        """Append log line"""
        self.log_lines.extend(log.split("\n"))
        # Keep only last N lines to prevent memory issues
        if len(self.log_lines) > LOGS_MAX_LINES:
            self.log_lines = self.log_lines[-LOGS_MAX_LINES:]
        
        text_widget = self.query_one("#logs-text", Static)
        text_widget.update("\n".join(self.log_lines))


class LogsModal(ModalScreen):
    """Modal screen for viewing daemon logs"""
    
    BINDINGS = [
        ("escape", "dismiss", "Close"),
        ("q", "dismiss", "Close"),
        ("ctrl+c", "dismiss", "Close"),
    ]
    
    def __init__(self):
        super().__init__()
        self._is_mounted = False
        self._log_process = None
        self._stream_worker = None
    
    def compose(self) -> ComposeResult:
        with Container(id="logs-modal"):
            with Container(id="logs-panel"):
                yield Static("", id="logs-header")
                yield LogsContent(id="logs-content")
                yield Static("", id="logs-footer")
    
    def on_mount(self) -> None:
        """Start log streaming"""
        self._is_mounted = True
        # Update borders to match terminal width
        self._update_borders()
        # Get initial logs first
        self._stream_worker = self.run_worker(self._stream_logs, thread=True, group="logs", exclusive=True)
    
    def _update_borders(self) -> None:
        """Update header and footer borders to match terminal width"""
        try:
            header = self.query_one("#logs-header", Static)
            footer = self.query_one("#logs-footer", Static)
            
            # Get terminal width
            width = self.app.size.width if self.app.size.width > 0 else LOGS_DEFAULT_WIDTH
            
            # Create header with title and controls
            title = f" 📋 {DAEMON_SERVICE_NAME} Logs (Live Stream) "
            controls = " [ESC] Close | [Q] Quit | [Ctrl+C] Exit "
            
            # Calculate padding
            title_pad_left = 2
            controls_len = len(controls)
            remaining = max(0, width - len(title) - title_pad_left - controls_len - 6)  # 6 for borders
            
            header_line = f"[{THEME['box_outline']}]╭{'─' * title_pad_left}┤{title}├{'─' * remaining}┤{controls}├╮[/]"
            header.update(header_line)
            
            # Create footer
            footer_line = f"[{THEME['box_outline']}]╰{'─' * (width - 2)}╯[/]"
            footer.update(footer_line)
        except Exception:
            pass
    
    def _stream_logs(self) -> None:
        """Stream logs continuously (runs in worker thread)"""
        try:
            # First, get recent logs
            print("[LOGS] Fetching initial logs...", file=sys.stderr)
            initial = subprocess.run(
                ["journalctl", "--user", "-u", DAEMON_SERVICE_NAME, "-n", str(LOGS_INITIAL_LINES), "--no-pager"],
                capture_output=True,
                text=True,
                timeout=LOGS_FETCH_TIMEOUT
            )
            if initial.returncode == 0 and initial.stdout:
                print(f"[LOGS] Got {len(initial.stdout)} chars of initial logs", file=sys.stderr)
                self.app.call_from_thread(self._append_logs, initial.stdout.strip())
            else:
                print(f"[LOGS] No initial logs: rc={initial.returncode}", file=sys.stderr)
                self.app.call_from_thread(self._append_logs, "Waiting for logs...")
            
            # Then start streaming new logs
            print("[LOGS] Starting log stream...", file=sys.stderr)
            self._log_process = subprocess.Popen(
                ["journalctl", "--user", "-u", DAEMON_SERVICE_NAME, "-f", "--no-pager"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1  # Line buffered
            )
            
            print("[LOGS] Stream process started, reading lines...", file=sys.stderr)
            # Read and stream logs line by line
            while self._is_mounted and self._log_process:
                try:
                    line = self._log_process.stdout.readline()
                    if not line:
                        print("[LOGS] No more lines, stream ended", file=sys.stderr)
                        break
                    if line.strip():
                        self.app.call_from_thread(self._append_logs, line.rstrip())
                except Exception as e:
                    print(f"[LOGS] Error reading line: {e}", file=sys.stderr)
                    break
                    
        except Exception as e:
            print(f"[LOGS] Stream error: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            self.app.call_from_thread(self._append_logs, f"Error streaming logs: {e}")
    
    def _append_logs(self, new_log: str) -> None:
        """Append new log lines (called from main thread)"""
        if not self._is_mounted:
            return
        
        try:
            content = self.query_one("#logs-content", LogsContent)
            content.append_log(new_log)
            # Auto-scroll to bottom to show latest logs
            content.scroll_end(animate=False)
        except Exception as e:
            # Don't let errors crash the modal
            print(f"Error appending logs: {e}", file=sys.stderr)
            pass
    
    def on_resize(self) -> None:
        """Update borders when terminal is resized"""
        self._update_borders()
    
    def action_dismiss(self) -> None:
        """Close the modal"""
        self._is_mounted = False  # Stop streaming
        
        # Kill the log process
        if self._log_process:
            try:
                self._log_process.terminate()
                self._log_process.wait(timeout=1)
            except:
                try:
                    self._log_process.kill()
                except:
                    pass
            self._log_process = None
        
        # Cancel any running workers
        if self._stream_worker:
            self._stream_worker.cancel()
        self.workers.cancel_group(self, "logs")
        
        self.dismiss()
