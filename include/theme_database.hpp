#pragma once
#include "color.hpp"
#include <string>
#include <vector>
#include <optional>
#include <unordered_map>

namespace omarchy {

struct ThemeColors {
  std::string name;
  std::vector<RGB> colors; // 5 colors defining the gradient
};

class ThemeDatabase {
public:
  // Load database from JSON file
  bool load(const std::string& path);
  
  // Get colors for a theme (returns nullopt if not found)
  std::optional<ThemeColors> get(const std::string& theme_name) const;
  
  // Save custom colors for a theme
  bool save_custom(const std::string& theme_name, const std::vector<RGB>& colors);
  
  // Get all theme names
  std::vector<std::string> list_themes() const;

private:
  std::unordered_map<std::string, ThemeColors> themes_;
  std::string db_path_;
};

} // namespace omarchy
