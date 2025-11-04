#!/usr/bin/env python3
"""
Sync themes from Omarchy theme directory to themes.json
Scans all theme directories, extracts colors from btop.theme files,
generates 14-color gradients, and updates the database.
"""

import json
import re
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
        return colors * num_steps
    
    gradient = []
    for i in range(num_steps):
        pos = i / (num_steps - 1) if num_steps > 1 else 0
        color_pos = pos * (num_colors - 1)
        
        idx = int(color_pos)
        frac = color_pos - idx
        
        if idx >= num_colors - 1:
            r, g, b = rgb_colors[num_colors - 1]
        else:
            c1 = rgb_colors[idx]
            c2 = rgb_colors[idx + 1]
            r = c1[0] + (c2[0] - c1[0]) * frac
            g = c1[1] + (c2[1] - c1[1]) * frac
            b = c1[2] + (c2[2] - c1[2]) * frac
        
        gradient.append(rgb_to_hex(r, g, b))
    
    return gradient

def extract_colors_from_btop(btop_file):
    """Extract temp_start, temp_mid, temp_end colors from btop.theme"""
    try:
        data = btop_file.read_text()
        start = re.search(r'theme\[temp_start\]\s*=\s*"#([0-9a-fA-F]{6})"', data)
        mid = re.search(r'theme\[temp_mid\]\s*=\s*"#([0-9a-fA-F]{6})"', data)
        end = re.search(r'theme\[temp_end\]\s*=\s*"#([0-9a-fA-F]{6})"', data)
        
        if start and mid and end:
            return [f"#{start.group(1)}", f"#{mid.group(1)}", f"#{end.group(1)}"]
    except Exception:
        pass
    return None

def extract_colors_from_json(json_file):
    """Extract accent colors from palette.json or theme.json"""
    try:
        data = json.loads(json_file.read_text())
        if "accent" in data and "accent2" in data and "accent3" in data:
            return [data["accent"], data["accent2"], data["accent3"]]
    except Exception:
        pass
    return None

def scan_theme_directory(theme_dir):
    """Scan a theme directory for color information"""
    theme_name = theme_dir.name
    
    # Try palette files in priority order
    palette_files = [
        ("btop.theme", extract_colors_from_btop),
        ("palette.json", extract_colors_from_json),
        ("theme.json", extract_colors_from_json)
    ]
    
    for filename, extractor in palette_files:
        filepath = theme_dir / filename
        if filepath.exists():
            colors = extractor(filepath)
            if colors:
                return {
                    "name": theme_name.replace("-", " ").title(),
                    "colors": generate_gradient(colors, 14)
                }
    
    return None

def sync_themes(verbose=False):
    """Sync all themes from Omarchy directory to themes.json"""
    # Locate Omarchy theme directories
    theme_dirs = []
    possible_locations = [
        Path.home() / ".config/omarchy/themes",
        Path.home() / ".local/share/omarchy/themes",
    ]
    
    for location in possible_locations:
        if location.exists() and location.is_dir():
            theme_dirs.extend([d for d in location.iterdir() if d.is_dir()])
    
    if not theme_dirs:
        if verbose:
            print("No theme directories found")
        return 0
    
    # Load existing themes.json
    themes_path = Path.home() / ".config/omarchy-argb/themes.json"
    themes_path.parent.mkdir(parents=True, exist_ok=True)
    
    if themes_path.exists():
        try:
            with open(themes_path, 'r') as f:
                data = json.load(f)
        except Exception:
            data = {"themes": {}}
    else:
        data = {"themes": {}}
    
    # Scan all theme directories
    new_count = 0
    updated_count = 0
    
    for theme_dir in theme_dirs:
        theme_key = theme_dir.name
        theme_data = scan_theme_directory(theme_dir)
        
        if theme_data:
            if theme_key not in data["themes"]:
                data["themes"][theme_key] = theme_data
                new_count += 1
                if verbose:
                    print(f"✓ Added: {theme_key}")
            else:
                # Update if colors changed
                existing = data["themes"][theme_key]
                if existing.get("colors") != theme_data["colors"]:
                    data["themes"][theme_key] = theme_data
                    updated_count += 1
                    if verbose:
                        print(f"✓ Updated: {theme_key}")
    
    # Save updated themes.json
    with open(themes_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    if verbose:
        print(f"\nSync complete:")
        print(f"  New themes: {new_count}")
        print(f"  Updated: {updated_count}")
        print(f"  Total themes: {len(data['themes'])}")
        print(f"  Saved to: {themes_path}")
    
    return new_count + updated_count

def main():
    import sys
    verbose = "--verbose" in sys.argv or "-v" in sys.argv
    changes = sync_themes(verbose=True)
    return 0 if changes >= 0 else 1

if __name__ == "__main__":
    exit(main())
