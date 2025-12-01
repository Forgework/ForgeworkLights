# ForgeworkLights

Synchronize Framework Desktop ARGB LED strip with Omarchy theme colors in real-time.

## Overview

ForgeworkLights is a C++20 daemon designed specifically for **Framework Desktop** running **Omarchy Linux**. It monitors your active Omarchy theme and automatically applies a beautiful 3-color temperature gradient from `btop.theme` to the 22-LED WS2812B strip connected to the desktop's JARGB1 header.

## Requirements

### Hardware
- **Framework Desktop** (DIY Edition or Pre-built)
- **22-LED WS2812B ARGB strip** connected to the JARGB1 3-pin header
- Strip must use **GRB color order** (standard for WS2812B)

### Software
- **Omarchy Linux** (or compatible Arch-based distribution)
- **framework-system** package (provides `framework_tool`)
- **Omarchy theme system** (btop.theme)
- **CMake** 3.16+ and **C++20 compiler** (g++ or clang++)

## Quick Install (Recommended)

The automated installer will check dependencies, build, and set everything up:

```bash
git clone https://github.com/Forgework/ForgeworkLights.git
cd ForgeworkLights
./install.sh
```

The installer will:
- ✓ Check for Framework Desktop hardware
- ✓ Verify dependencies (framework_tool, cmake, etc.)
- ✓ Build the daemon and root helper
- ✓ Install user daemon to `/usr/local/bin`
- ✓ Install root helper to `/usr/local/libexec` (root:root 4755 setuid-root)
- ✓ Install LED theme database to `~/.config/forgeworklights/led_themes.json` and `/usr/local/share/forgeworklights/led_themes.json`
- ✓ Install the Textual TUI package (`forgeworklights-menu`) plus theme sync/generator helpers
- ✓ Set up configuration
- ✓ Install systemd user service (optional)
- ✓ Set up waybar integration (optional)

### Uninstall

```bash
./uninstall.sh
```

## Manual Installation

### Installing framework-system

The daemon requires `framework_tool` from the `framework-system` package to control the ARGB LEDs.

**Install via pacman:**
```bash
# ArchLinux
sudo pacman -S framework-system
```

**Manual installation:**
```bash
git clone https://aur.archlinux.org/framework-system.git
cd framework-system
makepkg -si
```

**Verify installation:**
```bash
which framework_tool
# Should output: /usr/bin/framework_tool

# Test LED control (requires sudo):
sudo framework_tool --rgbkbd 0 0xFF0000 0x00FF00 0x0000FF
```

### Build & Install Manually

```bash
# Clone repository
git clone https://github.com/Forgework/ForgeworkLights.git
cd ForgeworkLights

# Build
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j

# Install daemon (runs as user)
sudo install -Dm755 build/forgeworklights /usr/local/bin/forgeworklights

# Install root helper (privileged hardware access only, setuid-root)
sudo install -Dm755 -o root -g root build/fw_root_helper /usr/local/libexec/fw_root_helper
sudo chmod 4755 /usr/local/libexec/fw_root_helper

# Install TUI package (optional)
python3 -m pip install --user -r requirements.txt
SITE_PACKAGES=$(python3 -c "import site; print(site.getsitepackages()[0])")
sudo mkdir -p "$SITE_PACKAGES/tui"
sudo cp -r scripts/tui/* "$SITE_PACKAGES/tui/"
```

## Configuration

Create config file at `~/.config/forgeworklights/config.toml`:

```toml
led_count = 22
max_brightness = 0.7
gamma_exponent = 1.33     # 0.45 = sRGB→linear, 1.0 = no correction
color_order = "RGB"       # framework_tool uses RGB
tool_path = "/usr/bin/framework_tool"
```

### Configuration Options

- **led_count**: Number of LEDs in your strip (default: 22)
- **max_brightness**: Brightness cap 0.0-1.0 (default: 0.7)
- **gamma_exponent**: Color space correction (0.45 = sRGB→linear, 1.0 = passthrough)
- **color_order**: "RGB" (framework_tool uses RGB)
- **tool_path**: Path to framework_tool binary

### LED Theme Workflow

- Installer seeds `led_themes.json` for both user and system scopes so curated gradients are always available.
- The Textual control panel (`forgeworklights-menu`) lets you browse, edit, or author gradients; CLI users can edit the JSON directly.
- `scripts/tui/sync_themes.py` (also exposed as `forgeworklights-sync-themes`) refreshes Omarchy-derived themes and keeps the daemon/TUI databases aligned.

ℹ️ **Need the full picture?** See [readmore/THEMES-LED-README.md](readmore/THEMES-LED-README.md) for LED gradient storage + hot reload behavior and [readmore/THEMES-TUI-README.md](readmore/THEMES-TUI-README.md) for sync + TUI palette details.

### Current Limiting

The Framework JARGB1 header provides a 5V rail with **2.4A maximum safe draw**. ForgeworkLights uses the WS2812B physical model (60mA per LED at full white) to automatically limit current:

