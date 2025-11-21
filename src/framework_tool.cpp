#include "framework_tool.hpp"
#include <sstream>
#include <cstdlib>
#include <string>
#include <unistd.h>
#include <sys/wait.h>
#include <vector>

namespace forgeworklights {

// Path to the root helper binary
static constexpr const char* ROOT_HELPER = "/usr/local/libexec/fw_root_helper";

FrameworkTool::FrameworkTool(std::string tool_path) : tool_path_(std::move(tool_path)) {}

// Convert RGB bytes to hex string
static std::string bytes_to_hex(const std::vector<uint8_t>& data) {
  static const char* hex = "0123456789ABCDEF";
  std::string result;
  result.reserve(data.size() * 2);
  for (uint8_t byte : data) {
    result += hex[(byte >> 4) & 0xF];
    result += hex[byte & 0xF];
  }
  return result;
}

bool FrameworkTool::sendFrame(int zone, const std::vector<RGB>& leds, ColorOrder order) const {
  // Build RGB byte buffer based on color order
  std::vector<uint8_t> led_data;
  led_data.reserve(leds.size() * 3);
  
  for (const auto& c : leds) {
    if (order == ColorOrder::GRB) {
      led_data.push_back(c.g);
      led_data.push_back(c.r);
      led_data.push_back(c.b);
    } else {
      led_data.push_back(c.r);
      led_data.push_back(c.g);
      led_data.push_back(c.b);
    }
  }
  
  // Convert to hex string for helper
  std::string hex_payload = bytes_to_hex(led_data);
  
  std::fprintf(stderr, "[omarchy-argb] sending %zu LEDs via root helper\n", leds.size());
  
  // Fork and exec the root helper
  pid_t pid = fork();
  if (pid < 0) {
    std::perror("[omarchy-argb] fork failed");
    return false;
  }
  
  if (pid == 0) {
    // Child process: exec the root helper
    execl(ROOT_HELPER, ROOT_HELPER, hex_payload.c_str(), nullptr);
    // If exec fails, exit immediately
    std::perror("[omarchy-argb] execl failed");
    std::exit(1);
  }
  
  // Parent process: wait for helper to complete
  int status = 0;
  if (waitpid(pid, &status, 0) < 0) {
    std::perror("[omarchy-argb] waitpid failed");
    return false;
  }
  
  if (WIFEXITED(status)) {
    int exit_code = WEXITSTATUS(status);
    if (exit_code != 0) {
      std::fprintf(stderr, "[omarchy-argb] root helper exit code: %d\n", exit_code);
      return false;
    }
  } else {
    std::fprintf(stderr, "[omarchy-argb] root helper terminated abnormally\n");
    return false;
  }
  
  return true;
}

}
