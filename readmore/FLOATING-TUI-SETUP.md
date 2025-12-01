# Floating TUI Window Setup

The ForgeworkLights TUI can now open as a **floating window** in the upper right corner when launched from Waybar. this is handeled by the installer.

## Quick Setup

Run the installer to set everything up automatically:

```bash
./install.sh
```

The installer will:
1. Install the floating launcher script
2. Configure Waybar to use the floating launcher  
3. Add Hyprland window rules for positioning
4. Reload Hyprland config

## Manual Setup

If you prefer to configure manually:

### 1. Install Launcher Script

```bash
sudo cp scripts/launch-tui-floating.sh /usr/local/bin/forgeworklights-menu-floating
sudo chmod +x /usr/local/bin/forgeworklights-menu-floating
```

### 2. Update Waybar Config

Edit `~/.config/waybar/config` and update the ForgeworkLights module:

```json
{
  "custom/forgework-lights": {
    "format": " 󰛨 ",
    "tooltip-format": "Lights: {}",
    "exec": "jq -r '.theme // \"Off\"' ~/.cache/forgeworklights/state.json 2>/dev/null || echo 'Off'",
    "interval": 2,
    "on-click": "/usr/local/bin/forgeworklights-menu-floating"
  }
}
```

Reload Waybar:
```bash
killall -SIGUSR2 waybar
```

### 3. Add Hyprland Window Rules

Add these lines to `~/.config/hypr/hyprland.conf`:

```conf
# ForgeworkLights TUI Window Rules
windowrulev2 = float, class:^(forgework-lights-tui)$
windowrulev2 = size 1200 900, class:^(forgework-lights-tui)$
windowrulev2 = move 100%-1220 60, class:^(forgework-lights-tui)$
windowrulev2 = animation slide, class:^(forgework-lights-tui)$
```

Reload Hyprland:
```bash
hyprctl reload
```

## Window Positioning

The default position is **upper right corner**, 20 pixels from the edge, 60 pixels from the top bar.

### Customize Position

Edit the `move` rule in your Hyprland config:

```conf
# Move further from right edge (increase offset):
windowrulev2 = move 100%-1420 60, class:^(forgework-lights-tui)$

# Move higher up (decrease Y offset):
windowrulev2 = move 100%-1220 40, class:^(forgework-lights-tui)$

# Move lower (increase Y offset):
windowrulev2 = move 100%-1220 100, class:^(forgework-lights-tui)$
```

### Customize Size

Edit the `size` rule:

```conf
# Smaller (compact):
windowrulev2 = size 1000 600, class:^(forgework-lights-tui)$

# Larger:
windowrulev2 = size 1400 900, class:^(forgework-lights-tui)$
```

### Center Instead

Replace the `move` rule with:

```conf
windowrulev2 = center, class:^(forgework-lights-tui)$
```

## Terminal Support

The launcher automatically detects and uses your terminal emulator:
- **kitty** - Recommended, best Unicode support
- **alacritty** - Good performance  
- **foot** - Lightweight Wayland native
- **wezterm** - Feature-rich

The launcher sets the window class to `forgework-lights-tui` for Hyprland window rules.

## Testing

Test the floating launcher manually:

```bash
/usr/local/bin/forgeworklights-menu-floating
```

The TUI should open as a floating window in the upper right corner.

## Troubleshooting

**Window doesn't float:**
- Check if Hyprland rules are in `~/.config/hypr/hyprland.conf`
- Reload Hyprland: `hyprctl reload`
- Check window class: `hyprctl clients | grep -A 5 forgework`

**Wrong position:**
- Adjust the `move` rule values in Hyprland config
- Formula: `move 100%-<window_width+margin> <top_margin>`

**Terminal not detected:**
- The launcher will fall back to `x-terminal-emulator`
- Set your preferred terminal in the launcher script

## Window Rule Reference

| Rule | Description |
|------|-------------|
| `float` | Make window floating (not tiled) |
| `size W H` | Set window dimensions in pixels |
| `move X Y` | Position window (100% = screen width/height) |
| `animation slide` | Add slide-in animation |
| `center` | Center window on screen |
| `noborder` | Remove window border |
| `noanim` | Disable animations |

## Recommended Settings

**For top-right dropdown effect:**
```conf
windowrulev2 = float, class:^(forgework-lights-tui)$
windowrulev2 = size 1200 800, class:^(forgework-lights-tui)$
windowrulev2 = move 100%-1220 60, class:^(forgework-lights-tui)$
windowrulev2 = animation slide, class:^(forgework-lights-tui)$
```

**For centered overlay:**
```conf
windowrulev2 = float, class:^(forgework-lights-tui)$
windowrulev2 = size 1200 800, class:^(forgework-lights-tui)$
windowrulev2 = center, class:^(forgework-lights-tui)$
windowrulev2 = animation popin 90%, class:^(forgework-lights-tui)$
```

**For minimal popup:**
```conf
windowrulev2 = float, class:^(forgework-lights-tui)$
windowrulev2 = size 1000 600, class:^(forgework-lights-tui)$
windowrulev2 = move 100%-1020 80, class:^(forgework-lights-tui)$
windowrulev2 = noborder, class:^(forgework-lights-tui)$
windowrulev2 = noanim, class:^(forgework-lights-tui)$
```