- **Safety mode (default)**: Enforces 2.4A rail limit by uniformly scaling LED brightness when needed
- **Safety off**: Disables current limiting (use only if you know your hardware can handle it)

Enable/disable with the `--safety` flag:
```bash
forgeworklights daemon --safety=on   # Default: enable 2.4A limiting
forgeworklights daemon --safety=off  # Disable limiting
forgeworklights once --safety=on     # Also works with test command
```

Brightness is always clamped to [0.0, 1.0] regardless of safety mode.

## Usage

### Manual Commands

```bash
# Test pattern (one-time)
forgeworklights once
forgeworklights once --safety=off     # Disable current limiting

# Run daemon (foreground)
forgeworklights daemon
forgeworklights daemon --safety=on    # Explicit safety mode (default)

# Adjust brightness (0.0-1.0)
forgeworklights brightness 0.5
```

### Systemd Service

Enable automatic startup:

```bash
# Copy service file
cp systemd/forgeworklights.service ~/.config/systemd/user/

# Enable and start
systemctl --user enable --now forgeworklights.service

# Check status
systemctl --user status forgeworklights
```

The daemon runs as your user via systemd user service. Hardware access is handled by a dedicated setuid-root helper binary (`/usr/local/libexec/fw_root_helper`) that provides secure, validated access to framework_tool.

## How It Works

### Architecture

ForgeworkLights uses a secure two-tier architecture:

1. **User Daemon** (`forgeworklights daemon`)
   - Runs as your user via systemd user service
   - Monitors theme changes via inotify
   - Calculates LED colors and animations
   - Never requires root privileges

2. **Root Helper** (`/usr/local/libexec/fw_root_helper`)
   - Hardened setuid-root binary owned by root:root with 4755 permissions
   - Only function: accept validated LED data and call `framework_tool`
   - Strict input validation (hex-encoded RGB data only)
   - No configuration, no file I/O, no user logic

### Process Flow (high level)

1. Watch Omarchy's `~/.config/omarchy/current/theme` symlink and the LED theme database for changes.
2. Resolve colors: either pull a curated gradient from `led_themes.json` or derive one from the active Omarchy palette (`btop.theme`/`palette.json`).
3. Apply gamma + brightness + safety limits, then hand frames to the root helper (`framework_tool --rgbkbd`).

More detail lives in [readmore/THEMES-LED-README.md](readmore/THEMES-LED-README.md).

## Omarchy Theme Requirements

For best results supply a `btop.theme` (or `palette.json`/`theme.json`) with `temp_*` or `accent*` colors inside each Omarchy theme folder so sync/gradient generation succeeds. Exact parsing rules and fallbacks are documented in [readmore/THEMES-LED-README.md](readmore/THEMES-LED-README.md) and [readmore/THEMES-TUI-README.md](readmore/THEMES-TUI-README.md).

## Limitations

- **Framework Desktop only**: Uses Desktop-specific `framework_tool --rgbkbd` command
- **Omarchy Linux optimized**: Expects Omarchy theme directory structure
- **btop.theme required**: Most themes include this; custom themes may need it added
- **Root helper required**: LED control uses dedicated root helper binary for hardware access
- **22 LEDs max**: Designed for JARGB1 header spec (with a .4A buffer) (can be adjusted in config)
- **GRB color order**: WS2812B standard; other strips may need config change

## Troubleshooting

**LEDs don't light up:**
- Verify `framework_tool` is installed: `which framework_tool`
- Test manually: `sudo framework_tool --rgbkbd 0 0xFF0000 0x00FF00 0x0000FF`
- Check strip is connected to JARGB1 header
- Ensure strip uses 5V power (not 12V)

**Wrong colors / grayscale:**
- Check `color_order` in config (try "RGB" if "GRB" fails) (AI keeps insisting on this, but it's GRB that the LED wants.... unless rgbkbd handles this??)
- Increase `max_brightness` if colors look washed out
- Verify theme has `btop.theme` file

**Theme changes not detected:**
- Check daemon is running: `systemctl --user status forgeworklights`
- Verify theme symlink: `ls -l ~/.config/omarchy/current/theme`
- Check logs: `journalctl --user -u forgeworklights -f`

**Permission errors:**
- Verify root helper is installed: `ls -l /usr/local/libexec/fw_root_helper`
- Should show: `-rwsr-xr-x 1 root root` (setuid bit set)
- Reinstall if needed: `./install.sh`

## Further Reading

- [readmore/THEMES-LED-README.md](readmore/THEMES-LED-README.md) – LED gradient schema, daemon reload hooks, theme selection rules.
- [readmore/THEMES-TUI-README.md](readmore/THEMES-TUI-README.md) – Sync pipeline, TUI palettes, per-theme customization tips.

## License

GPL-2.0 license

## Credits

Built for the Framework Desktop and Omarchy Linux community.
