#!/bin/bash
set -e

# ForgeworkLights Installation Script
# Checks dependencies, builds, and installs the daemon with waybar integration

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "========================================"
echo "  ForgeworkLights Installation"
echo "========================================"
echo ""

# Check if running on Framework Desktop
check_framework_desktop() {
    if ! grep -q "Framework" /sys/devices/virtual/dmi/id/product_name 2>/dev/null; then
        echo -e "${YELLOW}Warning: This doesn't appear to be a Framework Desktop${NC}"
        echo "The daemon may not work correctly on other hardware."
        read -p "Continue anyway? [y/N] " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    else
        echo -e "${GREEN}✓${NC} Framework Desktop detected"
    fi
}

# Check for required dependencies
check_dependencies() {
    echo ""
    echo "Checking dependencies..."
    
    local missing=0
    
    # Essential build tools
    if ! command -v cmake &> /dev/null; then
        echo -e "${RED}✗${NC} cmake not found (required for building)"
        missing=1
    else
        echo -e "${GREEN}✓${NC} cmake found"
    fi
    
    if ! command -v g++ &> /dev/null && ! command -v clang++ &> /dev/null; then
        echo -e "${RED}✗${NC} C++ compiler not found (g++ or clang++)"
        missing=1
    else
        echo -e "${GREEN}✓${NC} C++ compiler found"
    fi
    
    # Framework tool (critical)
    if ! command -v framework_tool &> /dev/null; then
        echo -e "${RED}✗${NC} framework_tool not found"
        echo "  Install with: sudo pacman -S framework-system"
        echo "  or from AUR: https://aur.archlinux.org/packages/framework-system"
        missing=1
    else
        echo -e "${GREEN}✓${NC} framework_tool found"
    fi
    
    # Optional but recommended
    if ! command -v jq &> /dev/null; then
        echo -e "${YELLOW}!${NC} jq not found (optional, for waybar integration)"
        echo "  Install with: sudo pacman -S jq"
    else
        echo -e "${GREEN}✓${NC} jq found"
    fi
    
    if ! command -v notify-send &> /dev/null; then
        echo -e "${YELLOW}!${NC} notify-send not found (optional, for notifications)"
        echo "  Install with: sudo pacman -S libnotify"
    else
        echo -e "${GREEN}✓${NC} notify-send found"
    fi
    
    if [ $missing -eq 1 ]; then
        echo ""
        echo -e "${RED}Missing required dependencies. Please install them first.${NC}"
        exit 1
    fi
}

# Build the project
build_project() {
    echo ""
    echo "Building ForgeworkLights..."
    
    cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
    cmake --build build -j$(nproc)
    
    echo -e "${GREEN}✓${NC} Build complete"
}

# Install binaries and scripts
install_binaries() {
    echo ""
    echo "Installing binaries..."
    
    # Install main binary
    sudo install -Dm755 build/omarchy-argb /usr/local/bin/omarchy-argb
    echo -e "${GREEN}✓${NC} Installed omarchy-argb to /usr/local/bin"
    
    # Install waybar script
    if [ -f scripts/show-gradient.sh ]; then
        sudo install -Dm755 scripts/show-gradient.sh /usr/local/bin/omarchy-argb-show
        echo -e "${GREEN}✓${NC} Installed waybar script to /usr/local/bin"
    fi
    
    # Install sample config
    mkdir -p ~/.config/omarchy-argb
    if [ ! -f ~/.config/omarchy-argb/config.toml ]; then
        cp config/config.toml.sample ~/.config/omarchy-argb/config.toml
        echo -e "${GREEN}✓${NC} Installed config to ~/.config/omarchy-argb/config.toml"
    else
        echo -e "${YELLOW}!${NC} Config already exists, skipping"
    fi
}

# Setup systemd service
setup_systemd() {
    echo ""
    read -p "Install systemd user service (auto-start on login)? [Y/n] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        mkdir -p ~/.config/systemd/user
        cp systemd/omarchy-argb.service ~/.config/systemd/user/
        systemctl --user daemon-reload
        echo -e "${GREEN}✓${NC} Systemd service installed"
        
        read -p "Enable service now? [Y/n] " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Nn]$ ]]; then
            systemctl --user enable --now omarchy-argb.service
            echo -e "${GREEN}✓${NC} Service enabled and started"
        fi
    fi
}

# Setup sudo access for framework_tool
setup_sudo() {
    echo ""
    read -p "Configure passwordless sudo for framework_tool? [Y/n] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        SUDOERS_FILE="/etc/sudoers.d/omarchy-argb"
        echo "$USER ALL=(ALL) NOPASSWD: /usr/bin/framework_tool --rgbkbd *" | sudo tee "$SUDOERS_FILE" > /dev/null
        sudo chmod 0440 "$SUDOERS_FILE"
        echo -e "${GREEN}✓${NC} Sudoers rule added"
    fi
}

# Setup waybar integration
setup_waybar() {
    echo ""
    if [ ! -f ~/.config/waybar/config ]; then
        echo -e "${YELLOW}!${NC} Waybar config not found, skipping integration"
        return
    fi
    
    read -p "Add waybar module configuration? [Y/n] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        echo ""
        echo "Add this to your ~/.config/waybar/config modules:"
        echo ""
        cat << 'EOF'
"custom/forgework-lights": {
  "format": "󰌵",
  "tooltip-format": "ForgeworkLights: {}",
  "exec": "jq -r '.theme // \"No theme\"' ~/.cache/omarchy-argb/state.json 2>/dev/null || echo 'Off'",
  "interval": 2,
  "on-click": "/usr/local/bin/omarchy-argb-show"
}
EOF
        echo ""
        echo "Then add \"custom/forgework-lights\" to your modules-right array."
        echo ""
        read -p "Press Enter to continue..." 
    fi
}

# Test the installation
test_installation() {
    echo ""
    echo "Testing installation..."
    
    if omarchy-argb probe &> /dev/null; then
        echo -e "${GREEN}✓${NC} omarchy-argb executable works"
    else
        echo -e "${RED}✗${NC} omarchy-argb test failed"
        return 1
    fi
    
    # Test framework_tool access
    if sudo -n framework_tool --help &> /dev/null; then
        echo -e "${GREEN}✓${NC} framework_tool sudo access works"
    else
        echo -e "${YELLOW}!${NC} framework_tool requires password (configure sudo rule)"
    fi
}

# Main installation flow
main() {
    check_framework_desktop
    check_dependencies
    build_project
    install_binaries
    setup_sudo
    setup_systemd
    setup_waybar
    
    echo ""
    echo "========================================"
    echo -e "${GREEN}Installation complete!${NC}"
    echo "========================================"
    echo ""
    echo "Quick start:"
    echo "  Test: omarchy-argb once"
    echo "  Run:  omarchy-argb daemon"
    echo "  or:   systemctl --user start omarchy-argb"
    echo ""
    echo "Config: ~/.config/omarchy-argb/config.toml"
    echo ""
    
    test_installation
}

main "$@"
