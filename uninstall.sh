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

# Turn off LEDs gracefully before uninstalling
if command -v omarchy-argb &> /dev/null; then
    echo "Turning off LEDs..."
    # Send all-black frame to turn off LEDs
    if omarchy-argb once &> /dev/null; then
        # Override with black frame
        if command -v framework_tool &> /dev/null; then
            sudo framework_tool --rgbkbd 0 $(printf '0x000000 %.0s' {1..14}) &> /dev/null || true
        fi
    fi
    echo -e "${GREEN}✓${NC} LEDs turned off"
fi

# Stop and disable service
if systemctl --user is-active omarchy-argb.service &> /dev/null; then
    echo "Stopping service..."
    systemctl --user stop omarchy-argb.service
    systemctl --user disable omarchy-argb.service
    echo -e "${GREEN}✓${NC} Service stopped and disabled"
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

if [ -f /usr/local/bin/omarchy-argb-show ]; then
    sudo rm /usr/local/bin/omarchy-argb-show
    echo -e "${GREEN}✓${NC} Removed /usr/local/bin/omarchy-argb-show"
fi

# Remove sudoers rule
if [ -f /etc/sudoers.d/omarchy-argb ]; then
    sudo rm /etc/sudoers.d/omarchy-argb
    echo -e "${GREEN}✓${NC} Removed sudoers rule"
fi

# Ask about config
echo ""
read -p "Remove configuration (~/.config/omarchy-argb)? [y/N] " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    rm -rf ~/.config/omarchy-argb
    echo -e "${GREEN}✓${NC} Configuration removed"
fi

# Ask about cache
read -p "Remove cache (~/.cache/omarchy-argb)? [y/N] " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    rm -rf ~/.cache/omarchy-argb
    echo -e "${GREEN}✓${NC} Cache removed"
fi

# Ask about waybar integration
echo ""
read -p "Remove waybar integration? [y/N] " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
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

echo ""
echo -e "${GREEN}Uninstall complete${NC}"
