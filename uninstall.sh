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

echo ""
echo -e "${GREEN}Uninstall complete${NC}"
echo ""
echo "Note: Manually remove waybar module from ~/.config/waybar/config if added"
