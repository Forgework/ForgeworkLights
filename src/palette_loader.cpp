#include "palette_loader.hpp"
#include <fstream>
#include <regex>
#include <unordered_map>
#include <algorithm>
#include <filesystem>

namespace omarchy {

static std::string slurp(const std::string& path) {
  std::ifstream in(path);
  if (!in.good()) return {};
  return std::string((std::istreambuf_iterator<char>(in)), std::istreambuf_iterator<char>());
}

bool parse_hex_rgb(const std::string& s, RGB& out) {
  if (s.size() == 7 && s[0] == '#') {
    auto hx = [](char c)->int{ if(c>='0'&&c<='9') return c-'0'; if(c>='a'&&c<='f') return 10+(c-'a'); if(c>='A'&&c<='F') return 10+(c-'A'); return -1; };
    int r1=hx(s[1]), r2=hx(s[2]), g1=hx(s[3]), g2=hx(s[4]), b1=hx(s[5]), b2=hx(s[6]);
    if (r1<0||r2<0||g1<0||g2<0||b1<0||b2<0) return false;
    out.r = (uint8_t)((r1<<4)|r2);
    out.g = (uint8_t)((g1<<4)|g2);
    out.b = (uint8_t)((b1<<4)|b2);
    return true;
  }
  return false;
}

std::optional<Palette> load_palette_from_file(const std::string& path) {
  std::string data = slurp(path);
  if (data.empty()) return std::nullopt;

  // Very simple JSON-ish capture: "key"\s*:\s*"#RRGGBB"
  std::regex re("\"([a-zA-Z0-9_]+)\"\\s*:\\s*\"(#[0-9a-fA-F]{6})\"");
  std::smatch m;
  std::unordered_map<std::string, RGB> map;
  for (auto it = std::sregex_iterator(data.begin(), data.end(), re); it != std::sregex_iterator(); ++it) {
    std::string key = (*it)[1].str();
    std::string val = (*it)[2].str();
    RGB c{}; if (parse_hex_rgb(val, c)) map[key]=c;
  }
  if (map.empty()) return std::nullopt;
  Palette p{};
  auto get = [&](const std::string& k)->std::optional<RGB>{ auto it=map.find(k); return it==map.end()?std::nullopt:std::optional<RGB>(it->second); };
  
  // Extract 3-color gradient
  auto acc = get("accent");
  auto acc2 = get("accent2");
  auto acc3 = get("accent3");
  if (acc) p.accent = *acc;
  if (acc2) p.accent2 = *acc2;
  if (acc3) p.accent3 = *acc3;
  
  // Only return if we have all three gradient colors
  bool has_all = (p.accent.r || p.accent.g || p.accent.b) && 
                 (p.accent2.r || p.accent2.g || p.accent2.b) && 
                 (p.accent3.r || p.accent3.g || p.accent3.b);
  if (has_all) return p;
  
  return std::nullopt;
}

// btop.theme: extract temperature gradient colors
std::optional<Palette> load_palette_from_btop(const std::string& path) {
  std::string data = slurp(path);
  if (data.empty()) return std::nullopt;
  Palette p{};
  auto find_hex = [&](const std::string& key, RGB& out) -> bool {
    std::regex re("theme\\[" + key + "\\]=\"(#[0-9a-fA-F]{6})\"");
    std::smatch m;
    if (std::regex_search(data, m, re)) {
      return parse_hex_rgb(m[1].str(), out);
    }
    return false;
  };
  bool has_start = find_hex("temp_start", p.accent);
  bool has_mid = find_hex("temp_mid", p.accent2);
  bool has_end = find_hex("temp_end", p.accent3);
  // Only return palette if we have all three gradient colors
  if (has_start && has_mid && has_end) return p;
  return std::nullopt;
}


std::optional<Palette> load_palette_from_theme_dir(const std::string& dir) {
  namespace fs = std::filesystem;
  fs::path d(dir);
  // Priority: btop.theme (primary) -> palette.json -> theme.json
  fs::path btop = d / "btop.theme";
  if (fs::exists(btop)) {
    if (auto p = load_palette_from_btop(btop.string())) return p;
  }
  fs::path p1 = d / "palette.json";
  if (fs::exists(p1)) {
    if (auto p = load_palette_from_file(p1.string())) return p;
  }
  fs::path p2 = d / "theme.json";
  if (fs::exists(p2)) {
    if (auto p = load_palette_from_file(p2.string())) return p;
  }
  return std::nullopt;
}

}
