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

#content-area {
    width: 100%;
    height: auto;
    overflow-y: auto;
    scrollbar-size: 1 1;
}

StatusPanel, BorderTop, BorderMiddle, CollapsibleBorderMiddle, Spacer {
    width: 100%;
    height: auto;
}

#animations-end-spacer {
    height: 1fr;
    border-left: solid cyan;
    border-right: solid cyan;
}

BrightnessPanel {
    width: 100%;
    height: 1;
}

#bottom-section {
    width: 100%;
    height: auto;
    dock: bottom;
    background: #1e1e2e;
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
    height: auto;
    padding: 0 1;
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
    min-width: 48;
    height: auto;
    layout: vertical;
}

ThemeCreator .compact-row {
    width: 100%;
    height: auto;
    layout: horizontal;
    align: center middle;
    margin: 0;
    padding: 0;
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
    height: 2;
    content-align: center middle;
    margin: 0;
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
    margin: 0;
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
    height: 14;
    max-height: 14;
    padding: 0;
    margin: 0 0 0 1;
    background: #181825;
    border: solid #45475a;
    overflow: hidden;
}

ThemeCreator ColorSelector:focus {
    border: solid #89b4fa;
}

ThemeCreator ColorSelector Horizontal {
    height: 14;
    max-height: 14;
    overflow: hidden;
    layout: horizontal;
}

ThemeCreator ColorSelector #color-grid {
    width: auto;
    height: 12;
    max-height: 12;
    margin: 0;
    overflow: hidden;
}

ThemeCreator ColorSelector #color-info {
    width: auto;
    min-width: 10;
    height: 14;
    padding: 0 1;
    text-align: left;
    color: #cdd6f4;
    overflow: hidden;
}

/* Animations Panel Styling */
AnimationsPanel {
    width: 100%;
    height: auto;
    padding: 1 1;
    margin: 0;
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
    layout: horizontal;
}

AnimationsPanel #animations-left {
    width: 50%;
    height: auto;
}

AnimationsPanel #animations-left:focus-within {
    border-right: solid cyan;
}

AnimationsPanel #animations-right {
    width: 50%;
    height: auto;
    padding-left: 1;
}

AnimationsPanel #animations-list {
    width: 100%;
    height: auto;
}

ParameterSlider {
    width: 100%;
    height: 1;
    margin-bottom: 0;
}

ParameterSlider:focus {
    background: #313244;
}
"""
