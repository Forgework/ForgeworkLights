# ForgeworkLights

Synchronize Framework Desktop ARGB LED strip with Omarchy theme colors in real-time.

## Overview

ForgeworkLights is a C++20 daemon designed specifically for **Framework Desktop** running **Omarchy Linux**. It monitors your active Omarchy theme and automatically applies a beautiful 3-color temperature gradient from `btop.theme` to the 14-LED WS2812B strip connected to the desktop's JARGB1 header.

## Requirements

### Hardware
- **Framework Desktop** (DIY Edition or Pre-built)
- **14-LED WS2812B ARGB strip** connected to the JARGB1 3-pin header
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
- ✓ Build the daemon
- ✓ Install binaries to `/usr/local/bin`
- ✓ Set up configuration
- ✓ Configure passwordless sudo for framework_tool
- ✓ Install systemd service (optional)
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

# Install
sudo install -Dm755 build/omarchy-argb /usr/local/bin/omarchy-argb
sudo install -Dm755 scripts/show-gradient.sh /usr/local/bin/omarchy-argb-show
```

## Configuration

Create config file at `~/.config/omarchy-argb/config.toml`:

```toml
led_count = 14
max_current_amps = 2.0
max_brightness = 0.7
gamma_exponent = 1.0      # 1.0 = no correction, 0.45 = sRGB→linear
color_order = "GRB"       # WS2812B standard
tool_path = "/usr/bin/framework_tool"
```

### Configuration Options

- **led_count**: Number of LEDs in your strip (default: 14)
- **max_current_amps**: Current limit in amps (default: 2.0A)
- **max_brightness**: Brightness cap 0.0-1.0 (default: 0.7)
- **gamma_exponent**: Color space correction (1.0 = passthrough)
- **color_order**: "GRB" for WS2812B, "RGB" for other strips
- **tool_path**: Path to framework_tool binary

## Usage

### Manual Commands

```bash
# Test pattern (one-time)
omarchy-argb once

# Run daemon (foreground)
omarchy-argb daemon

# Adjust brightness (0.0-1.0)
omarchy-argb brightness 0.5

# Check color order
omarchy-argb prob
```

### Systemd Service

Enable automatic startup:

```bash
# Copy service file
cp systemd/omarchy-argb.service ~/.config/systemd/user/

# Enable and start
systemctl --user enable --now omarchy-argb.service

# Check status
systemctl --user status omarchy-argb
```

The daemon requires `sudo` access to `framework_tool`. You may want to add a sudoers rule:

```bash
# /etc/sudoers.d/framework-argb
your_username ALL=(ALL) NOPASSWD: /usr/bin/framework_tool --rgbkbd *
```

## How It Works

1. **Theme Detection**: Monitors `~/.config/omarchy/current/theme` symlink via inotify
2. **Color Extraction**: Reads `btop.theme` from active theme directory:
   - `theme[temp_start]` → First gradient color
   - `theme[temp_mid]` → Middle gradient color
   - `theme[temp_end]` → Final gradient color
3. **Gradient Generation**: Creates smooth 3-color gradient across 14 LEDs
4. **Post-Processing**: Applies gamma correction, brightness scaling, and current limiting
5. **LED Update**: Sends frame to hardware via `framework_tool --rgbkbd`
6. **Live Updates**: Automatically reloads when theme changes (< 150ms latency)

## Omarchy Theme Requirements

Themes must include a `btop.theme` file with temperature gradient colors:

```bash
~/.local/share/omarchy/themes/nord/btop.theme
~/.local/share/omarchy/themes/catppuccin/btop.theme
# etc.
```

The daemon extracts these lines:
```
theme[temp_start]="#81A1C1"
theme[temp_mid]="#88C0D0"
theme[temp_end]="#ECEFF4"
```

**Fallback**: If `btop.theme` is missing, the daemon tries `palette.json` or `theme.json` with `accent`, `accent2`, `accent3` fields.

## Limitations

- **Framework Desktop only**: Uses Desktop-specific `framework_tool --rgbkbd` command
- **Omarchy Linux optimized**: Expects Omarchy theme directory structure
- **btop.theme required**: Most themes include this; custom themes may need it added
- **Sudo required**: LED control needs root access to hardware interface
- **14 LEDs max**: Designed for JARGB1 header spec (with a .4A buffer) (can be adjusted in config)
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
- Check daemon is running: `systemctl --user status omarchy-argb`
- Verify theme symlink: `ls -l ~/.config/omarchy/current/theme`
- Check logs: `journalctl --user -u omarchy-argb -f`

**Permission errors:**
- Add sudoers rule (see Usage section)
- Or run daemon with sudo: `sudo SUDO_USER="$USER" omarchy-argb daemon`

## License

GPL-2.0 license

## Contributing

Pull requests welcome! Please ensure code builds and follows existing style.

## Credits

Built for the Framework Desktop and Omarchy Linux community.
