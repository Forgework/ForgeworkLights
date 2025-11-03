#pragma once
#include <string>
#include <optional>

namespace omarchy {

struct ThemePaths {
  std::string symlink_path;
  std::string theme_dir;
  std::optional<std::string> palette_file;
};

std::optional<ThemePaths> resolve_theme();

}
