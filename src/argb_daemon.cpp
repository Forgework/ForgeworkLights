#include "argb_daemon.hpp"
#include "framework_tool.hpp"
#include "theme.hpp"
#include "palette_loader.hpp"
#include "color_utils.hpp"
#include "theme_database.hpp"
#include "animations.hpp"
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
#include <memory>

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
  
  auto read_animation_preference = [&]() -> std::string {
    // Read animation preference from config file
    std::string anim_file = config_base() + "/omarchy-argb/animation";
    std::ifstream in(anim_file);
    if (!in.good()) return "static";  // Default to static
    std::string anim;
    std::getline(in, anim);
    // Trim whitespace
    anim.erase(0, anim.find_first_not_of(" \t\n\r"));
    anim.erase(anim.find_last_not_of(" \t\n\r") + 1);
    return anim.empty() ? "static" : anim;
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

  // Helper to get theme colors as hex strings for animations
  auto get_theme_colors_hex = [&]() -> std::vector<std::string> {
    std::vector<std::string> colors;
    std::string led_theme_pref = read_led_theme_preference();
    std::optional<ThemeColors> db_colors;
    
    if (led_theme_pref != "match") {
      db_colors = theme_db.get(led_theme_pref);
    } else if (theme) {
      std::string theme_name = std::filesystem::path(theme->theme_dir).filename().string();
      db_colors = theme_db.get(theme_name);
    }
    
    if (db_colors && db_colors->colors.size() >= 3) {
      for (const auto& c : db_colors->colors) {
        char buf[8];
        std::snprintf(buf, sizeof(buf), "#%02X%02X%02X", c.r, c.g, c.b);
        colors.push_back(std::string(buf));
      }
    }
    return colors;
  };
  
  // Helper to read animation parameters from JSON file
  auto get_param = [&](const std::string& anim_name, const std::string& param_name, double default_val) -> double {
    std::string params_file = config_base() + "/omarchy-argb/animation-params.json";
    std::ifstream in(params_file);
    if (!in.good()) return default_val;
    
    std::string content((std::istreambuf_iterator<char>(in)), std::istreambuf_iterator<char>());
    
    // Simple JSON parsing for: { "animation": { "param": value } }
    size_t anim_pos = content.find("\"" + anim_name + "\"");
    if (anim_pos == std::string::npos) return default_val;
    
    size_t param_pos = content.find("\"" + param_name + "\"", anim_pos);
    if (param_pos == std::string::npos) return default_val;
    
    size_t colon_pos = content.find(":", param_pos);
    if (colon_pos == std::string::npos) return default_val;
    
    size_t value_start = colon_pos + 1;
    while (value_start < content.size() && (content[value_start] == ' ' || content[value_start] == '\t')) {
      value_start++;
    }
    
    size_t value_end = value_start;
    while (value_end < content.size() && (std::isdigit(content[value_end]) || content[value_end] == '.' || content[value_end] == '-')) {
      value_end++;
    }
    
    if (value_end > value_start) {
      try {
        return std::stod(content.substr(value_start, value_end - value_start));
      } catch (...) {
        return default_val;
      }
    }
    
    return default_val;
  };
  
  // Helper to create animation based on name
  auto create_animation = [&](const std::string& anim_name) -> std::unique_ptr<BaseAnimation> {
    std::vector<std::string> theme_colors = get_theme_colors_hex();
    if (theme_colors.empty()) {
      // Fallback colors (22-color gradient)
      theme_colors = {"#8a8a8d", "#948c81", "#9e8d76", "#a88f6b", "#b29160", "#bc9356", 
                      "#c6954b", "#d09740", "#da9936", "#e49b2b", "#ee9d20", "#f29918", 
                      "#ed9214", "#e88a11", "#e4820d", "#df7a0f", "#da7211", "#d66a13", 
                      "#d16214", "#cd5a16", "#c85218", "#c3491a", "#bf411c", "#ba391e"};
    }
    
    if (anim_name == "static") {
      return std::make_unique<StaticAnimation>(cfg_.led_count, theme_colors);
    } else if (anim_name == "breathe") {
      double period = get_param("breathe", "period", 3.0);
      return std::make_unique<BreatheAnimation>(cfg_.led_count, theme_colors, period);
    } else if (anim_name == "wave") {
      double speed = get_param("wave", "speed", 0.5);
      return std::make_unique<WaveAnimation>(cfg_.led_count, theme_colors, speed);
    } else if (anim_name == "ripple") {
      double period = get_param("ripple", "period", 2.0);
      double ripple_width = get_param("ripple", "ripple_width", 0.3);
      return std::make_unique<RippleAnimation>(cfg_.led_count, theme_colors, period, ripple_width);
    } else if (anim_name == "runner") {
      double speed = get_param("runner", "speed", 20.0);
      int trail_length = static_cast<int>(get_param("runner", "trail_length", 8.0));
      int num_runners = static_cast<int>(get_param("runner", "num_runners", 2.0));
      return std::make_unique<RunnerAnimation>(cfg_.led_count, theme_colors, speed, trail_length, num_runners);
    } else if (anim_name == "bounce") {
      double period = get_param("bounce", "period", 2.0);
      int segment_size = static_cast<int>(get_param("bounce", "segment_size", 5.0));
      return std::make_unique<BounceAnimation>(cfg_.led_count, theme_colors, period, segment_size);
    } else if (anim_name == "sparkle") {
      double sparkle_rate = get_param("sparkle", "sparkle_rate", 0.1);
      int sparkle_duration = static_cast<int>(get_param("sparkle", "sparkle_duration", 15.0));
      return std::make_unique<SparkleAnimation>(cfg_.led_count, theme_colors, sparkle_rate, sparkle_duration);
    } else if (anim_name == "strobe") {
      double frequency = get_param("strobe", "frequency", 10.0);
      return std::make_unique<StrobeAnimation>(cfg_.led_count, theme_colors, frequency);
    } else if (anim_name == "gradient-shift") {
      double period = get_param("gradient-shift", "period", 10.0);
      double shift_amount = get_param("gradient-shift", "shift_amount", 1.0);
      return std::make_unique<GradientShiftAnimation>(cfg_.led_count, theme_colors, period, shift_amount);
    } else if (anim_name == "drift") {
      double min_speed = get_param("drift", "min_speed", 0.3);
      double max_speed = get_param("drift", "max_speed", 10.0);
      double twinkle = get_param("drift", "twinkle", 0.0);
      return std::make_unique<DriftAnimation>(cfg_.led_count, theme_colors, min_speed, max_speed, twinkle);
    } else {
      // Default to static
      return std::make_unique<StaticAnimation>(cfg_.led_count, theme_colors);
    }
  };
  
  // Initial resolve and send
  load_theme();
  std::string current_animation = read_animation_preference();
  std::unique_ptr<BaseAnimation> animation = create_animation(current_animation);
  log(std::string("Created animation: ") + current_animation);
  
  auto leds = animation->render_frame();
  double brightness = read_brightness();
  apply_gamma_brightness(leds, gamma, brightness);
  tool.sendFrame(0, leds, cfg_.color_order);
  write_state(leds);
  if (!leds.empty()) {
    auto c = leds[0];
    char bufc[16]; std::snprintf(bufc, sizeof(bufc), "#%02X%02X%02X", c.r, c.g, c.b);
    log(std::string("sent initial frame, first LED ") + bufc);
  }
  prev_frame = leds;

  // Event loop - runs animation frames at 30 FPS
  char buf[4096];
  auto frame_start = std::chrono::steady_clock::now();
  const int target_fps = 30;
  const auto frame_duration = std::chrono::milliseconds(1000 / target_fps);
  
  for(;;){
    bool animation_changed = false;
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
              theme_changed = true;
            }
          }
        } else if (ev->wd == wd_brightness_dir) {
          if (ev->len > 0) {
            std::string nm(ev->name);
            if (nm == "brightness") {
              log("event: brightness changed");
              // Brightness changes don't need animation recreation
            } else if (nm == "led-theme") {
              log("event: LED theme preference changed");
              theme_changed = true;
            } else if (nm == "animation") {
              log("event: animation preference changed");
              animation_changed = true;
            } else if (nm == "animation-params.json") {
              log("event: animation parameters changed");
              animation_changed = true;
            } else if (nm == "themes.json" || nm.find("themes.json") != std::string::npos) {
              log("event: themes database changed");
              reload_theme_database();
              theme_changed = true;
            }
          }
        } else if (ev->wd == wd_themes_db) {
          if (ev->len > 0) {
            std::string nm(ev->name);
            log(std::string("event in themes db dir: ") + nm);
            if (nm == "themes.json" || nm.find("themes.json") != std::string::npos) {
              log("event: themes database changed");
              reload_theme_database();
              theme_changed = true;
            }
          }
        }
        i += sizeof(struct inotify_event) + ev->len;
      }
    }

    if (theme_changed) {
      load_theme();
      // Recreate animation with new theme colors
      current_animation = read_animation_preference();
      animation = create_animation(current_animation);
      log(std::string("Recreated animation with new theme: ") + current_animation);
    }
    
    if (animation_changed) {
      // Animation type changed - recreate
      current_animation = read_animation_preference();
      animation = create_animation(current_animation);
      log(std::string("Switched to animation: ") + current_animation);
    }

    // Render next animation frame
    leds = animation->render_frame();
    double brightness = read_brightness();
    apply_gamma_brightness(leds, gamma, brightness);
    
    // Send frame if changed
    if (leds.size() != prev_frame.size() || std::memcmp(leds.data(), prev_frame.data(), leds.size()*sizeof(RGB)) != 0) {
      tool.sendFrame(0, leds, cfg_.color_order);
      // Only write state periodically to avoid excessive I/O
      static int frame_count = 0;
      if (++frame_count % 30 == 0) { // Every second at 30 FPS
        write_state(leds);
      }
      prev_frame = leds;
    }

    // Maintain target FPS
    auto frame_end = std::chrono::steady_clock::now();
    auto elapsed = frame_end - frame_start;
    if (elapsed < frame_duration) {
      std::this_thread::sleep_for(frame_duration - elapsed);
    }
    frame_start = std::chrono::steady_clock::now();
  }

  if (wd_current>=0) inotify_rm_watch(fd, wd_current);
  if (wd_palette_dir>=0) inotify_rm_watch(fd, wd_palette_dir);
  if (wd_brightness_dir>=0) inotify_rm_watch(fd, wd_brightness_dir);
  close(fd);
  return 0;
}

}
