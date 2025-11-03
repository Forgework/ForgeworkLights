# Waybar Integration

Add ForgeworkLights module to your Waybar configuration.

## Installation

1. Copy the script to your PATH:
   ```bash
   sudo cp scripts/show-gradient.sh /usr/local/bin/omarchy-argb-show
   sudo chmod +x /usr/local/bin/omarchy-argb-show
   ```

2. Add module to your `~/.config/waybar/config`:
   ```json
   {
     "custom/forgework-lights": {
       "format": "󰌵",
       "tooltip": true,
       "tooltip-format": "ForgeworkLights: {}",
       "exec": "jq -r '.theme // \"No theme\"' ~/.cache/omarchy-argb/state.json 2>/dev/null || echo 'Off'",
       "interval": 2,
       "on-click": "/usr/local/bin/omarchy-argb-show"
     }
   }
   ```

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
- **Click**: Opens notification showing current gradient colors
- **Update**: Refreshes every 2 seconds

## Requirements

- `jq` - JSON processor (`sudo pacman -S jq`)
- `libnotify` - Desktop notifications (`sudo pacman -S libnotify`)
- Running `omarchy-argb daemon`
