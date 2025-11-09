# Waybar Integration

Add ForgeworkLights module to your Waybar configuration.

## Installation

1. Copy the TUI script to your PATH:
   ```bash
   sudo cp scripts/options-tui.py /usr/local/bin/omarchy-argb-menu
   sudo chmod +x /usr/local/bin/omarchy-argb-menu
   ```

2. Add module to your `~/.config/waybar/config`:
   ```json
   {
     "custom/forgework-lights": {
       "format": "󰛨",
       "tooltip": true,
       "tooltip-format": "ForgeworkLights: {}",
       "exec": "jq -r '.theme // \"No theme\"' ~/.cache/omarchy-argb/state.json 2>/dev/null || echo 'Off'",
       "interval": 2,
       "on-click": "kitty -e /usr/local/bin/omarchy-argb-menu"
     }
   }
   ```
   
   **Note:** Replace `kitty -e` with your terminal emulator command. The installer auto-detects this.

3. Add the module to your modules list in the same config:
   ```json
   "modules-right": ["...", "custom/forgework-lights", "..."]
   ```

4. Optional: Add styling to `~/.config/waybar/style.css`:
   ```css
   #custom-forgework-lights {
     padding: 0 10px;
     color: #88c0d0;
   }
   
   #custom-forgework-lights:hover {
     background-color: rgba(136, 192, 208, 0.2);
   }
   ```

5. Reload Waybar:
   ```bash
   killall -SIGUSR2 waybar
   ```

## Module Behavior

- **Icon**: 󰌵 (LED icon)
- **Tooltip**: Shows current theme name
- **Click**: Opens TUI control panel with status, gradient, brightness, and actions
- **Update**: Refreshes every 2 seconds

## Requirements

- `jq` - JSON processor (`sudo pacman -S jq`)
- `libnotify` - Desktop notifications (`sudo pacman -S libnotify`)
- `python` + `textual` - Terminal UI control panel (`sudo pacman -S python`, then `pip install --user textual`)
- `bc` - Calculator for brightness percentage (`sudo pacman -S bc`)
- A terminal emulator (kitty, alacritty, foot, wezterm, etc.) - auto-detected by installer
- Running `omarchy-argb daemon`

**Note:** The installer will automatically detect your terminal emulator and configure waybar to launch the TUI in it.

## TUI Control Panel Features

Clicking the waybar module opens a **terminal-based control panel** with:

**Live Status (auto-refreshing every 2s):**
- Daemon status (Running/Stopped)
- Current theme name  
- Current brightness level

**Current Gradient Display:**
- Shows hex values of the 3 key gradient colors
- Visual gradient preview with colored blocks
- Auto-updates when theme changes

**Interactive Brightness Control:**
- Progress bar showing current brightness
- Arrow keys: Up/Down (+/- 5%), Left/Right (+/- 10%)
- Button controls: ◀ / ▶

**Action Buttons:**
- Reload Daemon [R] - Restart the daemon service
- View Logs [L] - Show recent daemon logs

**Keyboard Shortcuts:**
- `Q` - Quit
- Arrow keys - Adjust brightness
- `R`, `L` - Quick actions
