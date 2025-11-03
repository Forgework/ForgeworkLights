#pragma once
#include "config.hpp"

namespace omarchy {

class ARGBDaemon {
public:
  explicit ARGBDaemon(const Config& cfg);
  int run();
private:
  Config cfg_;
};

}
