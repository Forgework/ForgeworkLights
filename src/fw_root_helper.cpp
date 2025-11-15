// fw_root_helper.cpp
// Hardened root-only helper for privileged framework_tool LED writes
// This binary must be installed as root:root with permissions 700

#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <cstdint>
#include <string>
#include <vector>
#include <unistd.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <grp.h>
#include <cctype>

// Maximum reasonable LED count (Framework Desktop JARGB1 supports up to 2.4A)
static constexpr int MAX_LED_COUNT = 22;
static constexpr int MIN_LED_COUNT = 1;
static constexpr int BYTES_PER_LED = 3;  // RGB

// Path to framework_tool (verified at compile time to exist on target system)
static constexpr const char* FRAMEWORK_TOOL = "/usr/bin/framework_tool";

// Helper to convert hex char to nibble
static int hex_to_nibble(char c) {
  if (c >= '0' && c <= '9') return c - '0';
  if (c >= 'A' && c <= 'F') return c - 'A' + 10;
  if (c >= 'a' && c <= 'f') return c - 'a' + 10;
  return -1;
}

// Decode hex string to bytes, returns true on success
static bool hex_decode(const char* hex_str, std::vector<uint8_t>& out) {
  size_t len = std::strlen(hex_str);
  
  // Must be even length
  if (len % 2 != 0) {
    std::fprintf(stderr, "fw_root_helper: hex string has odd length\n");
    return false;
  }
  
  out.clear();
  out.reserve(len / 2);
  
  for (size_t i = 0; i < len; i += 2) {
    int hi = hex_to_nibble(hex_str[i]);
    int lo = hex_to_nibble(hex_str[i + 1]);
    
    if (hi < 0 || lo < 0) {
      std::fprintf(stderr, "fw_root_helper: invalid hex character\n");
      return false;
    }
    
    out.push_back((uint8_t)((hi << 4) | lo));
  }
  
  return true;
}

// Convert byte buffer to framework_tool hex color arguments
static std::vector<char*> build_argv(const std::vector<uint8_t>& led_data) {
  int led_count = led_data.size() / BYTES_PER_LED;
  
  std::vector<char*> argv;
  argv.push_back(const_cast<char*>(FRAMEWORK_TOOL));
  argv.push_back(const_cast<char*>("--rgbkbd"));
  argv.push_back(const_cast<char*>("0"));  // zone 0
  
  // Allocate hex strings for each LED
  static std::vector<std::string> hex_colors;
  hex_colors.clear();
  hex_colors.reserve(led_count);
  
  for (int i = 0; i < led_count; ++i) {
    uint8_t r = led_data[i * BYTES_PER_LED + 0];
    uint8_t g = led_data[i * BYTES_PER_LED + 1];
    uint8_t b = led_data[i * BYTES_PER_LED + 2];
    
    char buf[16];
    std::snprintf(buf, sizeof(buf), "0x%02X%02X%02X", r, g, b);
    hex_colors.emplace_back(buf);
  }
  
  for (auto& color : hex_colors) {
    argv.push_back(const_cast<char*>(color.c_str()));
  }
  
  argv.push_back(nullptr);  // execv requires NULL terminator
  return argv;
}

int main(int argc, char** argv) {
  // Harden environment immediately
  clearenv();
  umask(0077);
  
  // Verify we have effective root (setuid-root or direct root execution)
  if (geteuid() != 0) {
    std::fprintf(stderr, "fw_root_helper: must be installed setuid-root\n");
    return 1;
  }
  
  // Drop supplementary groups for hardening
  #ifdef __linux__
  setgroups(0, nullptr);
  #endif
  
  // Ensure we have full root privileges (promotes euid to ruid)
  if (setuid(0) != 0 || setgid(0) != 0) {
    std::fprintf(stderr, "fw_root_helper: failed to set uid/gid to root\n");
    return 1;
  }
  
  // Validate argument count
  if (argc != 2) {
    std::fprintf(stderr, "fw_root_helper: usage: fw_root_helper <HEX_LED_DATA>\n");
    std::fprintf(stderr, "fw_root_helper: HEX_LED_DATA must be hex-encoded RGB data (3 bytes per LED)\n");
    return 1;
  }
  
  const char* hex_input = argv[1];
  
  // Validate input is not empty
  if (!hex_input || hex_input[0] == '\0') {
    std::fprintf(stderr, "fw_root_helper: empty input\n");
    return 1;
  }
  
  // Check length is reasonable
  size_t hex_len = std::strlen(hex_input);
  if (hex_len > MAX_LED_COUNT * BYTES_PER_LED * 2) {
    std::fprintf(stderr, "fw_root_helper: input too large (max %d LEDs)\n", MAX_LED_COUNT);
    return 1;
  }
  
  if (hex_len < MIN_LED_COUNT * BYTES_PER_LED * 2) {
    std::fprintf(stderr, "fw_root_helper: input too small (min %d LED)\n", MIN_LED_COUNT);
    return 1;
  }
  
  // Decode hex to bytes
  std::vector<uint8_t> led_data;
  if (!hex_decode(hex_input, led_data)) {
    std::fprintf(stderr, "fw_root_helper: hex decode failed\n");
    return 1;
  }
  
  // Validate decoded data is multiple of 3 (RGB triplets)
  if (led_data.size() % BYTES_PER_LED != 0) {
    std::fprintf(stderr, "fw_root_helper: decoded data is not RGB triplets\n");
    return 1;
  }
  
  int led_count = led_data.size() / BYTES_PER_LED;
  if (led_count < MIN_LED_COUNT || led_count > MAX_LED_COUNT) {
    std::fprintf(stderr, "fw_root_helper: invalid LED count %d (must be %d-%d)\n", 
                 led_count, MIN_LED_COUNT, MAX_LED_COUNT);
    return 1;
  }
  
  // Build argv for framework_tool
  std::vector<char*> fw_argv = build_argv(led_data);
  
  // Execute framework_tool
  // Use execv to avoid shell injection - direct binary execution only
  execv(FRAMEWORK_TOOL, fw_argv.data());
  
  // If we get here, exec failed
  std::perror("fw_root_helper: execv failed");
  return 1;
}
