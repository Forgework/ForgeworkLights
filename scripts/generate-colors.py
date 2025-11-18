#!/usr/bin/env python3
"""
Generate 22-color gradients for each theme in themes.json
Interpolates smoothly across the original 3-5 colors to create LED-specific colors
"""

import json
import sys
from pathlib import Path

# Import shared utilities and constants
sys.path.insert(0, str(Path(__file__).parent))
from tui.utils.colors import generate_gradient
from tui.constants import THEMES_DB_PATH

def main():
    
    # Check if called with command-line colors (for custom theme creation)
    if len(sys.argv) > 1:
        # Mode: Generate 22 colors from 3 input colors and output to stdout
        if len(sys.argv) != 4:
            print("Usage: generate-colors.py <color1> <color2> <color3>", file=sys.stderr)
            return 1
        
        input_colors = sys.argv[1:4]
        gradient = generate_gradient(input_colors, 22)
        
        # Output each color on its own line for easy parsing
        for color in gradient:
            print(color)
        
        return 0
    
    # Mode: Update all themes in themes.json
    themes_path = THEMES_DB_PATH
    
    if not themes_path.exists():
        print(f"Error: {themes_path} not found")
        return 1
    
    # Load existing themes
    with open(themes_path, 'r') as f:
        data = json.load(f)
    
    if "themes" not in data:
        print("Error: Invalid themes.json format")
        return 1
    
    # Generate 22 colors for each theme
    updated_count = 0
    for theme_key, theme_data in data["themes"].items():
        if "colors" in theme_data and theme_data["colors"]:
            original_colors = theme_data["colors"]
            original_count = len(original_colors)
            
            # Generate 22-color gradient
            new_colors = generate_gradient(original_colors, 22)
            theme_data["colors"] = new_colors
            
            print(f"✓ {theme_key}: {original_count} → 22 colors")
            updated_count += 1
    
    # Save updated themes.json
    with open(themes_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"\n✓ Updated {updated_count} themes with 22-color gradients")
    print(f"✓ Saved to: {themes_path}")
    return 0

if __name__ == "__main__":
    exit(main())
