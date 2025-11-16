"""
CSS styles for ForgeworkLights TUI
"""
from .theme import THEME

def get_css() -> str:
    """Generate CSS with theme colors"""
    return f"""
Screen {{
    background: {THEME['main_bg']};
}}

#main-panel {{
    width: 100%;
    height: 100vh;
    min-width: 60;
    background: {THEME['main_bg']};
    layout: vertical;
}}

#content-area {{
    width: 100%;
    height: auto;
    overflow-y: auto;
    scrollbar-size: 1 1;
}}

StatusPanel, BorderTop, BorderMiddle, CollapsibleBorderMiddle, Spacer {{
    width: 100%;
    height: auto;
}}

#animations-end-spacer {{
    height: 1fr;
    border-left: solid {THEME['box_outline']};
    border-right: solid {THEME['box_outline']};
}}

BrightnessPanel {{
    width: 100%;
    height: 1;
}}

#bottom-section {{
    width: 100%;
    height: auto;
    dock: bottom;
    background: {THEME['main_bg']};
}}

Filler {{
    width: 100%;
    height: 1fr;
}}

GradientPanel {{
    width: 100%;
    height: auto;
    max-height: 20;
    scrollbar-size: 0 0;
    overflow-y: auto;
    border: none;
}}

GradientPanel:focus {{
    border: none;
}}

ControlFooterBorder {{
    width: 100%;
    height: auto;
    border: none;
}}

ControlFooterBorder:focus {{
    border: none;
}}

#gradient-content {{
    width: 100%;
    height: auto;
}}

#logs-modal {{
    align: center middle;
}}

#logs-panel {{
    width: 90%;
    max-width: 120;
    height: 80%;
    max-height: 40;
    background: {THEME['main_bg']};
}}

#logs-content {{
    width: 100%;
    height: 100%;
    scrollbar-size: 0 0;
}}

#logs-text {{
    width: 100%;
    height: auto;
}}

ThemeCreator {{
    width: 100%;
    height: auto;
    padding: 0 1;
    border-left: solid {THEME['box_outline']};
    border-right: solid {THEME['box_outline']};
}}

ThemeCreator #theme-creator-main {{
    width: 100%;
    height: auto;
    layout: horizontal;
    align: left top;
}}

ThemeCreator #theme-controls {{
    width: 55%;
    min-width: 48;
    height: auto;
    layout: vertical;
}}

ThemeCreator .compact-row {{
    width: 100%;
    height: auto;
    layout: horizontal;
    align: center middle;
    margin: 0;
    padding: 0;
}}

ThemeCreator .name-input {{
    width: 1fr;
    border: solid {THEME['div_line']};
    margin-right: 1;
}}

ThemeCreator .color-input {{
    width: 14;
    border: solid {THEME['div_line']};
    margin-right: 1;
}}

ThemeCreator .color-input:last-child {{
    margin-right: 0;
}}

ThemeCreator Input:focus {{
    border: solid {THEME['hi_fg']};
}}

ThemeCreator .preview-centered {{
    width: 100%;
    height: 2;
    content-align: center middle;
    margin: 0;
}}

ThemeCreator .button-inline {{
    color: {THEME['button_fg']};
    width: 100%;
    text-align: center;
    padding: 0 1;
}}

ThemeCreator Horizontal#button-row {{
    height: 1;
    align: center middle;
}}

ThemeButton {{
    color: {THEME['button_fg']};
    width: auto;
    height: 1;
    padding: 0 1;
    margin: 0;
    text-align: center;
}}

ThemeButton:focus {{
    color: {THEME['hi_fg']};
    text-style: bold;
}}

ThemeButton.selected {{
    color: {THEME['hi_fg']};
    text-style: bold;
}}

ThemeCreator Input.selected {{
    border: tall {THEME['hi_fg']};
}}

/* Color Selector Styling */
ThemeCreator ColorSelector {{
    width: 45%;
    height: 14;
    max-height: 14;
    padding: 0;
    margin: 0 0 0 1;
    background: {THEME['secondary_bg']};
    border: solid {THEME['div_line']};
    overflow: hidden;
}}

ThemeCreator ColorSelector:focus {{
    border: solid {THEME['hi_fg']};
}}

ThemeCreator ColorSelector Horizontal {{
    height: 14;
    max-height: 14;
    overflow: hidden;
    layout: horizontal;
}}

ThemeCreator ColorSelector #color-grid {{
    width: auto;
    height: 12;
    max-height: 12;
    margin: 0;
    overflow: hidden;
}}

ThemeCreator ColorSelector #color-info {{
    width: auto;
    min-width: 10;
    height: 14;
    padding: 0 1;
    text-align: left;
    color: {THEME['main_fg']};
    overflow: hidden;
}}

/* Animations Panel Styling */
AnimationsPanel {{
    width: 100%;
    height: auto;
    padding: 1 1;
    margin: 0;
    border-left: solid {THEME['box_outline']};
    border-right: solid {THEME['box_outline']};
    border-bottom: none;
    border-top: none;
}}

AnimationsPanel:focus {{
    border-left: solid {THEME['box_outline']};
    border-right: solid {THEME['box_outline']};
}}

AnimationsPanel #animations-content {{
    width: 100%;
    height: auto;
    layout: horizontal;
}}

AnimationsPanel #animations-left {{
    width: 50%;
    height: auto;
}}

AnimationsPanel #animations-left:focus-within {{
    border-right: solid {THEME['box_outline']};
}}

AnimationsPanel #animations-right {{
    width: 50%;
    height: auto;
    padding-left: 1;
}}

AnimationsPanel #animations-list {{
    width: 100%;
    height: auto;
}}

ParameterSlider {{
    width: 100%;
    height: 1;
    margin-bottom: 0;
}}

ParameterSlider:focus {{
    background: {THEME['hover_bg']};
}}
"""

# For backward compatibility, keep CSS as a module-level variable
CSS = get_css()
