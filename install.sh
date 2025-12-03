#!/bin/bash
set -e

# ForgeworkLights Installation Script
# Checks dependencies, builds, and installs the daemon with waybar integration

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

SHORT_DELAY=0.05
pause_step() {
    sleep "$SHORT_DELAY"
}

SHORTCUTS_INSTALLED=0

# Setup Hyprland keyboard shortcuts
setup_hyprland_shortcuts() {
    echo ""

    if ! command -v hyprctl &> /dev/null; then
        echo -e "${YELLOW}!${NC} Hyprland not detected, skipping keyboard shortcuts"
        return
    fi

    local hypr_config="$HOME/.config/hypr/hyprland.conf"
    local bindings_target="$HOME/.config/forgeworklights/hyprland-bindings.conf"
    local include_line="source=${bindings_target}"

    if [ ! -f "$hypr_config" ]; then
        echo -e "${YELLOW}!${NC} Hyprland config not found at $hypr_config"
        return
    fi

    read -p "Install Hyprland keyboard shortcuts (Super+Alt combos)? [Y/n] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Nn]$ ]]; then
        return
    fi

    mkdir -p "$(dirname "$bindings_target")"
    if [ -f "config/hyprland-shortcuts.conf" ]; then
        cp "config/hyprland-shortcuts.conf" "$bindings_target"
    elif [ -f "${BASH_SOURCE%/*}/config/hyprland-shortcuts.conf" ]; then
        cp "${BASH_SOURCE%/*}/config/hyprland-shortcuts.conf" "$bindings_target"
    else
        echo -e "${RED}✗${NC} Shortcut template not found"
        return 1
    fi
    echo -e "${GREEN}✓${NC} Installed shortcut template to $bindings_target"
    SHORTCUTS_INSTALLED=1

    if ! grep -Fxq "$include_line" "$hypr_config"; then
        local backup_path="${hypr_config}.forgeworklights-shortcuts.backup"
        cp "$hypr_config" "$backup_path"
        echo "Created backup: $backup_path"

        {
            echo ""
            echo "# ForgeworkLights keyboard shortcuts"
            echo "$include_line"
        } >> "$hypr_config"

        echo -e "${GREEN}✓${NC} Added shortcut include to $hypr_config"
    else
        echo -e "${YELLOW}!${NC} Shortcut include already present in $hypr_config"
    fi

    hyprctl reload &>/dev/null && echo -e "${GREEN}✓${NC} Reloaded Hyprland config" || true
}

echo "========================================"
echo "  ForgeworkLights Installation"
echo "========================================"
echo ""

# Check if running on Framework Desktop
check_framework_desktop() {
    local vendor=$(cat /sys/devices/virtual/dmi/id/sys_vendor 2>/dev/null || echo "")
    local product=$(cat /sys/devices/virtual/dmi/id/product_name 2>/dev/null || echo "")
    
    # Check for Framework vendor AND Desktop product (not Laptop)
    if [[ "$vendor" != "Framework" ]] || [[ ! "$product" =~ Desktop ]]; then
        echo -e "${YELLOW}Warning: This doesn't appear to be a Framework Desktop${NC}"
        echo "Detected: $vendor - $product"
        echo "This tool is designed for Framework Desktop with LED strips."
        read -p "Continue anyway? [y/N] " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    else
        echo -e "${GREEN}✓${NC} Framework Desktop detected: $product"
    fi
}

