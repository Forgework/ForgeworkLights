# ForgeworkLights Theme Data (LED + TUI)

This document describes how theme data is modeled and used in ForgeworkLights after the TUI was migrated off TOML.

## Files: LED vs TUI theme data

Theme data is now split by concern:

- **LED gradients (daemon + animations)**
  - User runtime: `~/.config/forgeworklights/led_themes.json`
  - Premade defaults: `/usr/local/share/forgeworklights/led_themes.json`

- **TUI palettes (per-theme UI colors)**
  - User runtime: `~/.config/forgeworklights/tui_themes.json`

Schema for LED themes (`led_themes.json`, per theme):

```jsonc
{
  "themes": {
    "<key>": {
      "name": "Human Name",
      "colors": ["#rrggbb", ...]  // LED gradient used by the daemon
    }
  }
}
```

Schema for TUI themes (`tui_themes.json`, per theme):

```jsonc
{
  "themes": {
    "<key>": {
      "main_bg": "#091819",
      "main_fg": "#ffffff",
      "title": "#93c7d2",
      "hi_fg": "#C3DDDF",
      "selected_bg": "#345254",
      "inactive_fg": "#345254",
      "div_line": "#345254",
      "box_outline": "#79beae",
      "button_fg": "#79beae",
      "secondary_bg": "#0d2324",
      "hover_bg": "#1a3536"
    }
  }
}
```

- `colors` in `themes.json` drives LED gradients (unchanged from the original design).
- Per-theme TUI palettes live separately in `tui_themes.json`.

## How themes are populated (`sync_themes`)

The script that owns theme generation is:

- `scripts/tui/sync_themes.py`

It is used by:

- The CLI entrypoint installed as `forgeworklights-sync-themes`.
- The TUI (Theme Selection panel \u2192 Sync action).
- The helper script `scripts/generate-tui-theme.py` (which just calls `sync_themes`).

What `sync_themes` does:

- Scans Omarchy theme directories (`OMARCHY_THEME_DIRS`) for theme folders.
- For each theme folder:
  - Reads `btop.theme` and extracts CPU gradient colors (`cpu_start`, `cpu_mid`, `cpu_end`).
  - Generates a 14-step gradient and writes it into `colors` for that theme in `themes.json`.
  - Also extracts a rich TUI palette from keys like `main_bg`, `main_fg`, `title`, `hi_fg`, `selected_bg`, `inactive_fg`, `div_line`, `meter_bg`, `proc_box`.
  - Stores that palette under the same theme key in `tui_themes.json`.
- Restores any missing premade themes from the shared `/usr/local/share/forgeworklights/themes.json`.
- For most themes, existing entries in `themes.json` are **not overwritten**. The exception is `aether`, which is allowed to update so it tracks live edits.

Result: LED gradients and TUI palettes are stored in **separate** files but share the same theme keys.

## How the active theme is selected

The daemon and LEDs may use `LED_THEME_FILE` to choose a specific theme or
to follow Omarchy. The **TUI itself, however, always visually tracks the
current Omarchy theme** regardless of what is written into `led-theme`.

Files and paths relevant for the TUI:

- `THEME_SYMLINK = ~/.config/omarchy/current/theme`
- `TUI_THEMES_DB_PATH = ~/.config/forgeworklights/tui_themes.json`

Selection rules implemented in `scripts/tui/theme.py`:

1. **Match Omarchy (primary path)**
   - Resolve `THEME_SYMLINK` to its target directory.
   - Use the directory name of the target (e.g. `aether`, `nord`) as the
     theme key, if it exists in `tui_themes.json["themes"]`.

2. **Fallback**
   - If the symlink does not resolve to a known theme key, the TUI falls
     back to the first available key in `tui_themes.json["themes"]`.
   - If the database is empty or invalid, the TUI uses built-in default
     colors.

## How the TUI uses the `tui` palette

The TUI loads and reloads its palette through `scripts/tui/theme.py`:

- `load_theme()` reads `TUI_THEMES_DB_PATH`, resolves the active theme key, and returns:

  ```python
  {**DEFAULT_COLORS, **themes[theme_key]}
  ```

- `THEME` is a module-level dict initialized from `load_theme()` at import time.
- When the theme is reloaded, the app updates `THEME` in place and regenerates CSS.

Places where reload happens (`scripts/tui/app.py`):

- After LED theme changes from the Theme Selection panel.
- After Omarchy theme changes via `THEME_SYMLINK`.
- After `themes.json` is rewritten by `sync_themes` (detected via inotify).

Because `load_theme()` always reads from `themes.json`, the TUI and daemon stay in sync about what \"theme X\" means.

## How to regenerate themes

### From the CLI

After installing ForgeworkLights:

```bash
forgeworklights-sync-themes --verbose
```

This will:

- Restore any missing premade themes into `~/.config/forgeworklights/themes.json`.
- Scan Omarchy themes, add new entries, and (for Aether) update existing ones.
- Populate or update the `tui` blocks for any themes backed by a valid `btop.theme`.

### From the repo (development)

Inside the project root:

```bash
python scripts/generate-tui-theme.py
```

This is a thin wrapper over `tui.sync_themes.sync_themes(verbose=True)` and has the same effect as the CLI entrypoint, but is convenient during development without a full install.

## How to customize TUI colors per theme

To tweak TUI colors for a specific theme, edit:

- `~/.config/forgeworklights/themes.json`

Look for the theme key:

```jsonc
"aether": {
  "name": "Aether",
  "colors": [ ... ],
  "tui": {
    "main_bg": "#091819",
    "box_outline": "#79beae",
    ...
  }
}
```

You can change any of the `tui` values. On save:

- The TUI will see `themes.json` change via inotify.
- It will call its reload hook, re-read the `tui` block, regenerate CSS, and repaint.... or it should....
- No TOML files or restarts are required
