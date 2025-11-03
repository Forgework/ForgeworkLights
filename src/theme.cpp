#include "theme.hpp"
#include <filesystem>
#include <unistd.h>
#include <limits.h>
 #include <pwd.h>
 #include <sys/types.h>

namespace fs = std::filesystem;

namespace omarchy {

static std::string config_base() {
  const char* xdg = std::getenv("XDG_CONFIG_HOME");
  if (xdg && *xdg) return std::string(xdg);
  auto make_base = [](const char* home){ return std::string(home ? home : "/") + "/.config"; };
  // If running as root but SUDO_USER is set, use that user's home
  if (geteuid() == 0) {
    const char* sudo_user = std::getenv("SUDO_USER");
    if (sudo_user && *sudo_user) {
      struct passwd* pw = ::getpwnam(sudo_user);
      if (pw && pw->pw_dir) return make_base(pw->pw_dir);
    }
  }
  const char* h = std::getenv("HOME");
  return make_base(h);
}

std::optional<ThemePaths> resolve_theme() {
  std::string symlink = config_base() + "/omarchy/current/theme";
  char buf[PATH_MAX];
  ssize_t n = ::readlink(symlink.c_str(), buf, sizeof(buf)-1);
  if (n < 0) return std::nullopt;
  buf[n] = '\0';
  fs::path theme_dir = fs::weakly_canonical(fs::path(buf));
  ThemePaths t{ symlink, theme_dir.string(), std::nullopt };
  // Look for palette files in preference order
  const char* files[] = {"palette.json", "theme.json", "palette.toml"};
  for (auto f : files) {
    fs::path p = theme_dir / f;
    if (fs::exists(p)) { t.palette_file = p.string(); break; }
  }
  return t;
}

}
