"""
Theme button widget used by the theme creator and color selector.
"""
from textual.widgets import Static
from textual.message import Message

from ..theme import THEME


class ThemeButton(Static):
    """Individual clickable button widget"""
    
    class ButtonClicked(Message):
        def __init__(self, button_id: str):
            super().__init__()
            self.button_id = button_id
    
    def __init__(self, label: str, button_id: str, shortcut: str, **kwargs):
        super().__init__(**kwargs)
        self.label = label
        self.button_id = button_id
        self.shortcut = shortcut
        self.can_focus = True  # Allow focus so buttons can be tabbable
    
    def render(self) -> str:
        text = f"[{self.shortcut}] {self.label}"
        if self.has_focus:
            text = f"[bold {THEME['hi_fg']}]{text}[/]"
        return text
    
    def on_click(self, event) -> None:
        self.post_message(self.ButtonClicked(self.button_id))
    
    def on_key(self, event) -> None:
        if event.key == "enter":
            self.post_message(self.ButtonClicked(self.button_id))
