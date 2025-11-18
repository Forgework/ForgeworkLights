"""
Border widgets for ForgeworkLights TUI
"""
from textual.widgets import Static
from textual.message import Message


class BorderTop(Static):
    """Top border with title"""
    def __init__(self, title: str = ""):
        super().__init__()
        self.border_title = title
    
    def render(self) -> str:
        width = max(60, self.size.width if self.size.width > 0 else 70)
        title = f" {self.border_title} "
        left_pad = 2
        right_pad = max(0, width - len(title) - left_pad - 4)
        return f"[cyan]╭{'─' * left_pad}┤{title}├{'─' * right_pad}╮[/]"


class BorderMiddle(Static):
    """Middle border separator with optional label"""
    def __init__(self, border_title: str = "", **kwargs):
        super().__init__(**kwargs)
        self.border_title = border_title
    
    def render(self) -> str:
        width = max(60, self.size.width if self.size.width > 0 else 70)
        if self.border_title:
            # Render with label like BorderTop
            title = f" {self.border_title} "
            left_pad = 2
            right_pad = max(0, width - len(title) - left_pad - 4)
            return f"[cyan]├{'─' * left_pad}┤{title}├{'─' * right_pad}┤[/]"
        else:
            # Render plain border
            return f"[cyan]├{'─' * (width - 2)}┤[/]"


class Spacer(Static):
    """Empty line with borders for vertical spacing"""
    def render(self) -> str:
        width = max(60, self.size.width if self.size.width > 0 else 70)
        return f"[cyan]│{' ' * (width - 2)}│[/]"


class Filler(Static):
    """Empty area with borders that fills remaining vertical space"""
    def render(self) -> str:
        width = max(60, self.size.width if self.size.width > 0 else 70)
        height = self.size.height if self.size.height > 0 else 10
        
        lines = []
        for _ in range(height):
            lines.append(f"[cyan]│{' ' * (width - 2)}│[/]")
        
        return "\n".join(lines)


