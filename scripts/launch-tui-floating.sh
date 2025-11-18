#!/bin/bash
# Launch ForgeworkLights TUI in a floating window
# This script is meant to be called from Waybar
# Window sized to fit app with expanded theme creator (80 cols x 55 rows, ~734x1055 pixels)

# Detect terminal emulator
if command -v ghostty &> /dev/null; then
    # Note: Ghostty doesn't support setting dimensions directly, relies on Hyprland rules (734x1055 pixels)
    ghostty --class=forgework-lights-tui --title=ForgeworkLights -e /usr/local/bin/omarchy-argb-menu
elif command -v kitty &> /dev/null; then
    kitty --class="forgework-lights-tui" --title="ForgeworkLights" -o initial_window_width=80c -o initial_window_height=55c -e /usr/local/bin/omarchy-argb-menu
elif command -v alacritty &> /dev/null; then
    alacritty --class="forgework-lights-tui" --title="ForgeworkLights" -o window.dimensions.columns=80 -o window.dimensions.lines=55 -e /usr/local/bin/omarchy-argb-menu
elif command -v wezterm &> /dev/null; then
    wezterm start --class=forgework-lights-tui --title=ForgeworkLights /usr/local/bin/omarchy-argb-menu
elif command -v foot &> /dev/null; then
    foot --app-id="forgework-lights-tui" --title="ForgeworkLights" /usr/local/bin/omarchy-argb-menu
elif command -v konsole &> /dev/null; then
    konsole --class=forgework-lights-tui --title=ForgeworkLights -e /usr/local/bin/omarchy-argb-menu
elif command -v gnome-terminal &> /dev/null; then
    gnome-terminal --class=forgework-lights-tui --title=ForgeworkLights -- /usr/local/bin/omarchy-argb-menu
elif command -v terminator &> /dev/null; then
    terminator --classname=forgework-lights-tui --title=ForgeworkLights -x /usr/local/bin/omarchy-argb-menu
elif command -v xterm &> /dev/null; then
    xterm -class forgework-lights-tui -title ForgeworkLights -geometry 80x55 -e /usr/local/bin/omarchy-argb-menu
else
    # Fallback
    x-terminal-emulator -e /usr/local/bin/omarchy-argb-menu
fi
