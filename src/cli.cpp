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

namespace forgeworklights { namespace cli {

static int usage() {
  std::cout << "Usage: omarchy-argb <once|daemon|brightness> [--safety=on|off]\n";
  std::cout << "  once                   - Send test pattern once\n";
  std::cout << "  daemon                 - Run theme-syncing daemon\n";
  std::cout << "  brightness <0.0-1.0>   - Set brightness\n";
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
    double v = std::stod(argv[2]);
    if (v < 0.0) v = 0.0; if (v > 1.0) v = 1.0;
    const char* h = std::getenv("HOME");
    std::string dir = std::string(h?h:"/") + "/.config/omarchy-argb";
    std::filesystem::create_directories(dir);
    std::string path = dir + "/brightness";
    std::ofstream out(path);
    out.setf(std::ios::fixed); out.precision(3);
    out << v << "\n";
    std::cout << v << std::endl;
    return 0;
  }
  return usage();
}

} }