class ControlFooterBorder(Static):
    """Bottom border with embedded clickable controls"""
    
    class ControlClicked(Message):
        """Message when a control is clicked"""
        def __init__(self, action_id: str):
            super().__init__()
            self.action_id = action_id
    
    BINDINGS = [
        ("left", "select_previous", "Previous control"),
        ("right", "select_next", "Next control"),
        ("enter", "activate", "Activate control"),
    ]
    
    def __init__(self):
        super().__init__()
        self.hovered_item = None
        self.focused_index = 0
        self.controls = ["quit", "bright_down", "bright_up", "logs"]
        self.can_focus = True
    
    def render(self) -> str:
        width = max(60, self.size.width if self.size.width > 0 else 70)
        
        # Determine focused control when widget has focus
        focused_control = None
        if self.has_focus:
            focused_control = self.controls[self.focused_index]
        
        # Define controls with hover/focus effects
        quit = "[Ctrl+Q] Quit"
        if self.hovered_item == "quit" or focused_control == "quit":
            quit = "[bold yellow][Ctrl+Q] Quit[/]"
        
        down = "💡↓"
        if self.hovered_item == "bright_down" or focused_control == "bright_down":
            down = "[bold yellow]💡↓[/]"
        
        up = "💡↑"
        if self.hovered_item == "bright_up" or focused_control == "bright_up":
            up = "[bold yellow]💡↑[/]"
        
        logs = "[L] Logs"
        if self.hovered_item == "logs" or focused_control == "logs":
            logs = "[bold yellow][L] Logs[/]"
        
        controls = f" {quit}  {down}  {up}  {logs} "
        
        # Calculate exact visible width:
        # space(1) + [Ctrl+Q] Quit(13) + spaces(2) + 💡↓(2) + spaces(2) + 💡↑(2) + spaces(2) + [L] Logs(8) + space(1)
        # Total visible: 1 + 13 + 2 + 2 + 2 + 2 + 2 + 8 + 1 = 33
        
        # Total: ╰(1) + left_pad + ┤(1) + space(1) + [Ctrl+Q] Quit(13) + spaces(2) + 💡↓(2) + spaces(2) + 💡↑(2) + spaces(2) + [L] Logs(8) + space(1) + ├(1) + ─(1) + ╯(1)
        # = 1 + left_pad + 1 + 1 + 13 + 2 + 2 + 2 + 2 + 2 + 8 + 1 + 1 + 1 + 1 = left_pad + 38 = width
        left_pad = max(1, width - 37)
        
        return f"[cyan]╰{'─' * left_pad}┤{controls}├─╯[/]"
    
    def on_click(self, event) -> None:
        x = event.x
        width = self.size.width if self.size.width > 0 else 70
        
        # Calculate control positions from the left edge
        # Layout: ╰───...───┤ [Ctrl+Q] Quit  💡↓  💡↑  [L] Logs ├─╯
        #         0         left_pad+1 (┤) +2 (space) +3 (start of text)
        
        left_pad = max(1, width - 37)
        # Position after: ╰ (1) + dashes (left_pad) + ┤ (1) + space (1)
        controls_start = left_pad + 3
        
        # [Ctrl+Q] Quit = 13 chars
        quit_start = controls_start
        quit_end = quit_start + 13
        
        # 2 spaces, then 💡↓ = 2 display chars (but emoji is 1 column in most terminals)
        down_start = quit_end + 2
        down_end = down_start + 2
        
        # 2 spaces, then 💡↑ = 2 display chars
        up_start = down_end + 2
        up_end = up_start + 2
        
        # 2 spaces, then [L] Logs = 8 chars
        logs_start = up_end + 2
        logs_end = logs_start + 8
        
        if quit_start <= x < quit_end:
            self.post_message(self.ControlClicked("quit"))
        elif down_start <= x < down_end:
            self.post_message(self.ControlClicked("bright_down"))
        elif up_start <= x < up_end:
            self.post_message(self.ControlClicked("bright_up"))
        elif logs_start <= x < logs_end:
            self.post_message(self.ControlClicked("logs"))
    
    def on_mouse_move(self, event) -> None:
        x = event.x
        width = self.size.width if self.size.width > 0 else 70
        
        # Use same position calculation as click
        left_pad = max(1, width - 37)
        controls_start = left_pad + 3
        
        quit_start = controls_start
        quit_end = quit_start + 13
        down_start = quit_end + 2
        down_end = down_start + 2
        up_start = down_end + 2
        up_end = up_start + 2
        logs_start = up_end + 2
        logs_end = logs_start + 8
        
        old = self.hovered_item
        if quit_start <= x < quit_end:
            self.hovered_item = "quit"
        elif down_start <= x < down_end:
            self.hovered_item = "bright_down"
        elif up_start <= x < up_end:
            self.hovered_item = "bright_up"
        elif logs_start <= x < logs_end:
            self.hovered_item = "logs"
        else:
            self.hovered_item = None
        
        if old != self.hovered_item:
            self.refresh()
    
    def on_leave(self) -> None:
        self.hovered_item = None
        self.refresh()
    
    def action_select_previous(self) -> None:
        """Select previous control"""
        self.focused_index = (self.focused_index - 1) % len(self.controls)
        self.refresh()
    
    def action_select_next(self) -> None:
        """Select next control"""
        self.focused_index = (self.focused_index + 1) % len(self.controls)
        self.refresh()
    
    def action_activate(self) -> None:
        """Activate the focused control"""
        focused_control = self.controls[self.focused_index]
        self.post_message(self.ControlClicked(focused_control))
    
    def on_focus(self) -> None:
        """Refresh when gaining focus"""
        self.refresh()
    
    def on_blur(self) -> None:
        """Refresh when losing focus"""
        self.refresh()
