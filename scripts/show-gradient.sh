#!/bin/bash
# Display current ARGB gradient in a notification/popup

STATE_FILE="$HOME/.cache/omarchy-argb/state.json"

if [[ ! -f "$STATE_FILE" ]]; then
    notify-send "ForgeworkLights" "Daemon not running" -i video-display
    exit 1
fi

# Read current colors
colors=$(jq -r '.colors[]' "$STATE_FILE" 2>/dev/null)

if [[ -z "$colors" ]]; then
    notify-send "ForgeworkLights" "No gradient active" -i video-display
    exit 1
fi

# Build color preview HTML for notification
theme=$(jq -r '.theme // "Unknown"' "$STATE_FILE")
led_count=$(echo "$colors" | wc -l)

# Create gradient CSS string
gradient_stops=""
i=0
while IFS= read -r color; do
    if [[ $i -gt 0 ]]; then
        gradient_stops+=", "
    fi
    gradient_stops+="$color"
    ((i++))
done <<< "$colors"

# Show notification with gradient preview
notify-send "ForgeworkLights" \
    "Theme: $theme\nLEDs: $led_count\nGradient: $gradient_stops" \
    -i video-display \
    -t 5000
