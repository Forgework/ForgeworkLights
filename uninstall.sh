#!/bin/bash

# ForgeworkLights Uninstall Script

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "========================================"
echo "  ForgeworkLights Uninstall"
echo "========================================"
echo ""

# Stop service first to prevent it from turning LEDs back on
if systemctl --user is-active omarchy-argb.service &> /dev/null; then
    echo "Stopping service..."
    systemctl --user stop omarchy-argb.service
    systemctl --user disable omarchy-argb.service
    echo -e "${GREEN}✓${NC} Service stopped and disabled"
fi

# Turn off all 22 LEDs
if command -v framework_tool &> /dev/null; then
    echo "Turning off LEDs..."
    sudo framework_tool --rgbkbd 0 $(printf '0x000000 %.0s' {1..22}) &> /dev/null || true
    echo -e "${GREEN}✓${NC} All 22 LEDs turned off"
fi

# Remove systemd service
if [ -f ~/.config/systemd/user/omarchy-argb.service ]; then
    rm ~/.config/systemd/user/omarchy-argb.service
    systemctl --user daemon-reload
    echo -e "${GREEN}✓${NC} Systemd service removed"
fi

# Remove binaries
if [ -f /usr/local/bin/omarchy-argb ]; then
    sudo rm /usr/local/bin/omarchy-argb
    echo -e "${GREEN}✓${NC} Removed /usr/local/bin/omarchy-argb"
fi

if [ -f /usr/local/bin/omarchy-argb-menu ]; then
    sudo rm /usr/local/bin/omarchy-argb-menu
    echo -e "${GREEN}✓${NC} Removed /usr/local/bin/omarchy-argb-menu"
fi

if [ -f /usr/local/bin/omarchy-argb-sync-themes ]; then
    sudo rm /usr/local/bin/omarchy-argb-sync-themes
    echo -e "${GREEN}✓${NC} Removed /usr/local/bin/omarchy-argb-sync-themes"
fi

if [ -f /usr/local/bin/omarchy-argb-menu-floating ]; then
    sudo rm /usr/local/bin/omarchy-argb-menu-floating
    echo -e "${GREEN}✓${NC} Removed /usr/local/bin/omarchy-argb-menu-floating"
fi

# Remove TUI package module
if command -v python3 &> /dev/null; then
    TUI_INSTALL_DIR=$(python3 -c "import site; print(site.getsitepackages()[0])" 2>/dev/null)/tui
    if [ -d "$TUI_INSTALL_DIR" ]; then
        sudo rm -rf "$TUI_INSTALL_DIR"
        echo -e "${GREEN}✓${NC} Removed TUI package module from $TUI_INSTALL_DIR"
    fi
    # Also check old location for backwards compatibility
    for py_path in /usr/local/lib/python*/site-packages/tui; do
        if [ -d "$py_path" ]; then
            sudo rm -rf "$py_path"
            echo -e "${GREEN}✓${NC} Removed old TUI package from $py_path"
        fi
    done
fi

# Remove sudoers rule
if [ -f /etc/sudoers.d/omarchy-argb ]; then
    sudo rm /etc/sudoers.d/omarchy-argb
    echo -e "${GREEN}✓${NC} Removed sudoers rule"
fi

# Ask about config
echo ""
read -p "Remove configuration (~/.config/omarchy-argb)? [Y/n] " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    rm -rf ~/.config/omarchy-argb
    echo -e "${GREEN}✓${NC} Configuration removed"
fi

# Ask about cache
read -p "Remove cache (~/.cache/omarchy-argb)? [Y/n] " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    rm -rf ~/.cache/omarchy-argb
    echo -e "${GREEN}✓${NC} Cache removed"
fi

