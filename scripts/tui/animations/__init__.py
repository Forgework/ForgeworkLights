"""
LED Animations Module

Animation execution is now handled by the C++ daemon.
This module provides the list of available animations and their configurable parameters.
"""

# Animation definitions with parameters
# Format: (id, name, description, parameters)
# Parameters: list of (param_name, display_name, min, max, default, step, unit)
ANIMATIONS = {
    "static": {
        "name": "Static",
        "description": "No animation - solid gradient",
        "params": []
    },
    "breathe": {
        "name": "Breathe",
        "description": "Slow fade in/out",
        "params": [
            ("period", "Period", 1.0, 10.0, 3.0, 0.5, "seconds")
        ]
    },
    "wave": {
        "name": "Wave",
        "description": "Left to right flowing",
        "params": [
            ("speed", "Speed", 0.1, 2.0, 0.5, 0.1, "cycles/sec")
        ]
    },
    "ripple": {
        "name": "Ripple",
        "description": "Center outward pulse",
        "params": [
            ("period", "Period", 0.5, 5.0, 2.0, 0.1, "seconds"),
            ("ripple_width", "Width", 0.1, 1.0, 0.3, 0.05, "ratio")
        ]
    },
    "runner": {
        "name": "Runner",
        "description": "Shooting stars with trails",
        "params": [
            ("speed", "Speed", 5.0, 50.0, 20.0, 5.0, "LEDs/sec"),
            ("trail_length", "Trail", 3, 15, 8, 1, "LEDs"),
            ("num_runners", "Count", 1, 5, 2, 1, "stars")
        ]
    },
    "bounce": {
        "name": "Bounce",
        "description": "Segment bouncing back/forth",
        "params": [
            ("period", "Period", 0.5, 5.0, 2.0, 0.1, "seconds"),
            ("segment_size", "Size", 2, 10, 5, 1, "LEDs")
        ]
    },
    "sparkle": {
        "name": "Sparkle",
        "description": "Random twinkling",
        "params": [
            ("sparkle_rate", "Rate", 0.01, 0.5, 0.1, 0.01, "prob"),
            ("sparkle_duration", "Duration", 5, 30, 15, 1, "frames")
        ]
    },
    "strobe": {
        "name": "Strobe",
        "description": "Fast flashing",
        "params": [
            ("frequency", "Frequency", 1.0, 20.0, 10.0, 1.0, "Hz")
        ]
    },
    "gradient-shift": {
        "name": "Gradient Shift",
        "description": "Smooth color transitions",
        "params": [
            ("period", "Period", 2.0, 30.0, 10.0, 1.0, "seconds"),
            ("shift_amount", "Shift", 0.5, 2.0, 1.0, 0.1, "cycles")
        ]
    }
}

# Legacy list format for backward compatibility
ANIMATIONS_LIST = [
    (anim_id, f"{data['name']} - {data['description']}")
    for anim_id, data in ANIMATIONS.items()
]

__all__ = ['ANIMATIONS', 'ANIMATIONS_LIST']
