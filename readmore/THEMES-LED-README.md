# ForgeworkLights LED Themes

This document explains how LED gradient data is modeled, stored, and consumed by the ForgeworkLights daemon and tooling.

## Runtime files and locations

LED theme data lives in JSON alongside a few helper files:

- **User LED gradient database**: `~/.config/forgeworklights/led_themes.json`
- **Premade defaults restored on sync**: `/usr/local/share/forgeworklights/led_themes.json`
- **Active LED theme preference**: `~/.config/forgeworklights/led-theme`
- **Daemon brightness + control dir**: `~/.config/forgeworklights/` (watched for `brightness`, `led-theme`, `animation`, etc.)

The `led_themes.json` schema matches the daemon's expectations:

```jsonc
{
  "themes": {
    "<key>": {
      "name": "Human Name",
      "colors": ["#rrggbb", ...]  // Gradient the daemon interpolates across
    }
  }
}
```

Each `colors` array should contain at least three entries (the daemon interpolates between them across the physical LED count).

## How the daemon loads and watches LED themes

`argb_daemon` loads LED gradients through `ThemeDatabase`:

1. On startup it synchronizes Omarchy themes (`forgeworklights-sync-themes`) so `led_themes.json` stays in sync with the desktop palettes.@src/argb_daemon.cpp#177-185
2. It then attempts to load `~/.config/forgeworklights/led_themes.json`, falling back through legacy user/system paths if needed.@src/argb_daemon.cpp#186-210
3. The daemon installs an inotify watch on the directory that owns the resolved database path; any rewrite of `led_themes.json` triggers a reload hook so new colors are picked up automatically.@src/argb_daemon.cpp#212-227 @src/argb_daemon.cpp#482-511
4. `ThemeDatabase` handles the minimal JSON parsing (name + gradient list) and exposes helpers to list themes or fetch colors for a key.@src/theme_database.cpp#41-163

The daemon also watches `~/.config/forgeworklights/` for `led-theme` changes made by the TUI or CLI so user selections apply without restarting.@src/argb_daemon.cpp#77-145 @src/argb_daemon.cpp#458-544

## Selecting the active LED theme

`argb_daemon` reads `~/.config/forgeworklights/led-theme` whenever it composes a frame:

- **`match` (default)** – Follow the current Omarchy theme by resolving the `~/.config/omarchy/current/theme` symlink. The daemon extracts palette files from that directory (preferring `btop.theme`) and interpolates a BTOP accent gradient if no LED database entry exists for the Omarchy key.@src/argb_daemon.cpp#109-145 @src/argb_daemon.cpp#287-305
- **Explicit theme key** – Use a specific LED gradient from `led_themes.json`. The daemon looks up the key via `ThemeDatabase::get` and leverages the stored multi-stop gradient for smooth per-LED interpolation.@src/argb_daemon.cpp#237-285

If neither a database gradient nor a BTOP palette is available, the daemon falls back to a simple rainbow so LEDs remain responsive.@src/argb_daemon.cpp#306-311

The ForgeworkLights TUI writes to `led-theme` when a user selects “Match Omarchy” or a specific entry. Tapping the “Sync” action in the Theme Selection panel also refreshes the database and touches the preference file so the daemon reloads quickly.@scripts/tui/app.py#167-278 @scripts/tui/widgets/theme_selection.py#103-233

## How LED gradients are generated (`sync_themes`)

`scripts/tui/sync_themes.py` owns populating `led_themes.json`:

1. Discover Omarchy theme directories defined in `OMARCHY_THEME_DIRS`.
2. For each directory, read `btop.theme`, extract CPU gradient colors (`cpu_start`, `cpu_mid`, `cpu_end`), and expand them into a 14-stop gradient.
3. Store that gradient as `colors` for the theme key in `led_themes.json`. The same scan optionally extracts per-theme TUI palettes which get written to `tui_themes.json` (not consumed by the daemon but shares keys).
4. Restore any missing premade defaults from `/usr/local/share/forgeworklights/led_themes.json` so the user database always contains a baseline set.
5. Never overwrite existing user gradients unless the theme key is `aether`, which intentionally tracks the live Omarchy palette.

This logic powers the `forgeworklights-sync-themes` CLI, the TUI “Sync” action, and the dev helper `scripts/generate-tui-theme.py` (which simply invokes `sync_themes(verbose=True)`).@scripts/tui/sync_themes.py#136-260 @THEMES-TUI-README.md#54-149

## Creating and editing LED themes

There are two supported paths for custom LED gradients:

1. **TUI Theme Creator** – The ForgeworkLights TUI ships a creator/editor panel that lets users pick three anchor colors, preview the generated 22-step gradient live on the LEDs, and then save it into `led_themes.json`. The widget writes the JSON file directly and touches `led-theme` so the daemon reloads. It also supports editing existing entries and automatically restores the previously selected theme after previews.@scripts/tui/widgets/theme_creator.py#168-363
2. **Manual edits** – Because the database is plain JSON, power users can edit `~/.config/forgeworklights/led_themes.json` in an editor. After saving, either touch the file or run the sync helper so the daemon's inotify watch observes the update (or simply wait for the TUI to issue a reload after detecting the change).@src/argb_daemon.cpp#482-544

## Recommended workflow recap

1. Run `forgeworklights-sync-themes --verbose` (or trigger Sync in the TUI) after installing new Omarchy themes.
2. Use the TUI Theme Selection panel to pick “Match Omarchy” or a specific gradient. This updates `led-theme`, which the daemon watches.
3. Customize gradients via the Theme Creator or manual JSON edits; the daemon and animations will hot-reload as soon as `led_themes.json` changes.
4. For scripted environments, write the desired theme key into `~/.config/forgeworklights/led-theme` (use `match` to follow Omarchy) and ensure `led_themes.json` contains the corresponding gradient entry.
