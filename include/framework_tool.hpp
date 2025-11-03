#pragma once
#include <string>
#include <vector>
#include "color.hpp"

namespace omarchy {

enum class ColorOrder { RGB, GRB };

class FrameworkTool {
public:
  explicit FrameworkTool(std::string tool_path);
  bool sendFrame(int zone, const std::vector<RGB>& leds, ColorOrder order) const;
private:
  std::string tool_path_;
};

}
