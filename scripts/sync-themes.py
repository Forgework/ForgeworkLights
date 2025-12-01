#!/usr/bin/env python3
"""CLI wrapper for ForgeworkLights theme sync.

This script is installed as forgeworklights-sync-themes and simply delegates
to the shared tui.sync_themes module so that the same logic is used by both
the TUI and the command-line tool.
"""

import sys

from tui.sync_themes import main


if __name__ == "__main__":
    sys.exit(main())
