#!/bin/bash

# ForgeworkLights Uninstall Script

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

SHORT_DELAY=0.05
pause_step() {
    sleep "$SHORT_DELAY"
}

declare -a BACKUP_PATHS=()
register_backup() {
    BACKUP_PATHS+=("$1")
}
BACKUPS_REMOVED=false

echo "========================================"
echo "  ForgeworkLights Uninstall"
echo "========================================"
echo ""

# Stop service first to prevent it from turning LEDs back on
if systemctl --user is-active forgeworklights.service &> /dev/null; then
    echo "Stopping service..."
    systemctl --user stop forgeworklights.service
    systemctl --user disable forgeworklights.service
    echo -e "${GREEN}✓${NC} Service stopped and disabled"
    pause_step
fi

# Turn off all 22 LEDs using root helper
echo "Turning off LEDs..."
if [ -f /usr/local/libexec/fw_root_helper ]; then
    # 22 LEDs * 3 bytes = 66 bytes = 132 hex chars of zeros
    if sudo /usr/local/libexec/fw_root_helper 000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000 2>/dev/null; then
        echo -e "${GREEN}✓${NC} All 22 LEDs turned off (via root helper)"
    else
        echo -e "${YELLOW}!${NC} Root helper failed, trying framework_tool directly..."
        # Fallback to direct framework_tool call
        if command -v framework_tool &> /dev/null; then
            sudo framework_tool --rgbkbd 0 $(printf '0x000000 %.0s' {1..22}) &> /dev/null || true
            echo -e "${GREEN}✓${NC} All 22 LEDs turned off (via framework_tool)"
        else
            echo -e "${YELLOW}!${NC} Could not turn off LEDs (no framework_tool found)"
        fi
    fi
else
    echo -e "${YELLOW}!${NC} Root helper not found, trying framework_tool directly..."
    if command -v framework_tool &> /dev/null; then
        sudo framework_tool --rgbkbd 0 $(printf '0x000000 %.0s' {1..22}) &> /dev/null || true
        echo -e "${GREEN}✓${NC} All 22 LEDs turned off (via framework_tool)"
    else
        echo -e "${YELLOW}!${NC} Could not turn off LEDs (framework_tool not found)"
    fi
fi

# Remove systemd service
if [ -f ~/.config/systemd/user/forgeworklights.service ]; then
    rm ~/.config/systemd/user/forgeworklights.service
    systemctl --user daemon-reload
    echo -e "${GREEN}✓${NC} Systemd service removed"
    pause_step
fi

# Remove binaries
if [ -f /usr/local/bin/forgeworklights ]; then
    sudo rm /usr/local/bin/forgeworklights
    echo -e "${GREEN}✓${NC} Removed /usr/local/bin/forgeworklights"
    pause_step
fi

if [ -f /usr/local/bin/forgeworklights-menu ]; then
    sudo rm /usr/local/bin/forgeworklights-menu
    echo -e "${GREEN}✓${NC} Removed /usr/local/bin/forgeworklights-menu"
    pause_step
fi

if [ -f /usr/local/bin/forgeworklights-sync-themes ]; then
    sudo rm /usr/local/bin/forgeworklights-sync-themes
    echo -e "${GREEN}✓${NC} Removed /usr/local/bin/forgeworklights-sync-themes"
    pause_step
fi

if [ -f /usr/local/bin/forgeworklights-menu-floating ]; then
    sudo rm /usr/local/bin/forgeworklights-menu-floating
    echo -e "${GREEN}✓${NC} Removed /usr/local/bin/forgeworklights-menu-floating"
    pause_step
fi

# Remove Walker launcher script and desktop entry
launcher_script="$HOME/.local/bin/forgeworklights.sh"
desktop_entry="$HOME/.local/share/applications/forgeworklights.desktop"
icon_path="$HOME/.local/share/icons/forgeworklights.png"

if [ -f "$launcher_script" ]; then
    rm "$launcher_script"
    echo -e "${GREEN}✓${NC} Removed Walker launcher script ($launcher_script)"
    pause_step
fi

if [ -f "$desktop_entry" ]; then
    rm "$desktop_entry"
    echo -e "${GREEN}✓${NC} Removed desktop entry ($desktop_entry)"
    pause_step
fi

if [ -f "$icon_path" ]; then
    rm "$icon_path"
    echo -e "${GREEN}✓${NC} Removed launcher icon ($icon_path)"
    pause_step
fi

if command -v update-desktop-database &> /dev/null; then
    update-desktop-database "$HOME/.local/share/applications" >/dev/null 2>&1 || true
    pause_step
fi

# Remove root helper
if [ -f /usr/local/libexec/fw_root_helper ]; then
    sudo rm /usr/local/libexec/fw_root_helper
    echo -e "${GREEN}✓${NC} Removed /usr/local/libexec/fw_root_helper"
    pause_step
fi

