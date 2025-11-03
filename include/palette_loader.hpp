#pragma once
#include <optional>
#include <string>
#include "palette.hpp"

namespace omarchy {

// Load palette from a chosen palette file. Currently supports simple JSON with keys:
// accent, accent2, accent3 as "#RRGGBB" (for 3-color gradient).
std::optional<Palette> load_palette_from_file(const std::string& path);

// Parse a hex color string like #RRGGBB
bool parse_hex_rgb(const std::string& s, RGB& out);

// Load palette from btop.theme file (temperature gradient colors)
std::optional<Palette> load_palette_from_btop(const std::string& path);

// Try to load a palette from a theme directory by priority:
// btop.theme (primary) -> palette.json -> theme.json
std::optional<Palette> load_palette_from_theme_dir(const std::string& dir);

}
