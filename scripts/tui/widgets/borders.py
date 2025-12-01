"""
Border widgets for ForgeworkLights TUI
"""
from textual.widgets import Static
from textual.message import Message
from ..theme import THEME


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
        border_color = THEME["box_outline"]
        return f"[{border_color}]╭{'─' * left_pad}┤{title}├{'─' * right_pad}╮[/]"


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
            border_color = THEME["box_outline"]
            return f"[{border_color}]├{'─' * left_pad}┤{title}├{'─' * right_pad}┤[/]"
        else:
            # Render plain border
            border_color = THEME["box_outline"]
            return f"[{border_color}]├{'─' * (width - 2)}┤[/]"


class Spacer(Static):
    """Empty line with borders for vertical spacing"""
    def render(self) -> str:
        width = max(60, self.size.width if self.size.width > 0 else 70)
        border_color = THEME["box_outline"]
        return f"[{border_color}]│{' ' * (width - 2)}│[/]"


class Filler(Static):
    """Empty area with borders that fills remaining vertical space"""
    def render(self) -> str:
        width = max(60, self.size.width if self.size.width > 0 else 70)
        height = self.size.height if self.size.height > 0 else 10
        
        border_color = THEME["box_outline"]

        lines = []
        for _ in range(height):
            lines.append(f"[{border_color}]│{' ' * (width - 2)}│[/]")
        
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
        self.controls = ["quit"]
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
        
        controls = f" {quit} "
        
        # Calculate exact visible width:
        # space(1) + [Ctrl+Q] Quit(13) + space(1) = 15
        
        # Total: ╰(1) + left_pad + ┤(1) + controls(15) + ├(1) + ─(1) + ╯(1)
        # = left_pad + 20 = width
        left_pad = max(1, width - 20)

        border_color = THEME["box_outline"]
        return f"[{border_color}]╰{'─' * left_pad}┤{controls}├─╯[/]"
    
    def on_click(self, event) -> None:
        x = event.x
        width = self.size.width if self.size.width > 0 else 70
        
        # Calculate control positions from the left edge
        # Layout: ╰───...───┤ [Ctrl+Q] Quit ├─╯
        
        left_pad = max(1, width - 20)
        # Position after: ╰ (1) + dashes (left_pad) + ┤ (1) + space (1)
        controls_start = left_pad + 3
        
        # [Ctrl+Q] Quit = 13 chars
        quit_start = controls_start
        quit_end = quit_start + 13
        
        if quit_start <= x < quit_end:
            self.post_message(self.ControlClicked("quit"))
    
    def on_mouse_move(self, event) -> None:
        x = event.x
        width = self.size.width if self.size.width > 0 else 70
        
        # Use same position calculation as click
        left_pad = max(1, width - 20)
        controls_start = left_pad + 3
        
        quit_start = controls_start
        quit_end = quit_start + 13
        
        old = self.hovered_item
        if quit_start <= x < quit_end:
            self.hovered_item = "quit"
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
