#!/usr/bin/env python3
"""
ForgeworkLights TUI Control Panel
BTOP-style interface for controlling the ARGB daemon
"""

from tui import ForgeworkLightsTUI


def main():
    app = ForgeworkLightsTUI()
    app.run()


if __name__ == "__main__":
    main()
