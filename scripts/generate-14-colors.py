#!/usr/bin/env python3
"""
Generate 14-color gradients for each theme in themes.json
Interpolates smoothly across the original 3-5 colors to create LED-specific colors
"""

import json
from pathlib import Path

def hex_to_rgb(hex_color):
    """Convert hex color to RGB tuple"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def rgb_to_hex(r, g, b):
    """Convert RGB tuple to hex color"""
    return f"#{int(r):02x}{int(g):02x}{int(b):02x}"

def generate_gradient(colors, num_steps=14):
    """Generate smooth gradient with num_steps colors from input colors"""
    if not colors:
        return []
    
    rgb_colors = [hex_to_rgb(c) for c in colors]
    num_colors = len(rgb_colors)
    
    if num_colors == 1:
        # Single color - repeat it
        return colors * num_steps
    
    gradient = []
    for i in range(num_steps):
        # Map position to color gradient (0.0 to 1.0)
        pos = i / (num_steps - 1) if num_steps > 1 else 0
        color_pos = pos * (num_colors - 1)
        
        idx = int(color_pos)
        frac = color_pos - idx
        
        if idx >= num_colors - 1:
            # Last color
            r, g, b = rgb_colors[num_colors - 1]
        else:
            # Interpolate between idx and idx+1
            c1 = rgb_colors[idx]
            c2 = rgb_colors[idx + 1]
            r = c1[0] + (c2[0] - c1[0]) * frac
            g = c1[1] + (c2[1] - c1[1]) * frac
            b = c1[2] + (c2[2] - c1[2]) * frac
        
        gradient.append(rgb_to_hex(r, g, b))
    
    return gradient

def main():
    themes_path = Path.home() / ".config/omarchy-argb/themes.json"
    
    if not themes_path.exists():
        print(f"Error: {themes_path} not found")
        return 1
    
    # Load existing themes
    with open(themes_path, 'r') as f:
        data = json.load(f)
    
    if "themes" not in data:
        print("Error: Invalid themes.json format")
        return 1
    
    # Generate 14 colors for each theme
    updated_count = 0
    for theme_key, theme_data in data["themes"].items():
        if "colors" in theme_data and theme_data["colors"]:
            original_colors = theme_data["colors"]
            original_count = len(original_colors)
            
            # Generate 14-color gradient
            new_colors = generate_gradient(original_colors, 14)
            theme_data["colors"] = new_colors
            
            print(f"✓ {theme_key}: {original_count} → 14 colors")
            updated_count += 1
    
    # Save updated themes.json
    with open(themes_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"\n✓ Updated {updated_count} themes with 14-color gradients")
    print(f"✓ Saved to: {themes_path}")
    return 0

if __name__ == "__main__":
    exit(main())