# Setup Walker launcher integration
setup_walker_launcher() {
    echo ""

    if ! command -v walker &> /dev/null; then
        echo -e "${YELLOW}!${NC} Walker launcher not detected; skipping shortcut install"
        return
    fi

    read -p "Install Walker launcher shortcut? [Y/n] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Nn]$ ]]; then
        return
    fi

    local home_dir="$HOME"
    local launcher_dir="$home_dir/.local/bin"
    local launcher_path="$launcher_dir/forgeworklights.sh"
    local icon_target="$home_dir/.local/share/icons/forgeworklights.png"
    local desktop_dir="$home_dir/.local/share/applications"
    local desktop_entry="$desktop_dir/forgeworklights.desktop"

    mkdir -p "$launcher_dir" "$desktop_dir"
    install -Dm644 "Icons/icon.png" "$icon_target"

    cat > "$launcher_path" <<'LAUNCHER'
#!/usr/bin/env bash
set -euo pipefail

systemctl --user start forgeworklights.service >/dev/null 2>&1 || true

if command -v forgeworklights-menu-floating &> /dev/null; then
    exec forgeworklights-menu-floating "$@"
elif command -v forgeworklights-menu &> /dev/null; then
    exec forgeworklights-menu "$@"
else
    echo "ForgeworkLights TUI not found" >&2
    exit 1
fi
LAUNCHER
    chmod +x "$launcher_path"

    cat > "$desktop_entry" <<DESKTOP
[Desktop Entry]
Type=Application
Name=Forgework Lights
Comment=Control panel for Forgework Lights
Exec=${home_dir}/.local/bin/forgeworklights.sh
Icon=${icon_target}
Terminal=false
Categories=Utility;
DESKTOP

    if command -v update-desktop-database &> /dev/null; then
        update-desktop-database "$desktop_dir" >/dev/null 2>&1 || true
    fi

    if [ -f "$home_dir/.config/systemd/user/forgeworklights.service" ]; then
        if systemctl --user is-enabled forgeworklights.service &> /dev/null; then
            echo -e "${GREEN}✓${NC} forgeworklights.service already enabled"
        else
            if systemctl --user enable --now forgeworklights.service &> /dev/null; then
                echo -e "${GREEN}✓${NC} forgeworklights.service enabled and started"
            else
                echo -e "${YELLOW}!${NC} Unable to enable forgeworklights.service automatically"
            fi
        fi
    else
        echo -e "${YELLOW}!${NC} Systemd service not installed; launcher will start daemon on demand"
    fi

    echo -e "${GREEN}✓${NC} Walker launcher installed at $desktop_entry"
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
        # Check CMake version (>= 3.16 required)
        cmake_version=$(cmake --version | head -n1 | grep -oP '\d+\.\d+' | head -n1)
        cmake_major=$(echo "$cmake_version" | cut -d. -f1)
        cmake_minor=$(echo "$cmake_version" | cut -d. -f2)
        if [ "$cmake_major" -lt 3 ] || ([ "$cmake_major" -eq 3 ] && [ "$cmake_minor" -lt 16 ]); then
            echo -e "${YELLOW}!${NC} cmake $cmake_version found (>= 3.16 recommended)"
        else
            echo -e "${GREEN}✓${NC} cmake $cmake_version found"
        fi
    fi
    
    if ! command -v g++ &> /dev/null && ! command -v clang++ &> /dev/null; then
        echo -e "${RED}✗${NC} C++ compiler not found (g++ or clang++)"
        missing=1
    else
        # Check compiler version (C++20 support needed)
        if command -v g++ &> /dev/null; then
            gcc_version=$(g++ --version | head -n1 | grep -oP '\d+\.\d+' | head -n1)
            gcc_major=$(echo "$gcc_version" | cut -d. -f1)
            if [ "$gcc_major" -lt 11 ]; then
                echo -e "${YELLOW}!${NC} g++ $gcc_version found (>= 11.0 recommended for C++20)"
            else
                echo -e "${GREEN}✓${NC} g++ $gcc_version found"
            fi
        elif command -v clang++ &> /dev/null; then
            clang_version=$(clang++ --version | head -n1 | grep -oP '\d+\.\d+' | head -n1)
            clang_major=$(echo "$clang_version" | cut -d. -f1)
            if [ "$clang_major" -lt 14 ]; then
                echo -e "${YELLOW}!${NC} clang++ $clang_version found (>= 14.0 recommended for C++20)"
            else
                echo -e "${GREEN}✓${NC} clang++ $clang_version found"
            fi
        fi
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
    
    if ! command -v python3 &> /dev/null; then
        echo -e "${YELLOW}!${NC} python3 not found (optional, for TUI control panel)"
        echo "  Install with: sudo pacman -S python"
    else
        # Check Python version (>= 3.11 required for tomllib)
        python_version=$(python3 --version | grep -oP '\d+\.\d+' | head -n1)
        python_major=$(echo "$python_version" | cut -d. -f1)
        python_minor=$(echo "$python_version" | cut -d. -f2)
        if [ "$python_major" -lt 3 ] || ([ "$python_major" -eq 3 ] && [ "$python_minor" -lt 11 ]); then
            echo -e "${YELLOW}!${NC} python $python_version found (>= 3.11 required for TUI)"
        else
            echo -e "${GREEN}✓${NC} python $python_version found"
        fi
        
        # Check for textual
        if ! python3 -c "import textual" &> /dev/null; then
            echo -e "${YELLOW}!${NC} textual not found (optional, for TUI control panel)"
            echo "  Install with: pip install --user -r requirements.txt"
        else
            textual_version=$(python3 -c "import textual; print(textual.__version__)" 2>/dev/null || echo "unknown")
            echo -e "${GREEN}✓${NC} textual $textual_version found"
        fi
    fi
    
    if ! command -v bc &> /dev/null; then
        echo -e "${YELLOW}!${NC} bc not found (optional, for brightness control)"
        echo "  Install with: sudo pacman -S bc"
    else
        echo -e "${GREEN}✓${NC} bc found"
    fi
    
    if [ $missing -eq 1 ]; then
        echo ""
        echo -e "${RED}Missing required dependencies. Please install them first.${NC}"
        exit 1
    fi
}

