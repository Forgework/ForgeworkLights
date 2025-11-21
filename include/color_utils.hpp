#pragma once
#include <vector>
#include "color.hpp"

namespace forgeworklights {

struct Gamma {
  uint8_t table[256];
  explicit Gamma(double exponent = 0.45);
  uint8_t apply(uint8_t v) const { return table[v]; }
};

// Apply gamma, brightness scaling, and optional current limiting
// brightness: clamped to [0.0, 1.0]
// safety_enabled: if true, enforces 2.4A rail limit with WS2812B 60mA/LED model
void apply_gamma_brightness_safety(std::vector<RGB>& leds, const Gamma& g, 
                                   double brightness, bool safety_enabled);

}
