#include "cli.hpp"
#include "framework_tool.hpp"
#include "argb_daemon.hpp"
#include "config.hpp"
#include <iostream>
#include <vector>
 #include <filesystem>
 #include <fstream>

namespace omarchy { namespace cli {

static int usage() {
  std::cout << "Usage: omarchy-argb <probe|once|daemon|brightness> [args]\n";
  return 1;
}

int run(int argc, char** argv) {
  if (argc < 2) return usage();
  std::string cmd = argv[1];
  if (cmd == "probe") {
    std::cout << "GRB" << std::endl;
    return 0;
  } else if (cmd == "once") {
    omarchy::Config cfg;
    cfg.load_from_default();
    omarchy::FrameworkTool tool(cfg.tool_path);
    std::vector<omarchy::RGB> leds;
    leds.reserve(cfg.led_count);
    for (int i = 0; i < cfg.led_count; ++i) {
      omarchy::RGB c{0, 0, 0};
      c.g = static_cast<uint8_t>(10 + (i * 245) / (cfg.led_count ? cfg.led_count : 1));
      c.r = static_cast<uint8_t>((i * 200) / (cfg.led_count ? cfg.led_count : 1));
      c.b = static_cast<uint8_t>(255 - c.r);
      leds.push_back(c);
    }
    bool ok = tool.sendFrame(0, leds, cfg.color_order);
    return ok ? 0 : 2;
  } else if (cmd == "daemon") {
    omarchy::Config cfg;
    cfg.load_from_default();
    omarchy::ARGBDaemon d(cfg);
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