# Install optional dependencies
install_optional_deps() {
    echo ""
    echo "Installing optional dependencies..."
    
    local to_install=()
    
    if ! command -v jq &> /dev/null; then
        to_install+=("jq")
    fi
    
    if ! command -v notify-send &> /dev/null; then
        to_install+=("libnotify")
    fi
    
    if ! command -v python3 &> /dev/null; then
        to_install+=("python")
    fi
    
    if ! command -v bc &> /dev/null; then
        to_install+=("bc")
    fi
    
    if [ ${#to_install[@]} -gt 0 ]; then
        echo "Will install: ${to_install[*]}"
        sudo pacman -S --needed --noconfirm "${to_install[@]}"
        echo -e "${GREEN}✓${NC} Optional dependencies installed"
    else
        echo -e "${GREEN}✓${NC} All optional dependencies already installed"
    fi
    
    # Install Python dependencies from requirements.txt
    if command -v python3 &> /dev/null; then
        if ! python3 -c "import textual" &> /dev/null; then
            echo "Installing Python dependencies from requirements.txt..."
            # Use --break-system-packages with --user (safe on Arch Linux)
            python3 -m pip install --user --break-system-packages -r requirements.txt 2>/dev/null || \
                python3 -m pip install --user -r requirements.txt
            echo -e "${GREEN}✓${NC} Python dependencies installed"
        else
            echo -e "${GREEN}✓${NC} Python dependencies already satisfied"
        fi
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
    sudo install -Dm755 build/forgeworklights /usr/local/bin/forgeworklights
    echo -e "${GREEN}✓${NC} Installed forgeworklights to /usr/local/bin"
    
    # Install root helper with setuid-root (root:root 4755)
    # The setuid bit allows user daemon to execute it with effective root privileges
    sudo install -Dm755 -o root -g root build/fw_root_helper /usr/local/libexec/fw_root_helper
    sudo chmod 4755 /usr/local/libexec/fw_root_helper
    echo -e "${GREEN}✓${NC} Installed root helper to /usr/local/libexec/fw_root_helper (root:root 4755 setuid-root)"
    
    # Install TUI control panel
    if [ -f scripts/options-tui.py ]; then
        sudo install -Dm755 scripts/options-tui.py /usr/local/bin/forgeworklights-menu
        echo -e "${GREEN}✓${NC} Installed TUI control panel to /usr/local/bin"
        
        # Install TUI package module
        if [ -d scripts/tui ]; then
            # Use system site-packages (Arch Linux doesn't use /usr/local for Python)
            TUI_INSTALL_DIR=$(python3 -c "import site; print(site.getsitepackages()[0])")/tui
            sudo mkdir -p "$TUI_INSTALL_DIR"
            sudo cp -r scripts/tui/* "$TUI_INSTALL_DIR/"
            echo -e "${GREEN}✓${NC} Installed TUI package module to $TUI_INSTALL_DIR"
        fi
    fi
    
    # Install theme sync script
    if [ -f scripts/sync-themes.py ]; then
        sudo install -Dm755 scripts/sync-themes.py /usr/local/bin/forgeworklights-sync-themes
        echo -e "${GREEN}✓${NC} Installed theme sync script to /usr/local/bin"
    fi
    
    # Install floating TUI launcher
    if [ -f scripts/launch-tui-floating.sh ]; then
        sudo install -Dm755 scripts/launch-tui-floating.sh /usr/local/bin/forgeworklights-menu-floating
        echo -e "${GREEN}✓${NC} Installed floating TUI launcher to /usr/local/bin"
    fi
    
    # Install sample config
    mkdir -p ~/.config/forgeworklights
    if [ -f ~/.config/forgeworklights/config.toml ]; then
        echo -e "${YELLOW}!${NC} Config already exists, skipping"
    else
        cp config/config.toml.sample ~/.config/forgeworklights/config.toml
        echo -e "${GREEN}✓${NC} Installed config to ~/.config/forgeworklights/config.toml"
    fi

    # Install LED theme database (always update user copy)
    cp config/led_themes.json ~/.config/forgeworklights/led_themes.json
    echo -e "${GREEN}✓${NC} Installed LED theme database to ~/.config/forgeworklights/led_themes.json"

    # Install premade LED themes into shared data directory for TUI sync logic
    sudo install -Dm644 config/led_themes.json /usr/local/share/forgeworklights/led_themes.json
    echo -e "${GREEN}✓${NC} Installed premade LED themes to /usr/local/share/forgeworklights/led_themes.json"
}

# Setup systemd service
setup_systemd() {
    echo ""
    read -p "Install systemd user service (auto-start on login)? [Y/n] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        mkdir -p ~/.config/systemd/user
        cp systemd/forgeworklights.service ~/.config/systemd/user/
        systemctl --user daemon-reload
        echo -e "${GREEN}✓${NC} Systemd service installed"
        
        read -p "Enable service now? [Y/n] " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Nn]$ ]]; then
            systemctl --user enable --now forgeworklights.service
            echo -e "${GREEN}✓${NC} Service enabled and started"
        fi
    fi
}

# Setup waybar integration
setup_waybar() {
    echo ""
    # Check for various waybar config filenames
    local waybar_config=""
    if [ -f ~/.config/waybar/config.jsonc ]; then
        waybar_config=~/.config/waybar/config.jsonc
    elif [ -f ~/.config/waybar/config.json ]; then
        waybar_config=~/.config/waybar/config.json
    elif [ -f ~/.config/waybar/config ]; then
        waybar_config=~/.config/waybar/config
    else
        echo -e "${YELLOW}!${NC} Waybar config not found, skipping integration"
        return
    fi
    
    echo "Found waybar config: $waybar_config"
    
    # Check if already configured
    if grep -q "custom/forgework-lights" "$waybar_config"; then
        echo -e "${YELLOW}!${NC} Waybar module already configured"
        return
    fi
    
    read -p "Add ForgeworkLights module to waybar? [Y/n] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        # Backup config
        cp "$waybar_config" "${waybar_config}.backup"
        echo "Created backup: ${waybar_config}.backup"
        
        # Detect terminal emulator
        TERMINAL=""
        if command -v kitty &> /dev/null; then
            TERMINAL="kitty -e"
        elif command -v alacritty &> /dev/null; then
            TERMINAL="alacritty -e"
        elif command -v foot &> /dev/null; then
            TERMINAL="foot"
        elif command -v wezterm &> /dev/null; then
            TERMINAL="wezterm start --"
        elif command -v gnome-terminal &> /dev/null; then
            TERMINAL="gnome-terminal --"
        else
            echo -e "${YELLOW}!${NC} No terminal emulator found, TUI may not work"
            TERMINAL="xterm -e"
        fi
        
        # Use Python to properly parse and modify JSONC
        python3 << PYEOF
import json
import re
import sys
import os

config_file = "$waybar_config"
terminal_cmd = "$TERMINAL"

try:
    with open(config_file, 'r') as f:
        content = f.read()
    
    # Strip // comments for JSON parsing
    lines = content.split('\n')
    clean_lines = [re.sub(r'//.*$', '', line) for line in lines]
    clean_content = '\n'.join(clean_lines)
    
    # Remove trailing commas (JSONC allows them, JSON doesn't)
    clean_content = re.sub(r',(\s*[}\]])', r'\1', clean_content)
    
    config = json.loads(clean_content)
    
    config["custom/forgework-lights"] = {
        "format": " 󰛨 ",
        "tooltip-format": "Lights: {}",
        "exec": 'jq -r '"'"'.theme // "Off"'"'"' ~/.cache/forgeworklights/state.json 2>/dev/null || echo "Off"',
        "interval": 2,
        "on-click": "/usr/local/bin/forgeworklights-menu-floating"
    }
    
    # Add to tray-expander group if it exists, otherwise modules-right
    if "group/tray-expander" in config and "modules" in config["group/tray-expander"]:
        modules = config["group/tray-expander"]["modules"]
        if "custom/forgework-lights" not in modules:
            # Add before "tray" if it exists
            if "tray" in modules:
                idx = modules.index("tray")
                modules.insert(idx, "custom/forgework-lights")
            else:
                modules.append("custom/forgework-lights")
        config["group/tray-expander"]["modules"] = modules
        print("ADDED_TO_GROUP")
    elif "modules-right" in config and isinstance(config["modules-right"], list):
        if "custom/forgework-lights" not in config["modules-right"]:
            config["modules-right"].insert(0, "custom/forgework-lights")
        print("ADDED_TO_MODULES_RIGHT")
    
    # Write back
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    print("SUCCESS")
except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)
PYEOF
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓${NC} Waybar module added"
            
            # Add CSS styling
            if [ -f ~/.config/waybar/style.css ]; then
                if ! grep -q "custom-forgework-lights" ~/.config/waybar/style.css; then
                    # Append CSS from waybar/forgework-lights.css (single source of truth)
                    if [ -f "waybar/forgework-lights.css" ]; then
                        cat waybar/forgework-lights.css >> ~/.config/waybar/style.css
                        echo -e "${GREEN}✓${NC} Added CSS styling from waybar/forgework-lights.css"
                    else
                        echo -e "${YELLOW}!${NC} waybar/forgework-lights.css not found, skipping CSS"
                    fi
                fi
            fi
            
            # Reload waybar
            if pgrep waybar > /dev/null; then
                echo "Reloading waybar..."
                killall -SIGUSR2 waybar 2>/dev/null || true
            fi
        else
            echo -e "${RED}✗${NC} Failed to configure waybar"
            echo "You can manually add the module - see waybar/README.md"
        fi
    fi
}

# Setup Hyprland window rules
setup_hyprland() {
    echo ""
    
    # Check if Hyprland is installed
    if ! command -v hyprctl &> /dev/null; then
        echo -e "${YELLOW}!${NC} Hyprland not detected, skipping window rules"
        return
    fi
    
    local hypr_config="$HOME/.config/hypr/hyprland.conf"
    
    if [ ! -f "$hypr_config" ]; then
        echo -e "${YELLOW}!${NC} Hyprland config not found at $hypr_config"
        return
    fi
    
    # Check if float rule already exists (more specific check)
    if grep -q "^windowrulev2 = float.*forgework-lights-tui" "$hypr_config"; then
        echo -e "${YELLOW}!${NC} Hyprland window rules already configured"
        return
    fi
    
    read -p "Add Hyprland window rules for floating TUI? [Y/n] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        # Backup config
        cp "$hypr_config" "${hypr_config}.backup"
        echo "Created backup: ${hypr_config}.backup"
        
        # Append window rules from hyprland-rules.conf (single source of truth)
        echo "" >> "$hypr_config"
        if [ -f "hyprland-rules.conf" ]; then
            cat hyprland-rules.conf >> "$hypr_config"
        elif [ -f "${BASH_SOURCE%/*}/hyprland-rules.conf" ]; then
            cat "${BASH_SOURCE%/*}/hyprland-rules.conf" >> "$hypr_config"
        else
            echo -e "${RED}✗${NC} hyprland-rules.conf not found"
            return 1
        fi
        
        echo -e "${GREEN}✓${NC} Added Hyprland window rules from hyprland-rules.conf"
        echo -e "${GREEN}✓${NC} TUI will now open as floating window in top right corner"
        
        # Reload Hyprland config
        hyprctl reload &>/dev/null && echo -e "${GREEN}✓${NC} Reloaded Hyprland config" || true
    fi
}

# Check the installation
check_installation() {
    echo ""
    echo "Checking installation..."
    
    # Cck if binary exists and is executable
    if [ -x /usr/local/bin/forgeworklights ]; then
        echo -e "${GREEN}✓${NC} forgeworklights executable installed"
    else
        echo -e "${RED}✗${NC} forgeworklights not found or not executable"
        return 1
    fi
    
    # Check root helper
    if [ -f /usr/local/libexec/fw_root_helper ]; then
        local perms=$(stat -c '%a' /usr/local/libexec/fw_root_helper)
        if [ "$perms" = "4755" ]; then
            echo -e "${GREEN}✓${NC} root helper installed with correct permissions (4755)"
        else
            echo -e "${YELLOW}!${NC} root helper has incorrect permissions ($perms, should be 4755)"
        fi
    else
        echo -e "${RED}✗${NC} root helper not found at /usr/local/libexec/fw_root_helper"
    fi
}

# Main installation flow
main() {
    check_framework_desktop
    pause_step
    check_dependencies
    pause_step
    install_optional_deps
    pause_step
    build_project
    pause_step
    install_binaries
    pause_step
    setup_systemd
    pause_step
    setup_waybar
    pause_step
    setup_walker_launcher
    pause_step
    setup_hyprland
    pause_step
    setup_hyprland_shortcuts
    pause_step
    
    echo ""
    echo "========================================"
    echo -e "${GREEN}Installation complete!${NC}"
    echo "========================================"
    echo ""
    echo "Quick start:"
    echo "  Test: forgeworklights once"
    echo "  Run:  forgeworklights daemon"
    echo "  or:   systemctl --user start forgeworklights"
    echo ""
    echo "Config: ~/.config/forgeworklights/config.toml"
    echo ""
    
    check_installation
    pause_step

    if [ "$SHORTCUTS_INSTALLED" -eq 1 ]; then
        echo ""
        echo "Hyprland keyboard shortcuts installed (Super+Alt combos):"
        echo "  ↑  Increase brightness (+5%)"
        echo "  ↓  Decrease brightness (-5%)"
        echo "  0  Turn LEDs off"
        echo "  →  Next animation"
        echo "  ←  Previous animation"
        echo "Edit: ~/.config/forgeworklights/hyprland-bindings.conf"
    fi
}

main "$@"