# Ask about waybar integration
echo ""
read -p "Remove waybar integration? [Y/n] " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    # Find waybar config
    waybar_config=""
    if [ -f ~/.config/waybar/config.jsonc ]; then
        waybar_config=~/.config/waybar/config.jsonc
    elif [ -f ~/.config/waybar/config.json ]; then
        waybar_config=~/.config/waybar/config.json
    elif [ -f ~/.config/waybar/config ]; then
        waybar_config=~/.config/waybar/config
    fi
    
    if [ -n "$waybar_config" ]; then
        # Backup before modifying
        cp "$waybar_config" "${waybar_config}.uninstall-backup"
        
        # Remove module using sed (simpler and more robust than JSON parsing)
        # Remove the module definition block
        sed -i '/^[[:space:]]*"custom\/forgework-lights":/,/^[[:space:]]*}/d' "$waybar_config"
        
        # Remove from modules arrays (handle both with and without trailing comma)
        sed -i 's/"custom\/forgework-lights",\?[[:space:]]*//g' "$waybar_config"
        
        # Clean up any double commas that might have been created
        sed -i 's/,,/,/g' "$waybar_config"
        
        # Clean up trailing commas before closing brackets
        sed -i 's/,[[:space:]]*\]/\]/g' "$waybar_config"
        
        echo -e "${GREEN}✓${NC} Removed from waybar config"
        
        # Remove CSS styling
        if [ -f ~/.config/waybar/style.css ]; then
            if grep -q "custom-forgework-lights" ~/.config/waybar/style.css; then
                # Remove the ForgeworkLights section
                sed -i '/\/\* ForgeworkLights module styling \*\//,/^}$/d' ~/.config/waybar/style.css
                echo -e "${GREEN}✓${NC} Removed CSS styling"
            fi
        fi
        
        # Reload waybar
        if pgrep waybar > /dev/null; then
            killall -SIGUSR2 waybar 2>/dev/null || true
            echo -e "${GREEN}✓${NC} Reloaded waybar"
        fi
    else
        echo -e "${YELLOW}!${NC} Waybar config not found"
    fi
fi

# Ask about Hyprland window rules
echo ""
read -p "Remove Hyprland window rules? [Y/n] " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    hypr_config="$HOME/.config/hypr/hyprland.conf"
    
    if [ -f "$hypr_config" ]; then
        # Check if rules exist
        if grep -q "forgework-lights-tui" "$hypr_config"; then
            # Backup before modifying
            cp "$hypr_config" "${hypr_config}.uninstall-backup"
            echo "Created backup: ${hypr_config}.uninstall-backup"
            
            # Remove all ForgeworkLights-related lines
            # Remove the comment headers
            sed -i '/# ForgeworkLights TUI Window Rules/d' "$hypr_config"
            sed -i '/# Ghostty-specific rules/d' "$hypr_config"
            
            # Remove all windowrulev2 rules (including commented ones)
            sed -i '/forgework-lights-tui/d' "$hypr_config"
            
            # Remove ghostty-specific ForgeworkLights rules
            sed -i '/com\.mitchellh\.ghostty.*ForgeworkLights/d' "$hypr_config"
            
            # Clean up extra blank lines
            sed -i '/^$/N;/^\n$/D' "$hypr_config"
            
            echo -e "${GREEN}✓${NC} Removed Hyprland window rules"
            
            # Reload Hyprland config
            if command -v hyprctl &> /dev/null; then
                hyprctl reload &>/dev/null && echo -e "${GREEN}✓${NC} Reloaded Hyprland config" || true
            fi
        else
            echo -e "${YELLOW}!${NC} No Hyprland window rules found"
        fi
    else
        echo -e "${YELLOW}!${NC} Hyprland config not found"
    fi
fi

echo ""
echo -e "${GREEN}Uninstall complete${NC}"
echo ""
echo "Files removed:"
echo "  - /usr/local/bin/omarchy-argb"
echo "  - /usr/local/bin/omarchy-argb-menu"
echo "  - /usr/local/bin/omarchy-argb-sync-themes"
echo "  - /usr/local/bin/omarchy-argb-menu-floating"
echo "  - ~/.config/systemd/user/omarchy-argb.service"
echo "  - /etc/sudoers.d/omarchy-argb"
echo ""
echo "Backups created (if modified):"
echo "  - ~/.config/waybar/config.*.uninstall-backup"
echo "  - ~/.config/hypr/hyprland.conf.uninstall-backup"
