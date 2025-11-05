#include "argb_daemon.hpp"
#include "framework_tool.hpp"
#include "theme.hpp"
#include "palette_loader.hpp"
#include "color_utils.hpp"
#include "theme_database.hpp"
#include <sys/inotify.h>
#include <unistd.h>
#include <vector>
#include <string>
#include <chrono>
#include <thread>
#include <filesystem>
#include <optional>
#include <cstring>
#include <fstream>
#include <cstdio>
#include <pwd.h>
#include <sys/types.h>
 #include <cmath>

namespace omarchy {

ARGBDaemon::ARGBDaemon(const Config& cfg) : cfg_(cfg) {}

int ARGBDaemon::run() {
  int fd = inotify_init1(IN_NONBLOCK | IN_CLOEXEC);
  if (fd < 0) return 2;
  // Resolve config base: XDG_CONFIG_HOME, else (if root and SUDO_USER set) that user's ~/.config, else HOME/.config
  auto config_base = [](){
    auto make_base = [](const char* home){ return std::string(home ? home : "/") + "/.config"; };
    if (geteuid() == 0) {
      const char* sudo_user = std::getenv("SUDO_USER");
      if (sudo_user && *sudo_user) {
        if (struct passwd* pw = ::getpwnam(sudo_user)) {
          if (pw->pw_dir) return make_base(pw->pw_dir);
        }
      }
    }
    const char* xdg = std::getenv("XDG_CONFIG_HOME");
    if (xdg && *xdg) return std::string(xdg);
    const char* h = std::getenv("HOME");
    return make_base(h);
  };

  FrameworkTool tool(cfg_.tool_path);
  Gamma gamma(cfg_.gamma_exponent);
  auto log = [](const std::string& s){ std::fprintf(stderr, "[omarchy-argb] %s\n", s.c_str()); };

  // State
  int wd_current = -1;
  int wd_palette_dir = -1;
  int wd_brightness_dir = -1;
  int wd_themes_db = -1;
  std::string current_dir;
  std::optional<ThemePaths> theme;
  std::optional<Palette> palette;
  std::string palette_path;
  std::string palette_dir;
  std::vector<RGB> prev_frame;
  prev_frame.reserve(cfg_.led_count);
  auto last_send = std::chrono::steady_clock::now() - std::chrono::milliseconds(1000);

  auto add_watch = [&](const std::string& p){
    return inotify_add_watch(fd, p.c_str(), IN_ATTRIB | IN_CLOSE_WRITE | IN_MOVE_SELF | IN_DELETE_SELF | IN_CREATE | IN_DELETE | IN_MOVED_TO | IN_MOVED_FROM);
  };

  current_dir = config_base() + "/omarchy/current";
  if (wd_current < 0) {
    wd_current = add_watch(current_dir);
    log(std::string("watching dir: ") + current_dir);
  }

  // Watch brightness file
  std::string brightness_dir = config_base() + "/omarchy-argb";
  std::filesystem::create_directories(brightness_dir);
  wd_brightness_dir = add_watch(brightness_dir);
  log(std::string("watching brightness dir: ") + brightness_dir);

  auto read_led_theme_preference = [&]() -> std::string {
    // Read LED theme preference from config file
    std::string pref_file = config_base() + "/omarchy-argb/led-theme";
    std::ifstream in(pref_file);
    if (!in.good()) return "match";  // Default to matching Omarchy theme
    std::string pref;
    std::getline(in, pref);
    // Trim whitespace
    pref.erase(0, pref.find_first_not_of(" \t\n\r"));
    pref.erase(pref.find_last_not_of(" \t\n\r") + 1);
    return pref.empty() ? "match" : pref;
  };

  auto load_theme = [&](){
    std::string led_theme_pref = read_led_theme_preference();
    log(std::string("LED theme preference: ") + led_theme_pref);
    
    if (led_theme_pref == "match") {
      // Match Omarchy theme via symlink
      theme = resolve_theme();
      if (!theme) { log("resolve_theme: none"); return; }
      log(std::string("theme dir: ") + theme->theme_dir);
      // Always watch the theme directory for any palette source changes
      palette_dir = theme->theme_dir;
      if (wd_palette_dir >= 0) { inotify_rm_watch(fd, wd_palette_dir); wd_palette_dir = -1; }
      wd_palette_dir = add_watch(palette_dir);
      log(std::string("watching palette dir: ") + palette_dir);
      // Try loading via priority list from the theme directory
      if (theme->palette_file)
        palette_path = *theme->palette_file; else palette_path.clear();
      palette = load_palette_from_theme_dir(palette_dir);
      if (palette) {
        log("palette loaded from theme directory");
      } else {
        log("no palette could be parsed from theme directory");
      }
    } else {
      // Use specific LED theme from database - don't follow Omarchy symlink
      log(std::string("Using LED-specific theme: ") + led_theme_pref);
      // Theme database is already loaded, colors will be retrieved in compose()
      // Clear palette so compose() uses database colors
      palette = std::nullopt;
      theme = std::nullopt;
    }
  };

  auto read_brightness = [&](){
    std::string p = config_base() + "/omarchy-argb/brightness";
    std::ifstream in(p);
    if (!in.good()) return cfg_.max_brightness;
    double v = cfg_.max_brightness;
    in >> v;
    if (v < 0.0) v = 0.0; if (v > 1.0) v = 1.0;
    return v;
  };

  auto write_state = [&](const std::vector<RGB>& leds){
    const char* h = std::getenv("HOME");
    std::string cache_dir = std::string(h?h:"/") + "/.cache/omarchy-argb";
    std::filesystem::create_directories(cache_dir);
    std::string state_path = cache_dir + "/state.json";
    std::ofstream out(state_path);
    if (!out.good()) return;
    out << "{\n";
    out << "  \"theme\": \"" << (theme ? std::filesystem::path(theme->theme_dir).filename().string() : "none") << "\",\n";
    out << "  \"colors\": [\n";
    for (size_t i = 0; i < leds.size(); ++i) {
      char buf[16]; std::snprintf(buf, sizeof(buf), "#%02X%02X%02X", leds[i].r, leds[i].g, leds[i].b);
      out << "    \"" << buf << "\"";
      if (i + 1 < leds.size()) out << ",";
      out << "\n";
    }
    out << "  ]\n";
    out << "}\n";
  };

  // Sync themes from Omarchy directory on startup
  log("syncing themes from omarchy directory...");
  int sync_rc = std::system("python3 /usr/local/bin/omarchy-argb-sync-themes 2>/dev/null");
  if (sync_rc == 0) {
    log("theme sync completed");
  } else {
    log("theme sync failed or no changes");
  }

  // Load theme database
  ThemeDatabase theme_db;
  const char* home = std::getenv("HOME");
  std::string db_path = std::string(home ? home : "/") + "/.config/omarchy-argb/themes.json";
  std::string db_dir;
  if (!theme_db.load(db_path)) {
    // Try system-wide location
    db_path = "/usr/local/share/omarchy-argb/themes.json";
    theme_db.load(db_path);
  }
  
  // Watch the themes database directory for changes
  db_dir = std::filesystem::path(db_path).parent_path().string();
  wd_themes_db = add_watch(db_dir);
  log(std::string("watching themes database dir: ") + db_dir);
  
  auto reload_theme_database = [&]() {
    auto themes = theme_db.list_themes();
    log(std::string("Reloading theme database from: ") + db_path);
    if (theme_db.load(db_path)) {
      auto new_themes = theme_db.list_themes();
      log(std::string("Reloaded ") + std::to_string(new_themes.size()) + " themes from database");
    } else {
      log("Failed to reload theme database");
    }
  };
  
  // Debug: log loaded themes
  {
    auto themes = theme_db.list_themes();
    log(std::string("Loaded ") + std::to_string(themes.size()) + " themes from database");
    for (const auto& t : themes) {
      log(std::string("  - ") + t);
    }
  }

  auto compose = [&](){
    std::vector<RGB> leds(cfg_.led_count);
    
    // Try to get colors from database first
    std::optional<ThemeColors> db_colors;
    std::string led_theme_pref = read_led_theme_preference();
    
    if (led_theme_pref != "match") {
      // Use LED-specific theme from database
      db_colors = theme_db.get(led_theme_pref);
      if (db_colors) {
        log(std::string("Using LED theme from database: ") + led_theme_pref + 
            " with " + std::to_string(db_colors->colors.size()) + " colors");
      } else {
        log(std::string("Failed to load LED theme from database: ") + led_theme_pref);
      }
    } else if (theme) {
      // Match Omarchy theme
      std::string theme_name = std::filesystem::path(theme->theme_dir).filename().string();
      db_colors = theme_db.get(theme_name);
    }
    
    if (db_colors && db_colors->colors.size() >= 3) {
      // Use curated database colors (5-color gradient for smooth transitions)
      const auto& colors = db_colors->colors;
      int num_colors = colors.size();
      
      for (int i = 0; i < cfg_.led_count; ++i) {
        // Map LED position to color gradient
        double pos = (double)i / (double)(cfg_.led_count - 1);  // 0.0 to 1.0
        double color_pos = pos * (num_colors - 1);  // 0.0 to (num_colors-1)
        
        int idx = (int)color_pos;
        double frac = color_pos - idx;
        
        if (idx >= num_colors - 1) {
          // Last color
          leds[i] = colors[num_colors - 1];
        } else {
          // Interpolate between idx and idx+1
          const RGB& c1 = colors[idx];
          const RGB& c2 = colors[idx + 1];
          RGB c;
          c.r = (uint8_t)std::round(c1.r + (c2.r - c1.r) * frac);
          c.g = (uint8_t)std::round(c1.g + (c2.g - c1.g) * frac);
          c.b = (uint8_t)std::round(c1.b + (c2.b - c1.b) * frac);
          leds[i] = c;
        }
      }
    } else if (palette) {
      // Fallback: Use BTOP 3-color gradient
      int mid_idx = cfg_.led_count / 2;
      for (int i = 0; i < cfg_.led_count; ++i) {
        RGB c;
        if (i <= mid_idx) {
          // First half: interpolate between accent and accent2
          double t = mid_idx == 0 ? 0.0 : (double)i / (double)mid_idx;
          c.r = (uint8_t)std::round(palette->accent.r + (palette->accent2.r - palette->accent.r) * t);
          c.g = (uint8_t)std::round(palette->accent.g + (palette->accent2.g - palette->accent.g) * t);
          c.b = (uint8_t)std::round(palette->accent.b + (palette->accent2.b - palette->accent.b) * t);
        } else {
          // Second half: interpolate between accent2 and accent3
          double t = (double)(i - mid_idx) / (double)(cfg_.led_count - 1 - mid_idx);
          c.r = (uint8_t)std::round(palette->accent2.r + (palette->accent3.r - palette->accent2.r) * t);
          c.g = (uint8_t)std::round(palette->accent2.g + (palette->accent3.g - palette->accent2.g) * t);
          c.b = (uint8_t)std::round(palette->accent2.b + (palette->accent3.b - palette->accent2.b) * t);
        }
        leds[i] = c;
      }
    } else {
      // No palette or database: use fallback rainbow pattern
      for (int i=0;i<cfg_.led_count;++i) {
        RGB c{}; c.r = (uint8_t)((i*7)%256); c.g = (uint8_t)((i*19)%256); c.b=(uint8_t)((i*37)%256);
        leds[i]=c;
      }
    }
    double brightness = read_brightness();
    apply_gamma_brightness(leds, gamma, brightness);
    // enforce_current_cap(leds, cfg_.max_current_amps);  // Disabled - send raw colors
    return leds;
  };

  // Initial resolve and send
  load_theme();
  auto leds = compose();
  tool.sendFrame(0, leds, cfg_.color_order);
  write_state(leds);
  if (!leds.empty()) {
    auto c = leds[0];
    char bufc[16]; std::snprintf(bufc, sizeof(bufc), "#%02X%02X%02X", c.r, c.g, c.b);
    log(std::string("sent initial frame, first LED ") + bufc);
  }
  prev_frame = leds;

  // Event loop
  char buf[4096];
  for(;;){
    bool need_update = false;
    bool theme_changed = false;

    ssize_t n = read(fd, buf, sizeof(buf));
    if (n > 0) {
      ssize_t i = 0;
      while (i < n) {
        struct inotify_event* ev = reinterpret_cast<struct inotify_event*>(buf + i);
        if (ev->wd == wd_current) {
          if (ev->len > 0 && std::string(ev->name) == "theme") {
            log("event: theme symlink changed");
            theme_changed = true;
          }
        } else if (ev->wd == wd_palette_dir) {
          if (ev->len > 0) {
            std::string nm(ev->name);
            if (nm == "btop.theme" || nm == "palette.json" || nm == "theme.json") {
              log(std::string("event: palette source changed: ") + nm);
              need_update = true;
            }
          }
        } else if (ev->wd == wd_brightness_dir) {
          if (ev->len > 0) {
            std::string nm(ev->name);
            if (nm == "brightness") {
              log("event: brightness changed");
              need_update = true;
            } else if (nm == "led-theme") {
              log("event: LED theme preference changed");
              theme_changed = true;
            } else if (nm == "themes.json" || nm.find("themes.json") != std::string::npos) {
              log("event: themes database changed");
              reload_theme_database();
              need_update = true;
            }
          }
        } else if (ev->wd == wd_themes_db) {
          if (ev->len > 0) {
            std::string nm(ev->name);
            log(std::string("event in themes db dir: ") + nm);
            // Match themes.json or any temp file that becomes themes.json
            if (nm == "themes.json" || nm.find("themes.json") != std::string::npos) {
              log("event: themes database changed");
              reload_theme_database();
              need_update = true;
            }
          }
        }
        i += sizeof(struct inotify_event) + ev->len;
      }
    }

    if (theme_changed) {
      load_theme();
      need_update = true;
    }

    if (need_update) {
      auto now = std::chrono::steady_clock::now();
      auto elapsed = std::chrono::duration_cast<std::chrono::milliseconds>(now - last_send).count();
      if (elapsed < 50) {
        std::this_thread::sleep_for(std::chrono::milliseconds(50 - elapsed));
      }
      leds = compose();
      if (leds.size() == prev_frame.size() && std::memcmp(leds.data(), prev_frame.data(), leds.size()*sizeof(RGB)) == 0) {
        // no change
      } else {
        tool.sendFrame(0, leds, cfg_.color_order);
        write_state(leds);
        if (!leds.empty()) {
          auto c = leds[0];
          char bufc[16]; std::snprintf(bufc, sizeof(bufc), "#%02X%02X%02X", c.r, c.g, c.b);
          log(std::string("sent frame, first LED ") + bufc);
        }
        prev_frame = leds;
        last_send = std::chrono::steady_clock::now();
      }
    }

    std::this_thread::sleep_for(std::chrono::milliseconds(20));
  }

  if (wd_current>=0) inotify_rm_watch(fd, wd_current);
  if (wd_palette_dir>=0) inotify_rm_watch(fd, wd_palette_dir);
  if (wd_brightness_dir>=0) inotify_rm_watch(fd, wd_brightness_dir);
  close(fd);
  return 0;
}

}
