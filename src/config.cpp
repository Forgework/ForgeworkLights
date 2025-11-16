#include "config.hpp"
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <string>

namespace fs = std::filesystem;

namespace omarchy {

static std::string home() {
  const char* h = std::getenv("HOME");
  return h ? std::string(h) : std::string("/");
}

void Config::load_from_default() {
  config_path = home() + "/.config/omarchy-argb/config.toml";
  std::ifstream in(config_path);
  if (!in.good()) return;
  std::string line;
  while (std::getline(in, line)) {
    if (line.empty() || line[0] == '#') continue;
    auto pos = line.find('=');
    if (pos == std::string::npos) continue;
    std::string k = line.substr(0, pos);
    std::string v = line.substr(pos+1);
    auto trim = [](std::string& s){
      while (!s.empty() && (s.back()=='\n'||s.back()=='\r'||s.back()==' ')) s.pop_back();
      size_t i=0; while (i<s.size() && (s[i]==' '||s[i]=='\t')) ++i; s = s.substr(i);
      if (s.size()>=2 && s.front()=='"' && s.back()=='"') s = s.substr(1, s.size()-2);
    };
    trim(k); trim(v);
    if (k == "led_count") led_count = std::stoi(v);
    else if (k == "max_brightness") max_brightness = std::stod(v);
    else if (k == "gamma_exponent") gamma_exponent = std::stod(v);
    else if (k == "color_order") color_order = (v=="RGB"? ColorOrder::RGB: ColorOrder::GRB);
    else if (k == "tool_path") tool_path = v;
  }
}

}
