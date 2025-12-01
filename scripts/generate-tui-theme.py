#!/usr/bin/env python3
"""Generate ForgeworkLights TUI palettes into themes.json.

This helper now simply delegates to the sync_themes logic used by the
TUI, ensuring that per-theme "tui" blocks are generated for all
Omarchy themes and written into ~/.config/forgeworklights/themes.json.
"""

from __future__ import annotations

from tui.sync_themes import sync_themes


def main() -> int:
    changes = sync_themes(verbose=True)
    # sync_themes returns the number of themes added/updated/restored.
    # Treat any non-negative value as success.
    return 0 if changes >= 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
