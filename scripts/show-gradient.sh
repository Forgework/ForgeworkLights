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

# Build smooth gradient preview
theme=$(jq -r '.theme // "Unknown"' "$STATE_FILE")

# Create a temporary image showing the gradient
temp_img="/tmp/forgework-gradient-$$.png"

# Use ImageMagick to create a smooth gradient image
# Create array of colors
color_array=()
while IFS= read -r color; do
    color_array+=("$color")
done <<< "$colors"

total=${#color_array[@]}

# Create smooth gradient by blending individual gradients
if [[ $total -eq 1 ]]; then
    # Single color - solid fill
    convert -size 600x100 xc:"${color_array[0]}" "$temp_img" 2>/dev/null
elif [[ $total -eq 2 ]]; then
    # Two colors - simple gradient
    convert -size 600x100 gradient:"${color_array[0]}-${color_array[1]}" "$temp_img" 2>/dev/null
else
    # Multiple colors - create blended segments
    segment_width=$((600 / (total - 1)))
    
    # Create first segment
    convert -size ${segment_width}x100 gradient:"${color_array[0]}-${color_array[1]}" "$temp_img" 2>/dev/null
    
    # Add remaining segments
    for ((i=1; i<total-1; i++)); do
        temp_segment="/tmp/segment-$$.png"
        convert -size ${segment_width}x100 gradient:"${color_array[$i]}-${color_array[$i+1]}" "$temp_segment" 2>/dev/null
        convert "$temp_img" "$temp_segment" +append "$temp_img" 2>/dev/null
        rm -f "$temp_segment"
    done
    
    # Resize to exact width
    convert "$temp_img" -resize 600x100\! "$temp_img" 2>/dev/null
fi

if [[ -f "$temp_img" ]]; then
    # Show notification with gradient image
    notify-send "ForgeworkLights" \
        "Theme: $theme" \
        -i "$temp_img" \
        -t 5000
    
    # Clean up temp file after a delay
    (sleep 6; rm -f "$temp_img") &
else
    # Fallback to text if ImageMagick not available
    notify-send "ForgeworkLights" \
        "Theme: $theme\nGradient preview (install imagemagick for visual)" \
        -i video-display \
        -t 5000
fi
