#include "color_utils.hpp"
#include <cmath>
#include <algorithm>

namespace omarchy {

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

void apply_gamma_brightness(std::vector<RGB>& leds, const Gamma& g, double brightness) {
  brightness = std::clamp(brightness, 0.0, 1.0);
  for (auto& c : leds) {
    uint8_t r = g.apply(c.r);
    uint8_t gch = g.apply(c.g);
    uint8_t b = g.apply(c.b);
    c.r = static_cast<uint8_t>(std::round(r * brightness));
    c.g = static_cast<uint8_t>(std::round(gch * brightness));
    c.b = static_cast<uint8_t>(std::round(b * brightness));
  }
}

void enforce_current_cap(std::vector<RGB>& leds, double max_amps) {
  if (max_amps <= 0) return;
  // Approx current per LED (A): (r+g+b)/255 * 0.06
  double total = 0.0;
  for (const auto& c : leds) total += ( (c.r + c.g + c.b) / 255.0 ) * 0.06;
  if (total <= max_amps) return;
  double scale = max_amps / total;
  for (auto& c : leds) {
    c.r = static_cast<uint8_t>(std::round(c.r * scale));
    c.g = static_cast<uint8_t>(std::round(c.g * scale));
    c.b = static_cast<uint8_t>(std::round(c.b * scale));
  }
}

}
