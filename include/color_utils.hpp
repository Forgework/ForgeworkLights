#pragma once
#include <vector>
#include "color.hpp"

namespace omarchy {

struct Gamma {
  uint8_t table[256];
  explicit Gamma(double exponent = 0.45);
  uint8_t apply(uint8_t v) const { return table[v]; }
};

// Apply gamma then brightness scaling in [0,1]
void apply_gamma_brightness(std::vector<RGB>& leds, const Gamma& g, double brightness);

// Enforce current cap by uniform scaling. Assume 60mA at full white per LED.
void enforce_current_cap(std::vector<RGB>& leds, double max_amps);

}
