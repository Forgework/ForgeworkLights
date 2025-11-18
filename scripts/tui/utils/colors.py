"""
Color utility functions for gradient generation and color conversion.
Shared by TUI widgets, sync scripts, and color generation tools.
"""

def hex_to_rgb(hex_color):
    """Convert hex color to RGB tuple"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def rgb_to_hex(r, g, b):
    """Convert RGB tuple to hex color"""
    return f"#{int(r):02x}{int(g):02x}{int(b):02x}"

def generate_gradient(colors, num_steps=22):
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
