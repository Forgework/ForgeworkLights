#include "cli.hpp"
#include "framework_tool.hpp"
#include "argb_daemon.hpp"
#include "config.hpp"
#include "color_utils.hpp"
#include <iostream>
#include <vector>
#include <filesystem>
#include <fstream>
#include <cstring>
#include <algorithm>

namespace forgeworklights { namespace cli {

namespace {

std::string config_dir_path() {
  const char* home = std::getenv("HOME");
  std::string dir = std::string(home ? home : "/") + "/.config/forgeworklights";
  std::filesystem::create_directories(dir);
  return dir;
}

double clamp01(double value) {
  if (value < 0.0) return 0.0;
  if (value > 1.0) return 1.0;
  return value;
}

double read_brightness_value(const std::string& path) {
  std::ifstream in(path);
  double v = 1.0;
  if (in.good()) {
    in >> v;
  }
  return clamp01(v);
}

void write_brightness_value(const std::string& path, double value) {
  std::ofstream out(path);
  out.setf(std::ios::fixed); out.precision(3);
  out << clamp01(value) << "\n";
}

const std::vector<std::string> kAnimationOrder = {
  "static",
  "breathe",
  "wave",
  "ripple",
  "runner",
  "bounce",
  "sparkle",
  "gradient-shift",
  "drift"
};

bool is_valid_animation(const std::string& name) {
  return std::find(kAnimationOrder.begin(), kAnimationOrder.end(), name) != kAnimationOrder.end();
}

std::string read_animation_value(const std::string& path) {
  std::ifstream in(path);
  std::string value;
  if (in.good()) {
    std::getline(in, value);
    if (!value.empty()) return value;
  }
  return "static";
}

void write_animation_value(const std::string& path, const std::string& value) {
  std::ofstream out(path);
  out << value << "\n";
}

double parse_step(int argc, char** argv, double default_step) {
  if (argc >= 3) {
    try {
      return clamp01(std::abs(std::stod(argv[2])));
    } catch (...) {
      return default_step;
    }
  }
  return default_step;
}

}

static int usage() {
  std::cout << "Usage: forgeworklights <once|daemon|brightness|brightness-up|brightness-down|"
               "brightness-off|animation> [args] [--safety=on|off]\n";
  std::cout << "  once                   - Send test pattern once\n";
  std::cout << "  daemon                 - Run theme-syncing daemon\n";
  std::cout << "  brightness <0.0-1.0>   - Set brightness\n";
  std::cout << "  brightness-up [delta]  - Increase brightness (default +0.05)\n";
  std::cout << "  brightness-down [delta]- Decrease brightness (default -0.05)\n";
  std::cout << "  brightness-off         - Turn LEDs off (brightness 0)\n";
  std::cout << "  animation set <name>   - Set animation (static, breathe, ...)\n";
  std::cout << "  animation next|prev    - Cycle animation selection\n";
  std::cout << "\nOptions:\n";
  std::cout << "  --safety=on|off        - Enable/disable 2.4A current limiting (default: on)\n";
  return 1;
}

static bool parse_safety_flag(int argc, char** argv) {
  // Default is safety ON
  bool safety_enabled = true;
  for (int i = 2; i < argc; ++i) {
    if (std::strncmp(argv[i], "--safety=", 9) == 0) {
      const char* val = argv[i] + 9;
      if (std::strcmp(val, "off") == 0 || std::strcmp(val, "OFF") == 0) {
        safety_enabled = false;
      } else if (std::strcmp(val, "on") == 0 || std::strcmp(val, "ON") == 0) {
        safety_enabled = true;
      }
    }
  }
  return safety_enabled;
}

int run(int argc, char** argv) {
  if (argc < 2) return usage();
  std::string cmd = argv[1];
  if (cmd == "once") {
    bool safety_enabled = parse_safety_flag(argc, argv);
    forgeworklights::Config cfg;
    cfg.load_from_default();
    forgeworklights::FrameworkTool tool(cfg.tool_path);
    forgeworklights::Gamma gamma(cfg.gamma_exponent);
    std::vector<forgeworklights::RGB> leds;
    leds.reserve(cfg.led_count);
    for (int i = 0; i < cfg.led_count; ++i) {
      forgeworklights::RGB c{0, 0, 0};
      c.g = static_cast<uint8_t>(10 + (i * 245) / (cfg.led_count ? cfg.led_count : 1));
      c.r = static_cast<uint8_t>((i * 200) / (cfg.led_count ? cfg.led_count : 1));
      c.b = static_cast<uint8_t>(255 - c.r);
      leds.push_back(c);
    }
    apply_gamma_brightness_safety(leds, gamma, cfg.max_brightness, safety_enabled);
    bool ok = tool.sendFrame(0, leds, cfg.color_order);
    return ok ? 0 : 2;
  } else if (cmd == "daemon") {
    bool safety_enabled = parse_safety_flag(argc, argv);
    forgeworklights::Config cfg;
    cfg.load_from_default();
    forgeworklights::ARGBDaemon d(cfg, safety_enabled);
    return d.run();
  } else if (cmd == "brightness") {
    if (argc < 3) return usage();
    double v = clamp01(std::stod(argv[2]));
    std::string dir = config_dir_path();
    std::string path = dir + "/brightness";
    write_brightness_value(path, v);
    std::cout << v << std::endl;
    return 0;
  } else if (cmd == "brightness-up" || cmd == "brightness-down") {
    double step = parse_step(argc, argv, 0.05);
    std::string dir = config_dir_path();
    std::string path = dir + "/brightness";
    double current = read_brightness_value(path);
    if (cmd == "brightness-up") {
      current = clamp01(current + step);
    } else {
      current = clamp01(current - step);
    }
    write_brightness_value(path, current);
    std::cout << current << std::endl;
    return 0;
  } else if (cmd == "brightness-off") {
    std::string dir = config_dir_path();
    std::string path = dir + "/brightness";
    write_brightness_value(path, 0.0);
    std::cout << 0.0 << std::endl;
    return 0;
  } else if (cmd == "animation") {
    if (argc < 3) return usage();
    std::string action = argv[2];
    std::string dir = config_dir_path();
    std::string path = dir + "/animation";
    if (action == "set") {
      if (argc < 4) {
        std::cerr << "animation set requires a name" << std::endl;
        return 1;
      }
      std::string name = argv[3];
      if (!is_valid_animation(name)) {
        std::cerr << "Unknown animation: " << name << std::endl;
        return 1;
      }
      write_animation_value(path, name);
      std::cout << name << std::endl;
      return 0;
    } else if (action == "next" || action == "prev") {
      std::string current = read_animation_value(path);
      auto it = std::find(kAnimationOrder.begin(), kAnimationOrder.end(), current);
      int idx = 0;
      if (it != kAnimationOrder.end()) {
        idx = static_cast<int>(std::distance(kAnimationOrder.begin(), it));
      }
      if (action == "next") {
        idx = (idx + 1) % kAnimationOrder.size();
      } else {
        idx = (idx - 1 + static_cast<int>(kAnimationOrder.size())) % static_cast<int>(kAnimationOrder.size());
      }
      std::string next_value = kAnimationOrder[idx];
      write_animation_value(path, next_value);
      std::cout << next_value << std::endl;
      return 0;
    } else if (action == "list") {
      for (const auto& name : kAnimationOrder) {
        std::cout << name << std::endl;
      }
      return 0;
    } else {
      std::cerr << "Unknown animation subcommand: " << action << std::endl;
      return usage();
    }
  }
  return usage();
}

} }
