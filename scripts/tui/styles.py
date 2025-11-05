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

ThemeCreator #theme-creator-main {
    width: 100%;
    height: auto;
    layout: horizontal;
    align: left top;
}

ThemeCreator #theme-controls {
    width: 55%;
    min-width: 50;
    height: auto;
    layout: vertical;
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
    width: 100%;
    text-align: center;
    padding: 0 1;
}

ThemeCreator Horizontal#button-row {
    height: 1;
    align: center middle;
}

ThemeButton {
    color: #a6e3a1;
    width: auto;
    height: 1;
    padding: 0 1;
    margin: 0 1;
    text-align: center;
}

ThemeButton:focus {
    color: #f9e2af;
    text-style: bold;
}

ThemeButton.selected {
    color: #f9e2af;
    text-style: bold;
}

ThemeCreator Input.selected {
    border: tall #f9e2af;
}

/* Color Selector Styling */
ThemeCreator ColorSelector {
    width: 45%;
    height: auto;
    padding: 1;
    margin: 0 0 0 1;
    background: #181825;
    border: solid #45475a;
    display: none;
}

ThemeCreator ColorSelector:focus {
    border: solid #89b4fa;
}

ThemeCreator ColorSelector #color-grid {
    width: 100%;
    height: auto;
    margin: 0 0 1 0;
}

ThemeCreator ColorSelector #color-info {
    width: 100%;
    height: auto;
    text-align: center;
    color: #cdd6f4;
}

/* Animations Panel Styling */
AnimationsPanel {
    width: 100%;
    height: auto;
    max-height: 15;
    padding: 1 2;
    scrollbar-size: 0 0;
    overflow-y: auto;
    border-left: solid cyan;
    border-right: solid cyan;
    border-bottom: none;
    border-top: none;
}

AnimationsPanel:focus {
    border-left: solid cyan;
    border-right: solid cyan;
}

AnimationsPanel #animations-content {
    width: 100%;
    height: auto;
}

AnimationsPanel #animations-list {
    width: 100%;
    height: auto;
}
"""
