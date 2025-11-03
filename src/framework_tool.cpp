#include "framework_tool.hpp"
#include <sstream>
#include <cstdlib>
#include <string>
 #include <unistd.h>

namespace omarchy {

FrameworkTool::FrameworkTool(std::string tool_path) : tool_path_(std::move(tool_path)) {}

static std::string hex24(uint8_t r, uint8_t g, uint8_t b) {
  static const char* hex = "0123456789ABCDEF";
  std::string s("0x000000");
  auto put = [&](int idx, uint8_t v){ s[idx] = hex[(v >> 4) & 0xF]; s[idx+1] = hex[v & 0xF]; };
  put(2, r); put(4, g); put(6, b);
  return s;
}

bool FrameworkTool::sendFrame(int zone, const std::vector<RGB>& leds, ColorOrder order) const {
  std::ostringstream cmd;
  // Use sudo if not root
  if (geteuid() != 0) {
    cmd << "/usr/bin/sudo ";
  }
  cmd << tool_path_ << " --rgbkbd " << zone;
  for (const auto& c : leds) {
    uint8_t r=c.r,g=c.g,b=c.b;
    if (order == ColorOrder::GRB) {
      cmd << ' ' << hex24(g,r,b);
    } else {
      cmd << ' ' << hex24(r,g,b);
    }
  }
  std::string s = cmd.str();
  std::fprintf(stderr, "[omarchy-argb] exec: %s\n", s.c_str());
  int rc = std::system(s.c_str());
  if (rc != 0) {
    std::fprintf(stderr, "[omarchy-argb] framework_tool exit code: %d\n", rc);
  }
  return rc == 0;
}

}
