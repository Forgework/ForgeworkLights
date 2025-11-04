"""
CSS styles for ForgeworkLights TUI
"""

CSS = """
Screen {
    background: #1e1e2e;
}

#main-panel {
    width: 100%;
    height: 100vh;
    min-width: 60;
    background: #1e1e2e;
    layout: vertical;
}

StatusPanel, BorderTop, BorderMiddle, Spacer {
    width: 100%;
    height: auto;
}

BrightnessPanel {
    width: 100%;
    height: 1;
}

Filler {
    width: 100%;
    height: 1fr;
}

GradientPanel {
    width: 100%;
    height: auto;
    max-height: 20;
    scrollbar-size: 0 0;
    overflow-y: auto;
    border: none;
}

GradientPanel:focus {
    border: none;
}

ControlFooterBorder {
    width: 100%;
    height: auto;
    dock: bottom;
    border: none;
}

ControlFooterBorder:focus {
    border: none;
}

#gradient-content {
    width: 100%;
    height: auto;
}

#logs-modal {
    align: center middle;
}

#logs-panel {
    width: 90%;
    max-width: 120;
    height: 80%;
    max-height: 40;
    background: #1e1e2e;
}

#logs-content {
    width: 100%;
    height: 100%;
    scrollbar-size: 0 0;
}

#logs-text {
    width: 100%;
    height: auto;
}

ThemeCreator {
    width: 100%;
    height: 1fr;
    padding: 1 2;
    border-left: solid cyan;
    border-right: solid cyan;
}

ThemeCreator .compact-row {
    width: 100%;
    height: auto;
    layout: horizontal;
    align: center middle;
    margin: 0 0 0 0;
}

ThemeCreator .name-input {
    width: 1fr;
    border: solid #45475a;
    margin-right: 1;
}

ThemeCreator .color-input {
    width: 14;
    border: solid #45475a;
    margin-right: 1;
}

ThemeCreator .color-input:last-child {
    margin-right: 0;
}

ThemeCreator Input:focus {
    border: solid #89b4fa;
}

ThemeCreator .preview-centered {
    width: 100%;
    height: 3;
    content-align: center middle;
}

ThemeCreator .button-inline {
    color: #a6e3a1;
    width: auto;
}
"""
