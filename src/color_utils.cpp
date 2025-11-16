#include "color_utils.hpp"
#include <cmath>
#include <algorithm>
#include <cstdio>

namespace omarchy {

// Fixed hardware limits for Framework JARGB1 header
static constexpr float HARD_RAIL_LIMIT_AMPS = 2.4f;      // 5V rail max safe draw
static constexpr float WS2812B_MAX_CURRENT_PER_LED = 0.060f;  // Full white worst-case

Gamma::Gamma(double exponent) {
  // Color space conversion via gamma correction
  // exponent = 0.45: Degamma (sRGB → linear) - recommended for addressable LEDs
  // exponent = 1.0:  Identity (no conversion)
  // exponent = 2.2:  Gamma encode (linear → sRGB)
  for (int i=0;i<256;++i) {
    double n = i / 255.0;
    double v = std::pow(n, exponent);
    int o = static_cast<int>(std::round(v * 255.0));
    if (o<0) o=0; if (o>255) o=255;
    table[i] = static_cast<uint8_t>(o);
  }
}

void apply_gamma_brightness_safety(std::vector<RGB>& leds, const Gamma& g, 
                                   double brightness, bool safety_enabled) {
  // 1. Clamp brightness strictly to [0.0, 1.0]
  brightness = std::clamp(brightness, 0.0, 1.0);
  
  // 2. Apply gamma correction and brightness scaling
  for (auto& c : leds) {
    uint8_t r = g.apply(c.r);
    uint8_t gch = g.apply(c.g);
    uint8_t b = g.apply(c.b);
    c.r = static_cast<uint8_t>(std::round(r * brightness));
    c.g = static_cast<uint8_t>(std::round(gch * brightness));
    c.b = static_cast<uint8_t>(std::round(b * brightness));
  }
  
  // 3. Apply current limiting if safety mode enabled
  if (!safety_enabled) return;
  
  // Estimate current using WS2812B physical model
  // Worst case: full white = 60mA per LED
  // Current scales linearly with brightness since brightness is already applied
  int led_count = static_cast<int>(leds.size());
  float estimated_current = led_count * WS2812B_MAX_CURRENT_PER_LED * brightness;
  
  // Only limit if we exceed the rail capacity
  if (estimated_current <= HARD_RAIL_LIMIT_AMPS) return;
  
  // Calculate uniform scale factor to bring current under limit
  float scale = HARD_RAIL_LIMIT_AMPS / estimated_current;
  
  // Apply scaling uniformly to maintain color ratios
  static bool logged_limiting = false;
  if (!logged_limiting) {
    std::fprintf(stderr, "[omarchy-argb] current limiting engaged: %.2fA → %.2fA (scale %.3f)\n",
                 estimated_current, HARD_RAIL_LIMIT_AMPS, scale);
    logged_limiting = true;
  }
  
  for (auto& c : leds) {
    int r = static_cast<int>(std::round(c.r * scale));
    int g = static_cast<int>(std::round(c.g * scale));
    int b = static_cast<int>(std::round(c.b * scale));
    c.r = static_cast<uint8_t>(std::clamp(r, 0, 255));
    c.g = static_cast<uint8_t>(std::clamp(g, 0, 255));
    c.b = static_cast<uint8_t>(std::clamp(b, 0, 255));
  }
}

}
