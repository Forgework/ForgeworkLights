#pragma once
#include <string>
#include <functional>

namespace omarchy {

class ThemeWatcher {
public:
  using Callback = std::function<void()>;
  virtual ~ThemeWatcher() = default;
  virtual bool start(const std::string& path, Callback cb) = 0;
};

}