# Remove TUI package module
if command -v python3 &> /dev/null; then
    TUI_INSTALL_DIR=$(python3 -c "import site; print(site.getsitepackages()[0])" 2>/dev/null)/tui
    if [ -d "$TUI_INSTALL_DIR" ]; then
        sudo rm -rf "$TUI_INSTALL_DIR"
        echo -e "${GREEN}✓${NC} Removed TUI package module from $TUI_INSTALL_DIR"
        pause_step
    fi
    # Also check old location for backwards compatibility
    for py_path in /usr/local/lib/python*/site-packages/tui; do
        if [ -d "$py_path" ]; then
            sudo rm -rf "$py_path"
            echo -e "${GREEN}✓${NC} Removed old TUI package from $py_path"
            pause_step
        fi
    done
    
    # Clean up Python cache directories comprehensively
    SITE_PACKAGES=$(python3 -c "import site; print(site.getsitepackages()[0])" 2>/dev/null)
    if [ -n "$SITE_PACKAGES" ]; then
        # Remove tui-related __pycache__ directories and .pyc files
        find "$SITE_PACKAGES" -type d -name "__pycache__" -path "*tui*" -exec sudo rm -rf {} + 2>/dev/null || true
        find "$SITE_PACKAGES" -name "*.pyc" -path "*tui*" -delete 2>/dev/null || true
        find "$SITE_PACKAGES" -name "*.pyo" -path "*tui*" -delete 2>/dev/null || true
        
        # Also clean any forgeworklights-related cache
        find "$SITE_PACKAGES" -type d -name "__pycache__" -path "*forgeworklights*" -exec sudo rm -rf {} + 2>/dev/null || true
        find "$SITE_PACKAGES" -name "*.pyc" -path "*forgeworklights*" -delete 2>/dev/null || true
        find "$SITE_PACKAGES" -name "*.pyo" -path "*forgeworklights*" -delete 2>/dev/null || true
        
        echo -e "${GREEN}✓${NC} Cleaned Python cache"
        pause_step
    fi
    
    # Clean user-level Python cache
    if [ -d ~/.cache ]; then
        # Remove forgeworklights-related cache from user cache
        find ~/.cache -type d -name "__pycache__" -path "*forgeworklights*" -exec rm -rf {} + 2>/dev/null || true
        find ~/.cache -name "*.pyc" -path "*forgeworklights*" -delete 2>/dev/null || true
        find ~/.cache -name "*.pyo" -path "*forgeworklights*" -delete 2>/dev/null || true
        
        # Remove any tui-related cache from user cache
        find ~/.cache -type d -name "__pycache__" -path "*tui*" -exec rm -rf {} + 2>/dev/null || true
        find ~/.cache -name "*.pyc" -path "*tui*" -delete 2>/dev/null || true
        find ~/.cache -name "*.pyo" -path "*tui*" -delete 2>/dev/null || true
        
        echo -e "${GREEN}✓${NC} Cleaned user Python cache"
        pause_step
    fi
    
    # Clean any remaining Python bytecode cache
    if [ -d /tmp ]; then
        find /tmp -name "*forgeworklights*" -type d -exec rm -rf {} + 2>/dev/null || true
        find /tmp -name "*tui*" -type d -exec rm -rf {} + 2>/dev/null || true
    fi
    pause_step
fi

# Ask about config
echo ""
read -p "Remove configuration (~/.config/forgeworklights)? [Y/n] " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    rm -rf ~/.config/forgeworklights
    echo -e "${GREEN}✓${NC} Configuration removed"
    pause_step
fi

# Ask about cache
read -p "Remove cache (~/.cache/forgeworklights)? [Y/n] " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    rm -rf ~/.cache/forgeworklights
    echo -e "${GREEN}✓${NC} Cache removed"
    pause_step
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
        register_backup "${waybar_config}.uninstall-backup"
        
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
        pause_step
        
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
            pause_step
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
            register_backup "${hypr_config}.uninstall-backup"
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
            pause_step
            
            # Reload Hyprland config
            if command -v hyprctl &> /dev/null; then
                hyprctl reload &>/dev/null && echo -e "${GREEN}✓${NC} Reloaded Hyprland config" || true
                pause_step
            fi
        else
            echo -e "${YELLOW}!${NC} No Hyprland window rules found"
            pause_step
        fi
    else
        echo -e "${YELLOW}!${NC} Hyprland config not found"
        pause_step
    fi
fi

# Offer to delete backups if any were created
if [ ${#BACKUP_PATHS[@]} -gt 0 ]; then
    echo ""
    echo "Backups created during uninstall:"
    for backup in "${BACKUP_PATHS[@]}"; do
        echo "  - $backup"
    done
    read -p "Delete these backups now? [y/N] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        for backup in "${BACKUP_PATHS[@]}"; do
            rm -f "$backup"
        done
        echo -e "${GREEN}✓${NC} Backups removed"
        BACKUPS_REMOVED=true
    else
        echo -e "${YELLOW}!${NC} Backups kept at the locations above"
    fi
    pause_step
fi

echo ""
echo -e "${GREEN}Uninstall complete${NC}"
echo ""
echo "Files removed:"
echo "  - /usr/local/bin/forgeworklights"
echo "  - /usr/local/bin/forgeworklights-menu"
echo "  - /usr/local/bin/forgeworklights-sync-themes"
echo "  - /usr/local/bin/forgeworklights-menu-floating"
echo "  - /usr/local/libexec/fw_root_helper"
echo "  - ~/.config/systemd/user/forgeworklights.service"
echo ""
if [ ${#BACKUP_PATHS[@]} -gt 0 ]; then
    if [ "$BACKUPS_REMOVED" = true ]; then
        echo "Backups were deleted during this uninstall run."
    else
        echo "Backups created (if modified):"
        echo "  - ~/.config/waybar/config.*.uninstall-backup"
        echo "  - ~/.config/hypr/hyprland.conf.uninstall-backup"
    fi
else
    echo "No backups were created."
fi
