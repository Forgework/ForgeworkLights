#include "theme_database.hpp"
#include <fstream>
#include <sstream>
#include <algorithm>
#include <cstdio>
#include <cstring>

namespace forgeworklights {

// Simple JSON parsing for our specific format
static std::string trim(const std::string& str) {
  auto start = str.find_first_not_of(" \t\n\r");
  if (start == std::string::npos) return "";
  auto end = str.find_last_not_of(" \t\n\r");
  return str.substr(start, end - start + 1);
}

static std::string unquote(const std::string& str) {
  std::string s = trim(str);
  if (s.size() >= 2 && s.front() == '"' && s.back() == '"') {
    return s.substr(1, s.size() - 2);
  }
  return s;
}

static RGB parse_hex_color(const std::string& hex) {
  RGB c{0, 0, 0};
  std::string h = hex;
  if (h[0] == '#') h = h.substr(1);
  if (h.length() == 6) {
    unsigned int val;
    if (std::sscanf(h.c_str(), "%x", &val) == 1) {
      c.r = (val >> 16) & 0xFF;
      c.g = (val >> 8) & 0xFF;
      c.b = val & 0xFF;
    }
  }
  return c;
}

bool ThemeDatabase::load(const std::string& path) {
  db_path_ = path;
  themes_.clear();
  
  std::ifstream file(path);
  if (!file.good()) return false;
  
  std::string line;
  std::string current_theme;
  std::vector<RGB> current_colors;
  std::string current_name;
  
  while (std::getline(file, line)) {
    line = trim(line);
    
    // Look for theme key (but skip root "themes" object)
    if (line.find("\"") != std::string::npos && line.find(":") != std::string::npos && 
        line.find("{") != std::string::npos) {
      // Extract theme name first
      auto quote1 = line.find('"');
      auto quote2 = line.find('"', quote1 + 1);
      if (quote1 != std::string::npos && quote2 != std::string::npos) {
        std::string theme_key = line.substr(quote1 + 1, quote2 - quote1 - 1);
        
        // Skip the root "themes" object
        if (theme_key == "themes") continue;
        
        // Save previous theme if any
        if (!current_theme.empty() && !current_colors.empty()) {
          themes_[current_theme] = ThemeColors{current_name, current_colors};
        }
        
        current_theme = theme_key;
        current_colors.clear();
        current_name.clear();
      }
    }
    // Look for "name" field
    else if (line.find("\"name\"") != std::string::npos) {
      auto colon = line.find(':');
      if (colon != std::string::npos) {
        auto value = line.substr(colon + 1);
        // Remove trailing comma if present
        auto comma = value.find(',');
        if (comma != std::string::npos) value = value.substr(0, comma);
        current_name = unquote(value);
      }
    }
    // Look for "colors" array
    else if (line.find("\"colors\"") != std::string::npos) {
      auto bracket = line.find('[');
      if (bracket != std::string::npos) {
        // Colors on same line
        auto closing = line.find(']', bracket);
        if (closing != std::string::npos) {
          std::string colors_str = line.substr(bracket + 1, closing - bracket - 1);
          
          // Parse individual colors
          size_t pos = 0;
          while (pos < colors_str.length()) {
            auto quote1 = colors_str.find('"', pos);
            if (quote1 == std::string::npos) break;
            auto quote2 = colors_str.find('"', quote1 + 1);
            if (quote2 == std::string::npos) break;
            
            std::string color_hex = colors_str.substr(quote1 + 1, quote2 - quote1 - 1);
            current_colors.push_back(parse_hex_color(color_hex));
            pos = quote2 + 1;
          }
        }
      }
    }
    // Look for color values in multi-line arrays
    else if (line.find('"') != std::string::npos && line.find('#') != std::string::npos) {
      // Extract hex color from quoted string
      auto quote1 = line.find('"');
      auto quote2 = line.find('"', quote1 + 1);
      if (quote1 != std::string::npos && quote2 != std::string::npos) {
        std::string color_str = line.substr(quote1 + 1, quote2 - quote1 - 1);
        if (color_str.length() > 0 && color_str[0] == '#') {
          current_colors.push_back(parse_hex_color(color_str));
        }
      }
    }
  }
  
  // Save last theme
  if (!current_theme.empty() && !current_colors.empty()) {
    themes_[current_theme] = ThemeColors{current_name, current_colors};
  }
  
  return !themes_.empty();
}

std::optional<ThemeColors> ThemeDatabase::get(const std::string& theme_name) const {
  auto it = themes_.find(theme_name);
  if (it != themes_.end()) {
    return it->second;
  }
  return std::nullopt;
}

bool ThemeDatabase::save_custom(const std::string& theme_name, const std::vector<RGB>& colors) {
  if (colors.size() < 3) return false;
  
  // Update in-memory
  themes_[theme_name] = ThemeColors{theme_name, colors};
  
  // TODO: Write back to JSON file (for now just keep in memory)
  // This would require proper JSON serialization
  
  return true;
}

std::vector<std::string> ThemeDatabase::list_themes() const {
  std::vector<std::string> names;
  names.reserve(themes_.size());
  for (const auto& pair : themes_) {
    names.push_back(pair.first);
  }
  std::sort(names.begin(), names.end());
  return names;
}

} // namespace forgeworklights
