#pragma once
#include "config.hpp"

namespace omarchy {

class ARGBDaemon {
public:
  explicit ARGBDaemon(const Config& cfg, bool safety_enabled = true);
  int run();
private:
  Config cfg_;
  bool safety_enabled_;
};

}
