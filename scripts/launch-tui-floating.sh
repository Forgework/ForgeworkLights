#!/bin/bash
# Launch ForgeworkLights TUI in a floating window
# This script is meant to be called from Waybar
# Window size: 800x1000 (taller and skinnier)

# Detect terminal emulator
if command -v kitty &> /dev/null; then
    kitty --class="forgework-lights-tui" --title="ForgeworkLights" -o initial_window_width=800 -o initial_window_height=1000 -e /usr/local/bin/omarchy-argb-menu
elif command -v alacritty &> /dev/null; then
    alacritty --class="forgework-lights-tui" --title="ForgeworkLights" -o window.dimensions.columns=100 -o window.dimensions.lines=50 -e /usr/local/bin/omarchy-argb-menu
elif command -v foot &> /dev/null; then
    foot --app-id="forgework-lights-tui" --title="ForgeworkLights" /usr/local/bin/omarchy-argb-menu
elif command -v wezterm &> /dev/null; then
    wezterm start --class="forgework-lights-tui" /usr/local/bin/omarchy-argb-menu
else
    # Fallback to any available terminal
    x-terminal-emulator -e /usr/local/bin/omarchy-argb-menu
fi
