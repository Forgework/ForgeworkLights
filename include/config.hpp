#pragma once
#include <string>
#include "framework_tool.hpp"

namespace omarchy {

struct Config {
  int led_count = 22;
  double max_brightness = 0.2;
  double gamma_exponent = 1; // Degamma: convert sRGB → linear RGB for LEDs
  ColorOrder color_order = ColorOrder::GRB;
  std::string tool_path = "/usr/bin/framework_tool";
  std::string config_path;

  void load_from_default();
};

}
