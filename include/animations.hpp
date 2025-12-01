#pragma once

#include "color.hpp"
#include <vector>
#include <string>
#include <cmath>
#include <chrono>
#include <random>
#include <map>
#include <memory>

namespace forgeworklights {

// Helper functions for RGB (defined in color.hpp)
inline RGB rgb_scale(const RGB& c, double factor) {
  return RGB{
    static_cast<uint8_t>(c.r * factor),
    static_cast<uint8_t>(c.g * factor),
    static_cast<uint8_t>(c.b * factor)
  };
}

inline RGB rgb_interpolate(const RGB& c1, const RGB& c2, double t) {
  t = std::max(0.0, std::min(1.0, t));
  return RGB{
    static_cast<uint8_t>(c1.r + (c2.r - c1.r) * t),
    static_cast<uint8_t>(c1.g + (c2.g - c1.g) * t),
    static_cast<uint8_t>(c1.b + (c2.b - c1.b) * t)
  };
}

inline RGB rgb_from_hex(const std::string& hex) {
  std::string h = hex;
  if (h[0] == '#') h = h.substr(1);
  if (h.length() != 6) return RGB{0, 0, 0};
  
  try {
    uint8_t r = std::stoi(h.substr(0, 2), nullptr, 16);
    uint8_t g = std::stoi(h.substr(2, 2), nullptr, 16);
    uint8_t b = std::stoi(h.substr(4, 2), nullptr, 16);
    return RGB{r, g, b};
  } catch (...) {
    return RGB{0, 0, 0};
  }
}

class BaseAnimation {
protected:
  int led_count_;
  std::vector<RGB> theme_colors_;
  std::chrono::steady_clock::time_point start_time_;
  
  // Get elapsed time in seconds
  double get_elapsed_time() const {
    auto now = std::chrono::steady_clock::now();
    return std::chrono::duration<double>(now - start_time_).count();
  }
  
  // Get color from theme gradient at position (0.0 to 1.0)
  RGB get_color_at_position(double position) const {
    position = std::max(0.0, std::min(1.0, position));
    
    int num_colors = theme_colors_.size();
    double color_pos = position * (num_colors - 1);
    
    int idx = static_cast<int>(color_pos);
    double frac = color_pos - idx;
    
    if (idx >= num_colors - 1) {
      return theme_colors_.back();
    }
    
    return rgb_interpolate(theme_colors_[idx], theme_colors_[idx + 1], frac);
  }
  
  // Get base color for an LED based on its position
  RGB get_led_base_color(int led_index) const {
    double position = led_index / std::max(1.0, static_cast<double>(led_count_ - 1));
    return get_color_at_position(position);
  }

public:
  BaseAnimation(int led_count, const std::vector<std::string>& theme_colors)
    : led_count_(led_count) {
    start_time_ = std::chrono::steady_clock::now();
    
    for (const auto& hex : theme_colors) {
      theme_colors_.push_back(rgb_from_hex(hex));
    }
  }
  
  virtual ~BaseAnimation() = default;
  
  virtual std::vector<RGB> render_frame() = 0;
  
  void reset() {
    start_time_ = std::chrono::steady_clock::now();
  }
};

// Static - just shows the gradient
class StaticAnimation : public BaseAnimation {
public:
  using BaseAnimation::BaseAnimation;
  
  std::vector<RGB> render_frame() override {
    std::vector<RGB> frame;
    for (int i = 0; i < led_count_; i++) {
      frame.push_back(get_led_base_color(i));
    }
    return frame;
  }
};

// Breathe - fade in/out
class BreatheAnimation : public BaseAnimation {
  double period_;
  
public:
  BreatheAnimation(int led_count, const std::vector<std::string>& theme_colors, double period = 3.0)
    : BaseAnimation(led_count, theme_colors), period_(period) {}
  
  std::vector<RGB> render_frame() override {
    double t = get_elapsed_time();
    double phase = (t / period_) * 2 * M_PI;
    double brightness = 0.2 + 0.8 * (std::sin(phase) * 0.5 + 0.5);
    
    std::vector<RGB> frame;
    for (int i = 0; i < led_count_; i++) {
      frame.push_back(rgb_scale(get_led_base_color(i), brightness));
    }
    return frame;
  }
};

// Wave - flowing gradient with smooth color transitions
class WaveAnimation : public BaseAnimation {
  double speed_;
  std::vector<RGB> last_frame_;
  double blend_factor_;
  
public:
  WaveAnimation(int led_count, const std::vector<std::string>& theme_colors, double speed = 0.2)
    : BaseAnimation(led_count, theme_colors), speed_(speed), blend_factor_(0.05) {
    // Initialize last_frame with starting colors
    for (int i = 0; i < led_count_; i++) {
      last_frame_.push_back(get_led_base_color(i));
    }
  }
  
  std::vector<RGB> render_frame() override {
    double t = get_elapsed_time();
    double offset = std::fmod(t * speed_, 1.0);
    
    std::vector<RGB> frame;
    for (int i = 0; i < led_count_; i++) {
      double base_position = i / std::max(1.0, static_cast<double>(led_count_ - 1));
      double position = std::fmod(base_position + offset, 1.0);
      RGB target_color = get_color_at_position(position);
      
      // Smoothly interpolate from last frame to target color
      RGB smoothed = rgb_interpolate(last_frame_[i], target_color, blend_factor_);
      frame.push_back(smoothed);
    }
    
    // Store this frame for next iteration
    last_frame_ = frame;
    return frame;
  }
};

// Ripple - expanding wave from center
class RippleAnimation : public BaseAnimation {
  double period_;
  double ripple_width_;
  
public:
  RippleAnimation(int led_count, const std::vector<std::string>& theme_colors, 
                  double period = 2.0, double ripple_width = 0.3)
    : BaseAnimation(led_count, theme_colors), period_(period), ripple_width_(ripple_width) {}
  
  std::vector<RGB> render_frame() override {
    double t = get_elapsed_time();
    double phase = std::fmod(t / period_, 1.5);
    double center = led_count_ / 2.0;
    
    std::vector<RGB> frame;
    for (int i = 0; i < led_count_; i++) {
      double distance = std::abs(i - center) / center;
      double ripple_position = (distance - phase) / ripple_width_;
      
      double intensity = 0.0;
      if (ripple_position >= -1.0 && ripple_position <= 1.0) {
        // Base intensity using cosine for smooth wave shape
        double base_intensity = (std::cos(ripple_position * M_PI) + 1.0) / 2.0;
        
        // Overall cycle ramp-up - when the entire ripple cycle restarts
        double cycle_ramp = 1.0;
        if (phase < 0.2) {
          // Ramp up from 0 to 1 over the first 20% of the cycle
          cycle_ramp = phase / 0.2;
          cycle_ramp = cycle_ramp * cycle_ramp; // Quadratic easing
        }
        
        // Gradual increase at the start of the ripple wave
        // When ripple_position is near -1.0 (start of wave), apply gradual increase
        double start_factor = 0.0;
        if (ripple_position >= -1.0 && ripple_position <= -0.5) {
          // Map ripple_position from [-1.0, -0.5] to [0.0, 1.0] for gradual increase
          start_factor = (ripple_position + 1.0) / 0.5;
          start_factor = start_factor * start_factor; // Quadratic easing for smoother transition
        } else if (ripple_position > -0.5) {
          start_factor = 1.0; // Full intensity after the gradual increase
        }
        
        intensity = base_intensity * start_factor * cycle_ramp;
        
        // Apply fade at the end of the ripple cycle
        double fade = 1.0 - std::max(0.0, std::min(1.0, (phase - 1.0) / 0.5));
        intensity *= fade;
      }
      
      double brightness = 0.3 + 0.7 * intensity;
      frame.push_back(rgb_scale(get_led_base_color(i), brightness));
    }
    return frame;
  }
};

// Runner - shooting stars with trails
class RunnerAnimation : public BaseAnimation {
  double speed_;
  int trail_length_;
  int num_runners_;
  
  struct Runner {
    double position;
    int color_index;
  };
  std::vector<Runner> runners_;
  std::mt19937 rng_;
  
public:
  RunnerAnimation(int led_count, const std::vector<std::string>& theme_colors,
                  double speed = 20.0, int trail_length = 8, int num_runners = 2)
    : BaseAnimation(led_count, theme_colors), speed_(speed), 
      trail_length_(trail_length), num_runners_(num_runners),
      rng_(std::random_device{}()) {
    
    std::uniform_int_distribution<int> color_dist(0, theme_colors_.size() - 1);
    
    // Space runners equally apart
    for (int i = 0; i < num_runners; i++) {
      double spacing = static_cast<double>(led_count) / num_runners;
      double start_pos = i * spacing;
      runners_.push_back({start_pos, color_dist(rng_)});
    }
  }
  
  std::vector<RGB> render_frame() override {
    // Start with dim base gradient
    std::vector<RGB> frame;
    for (int i = 0; i < led_count_; i++) {
      frame.push_back(rgb_scale(get_led_base_color(i), 0.1));
    }
    
    std::uniform_int_distribution<int> color_dist(0, theme_colors_.size() - 1);
    
    for (auto& runner : runners_) {
      double prev_position = runner.position;
      runner.position += speed_ / 30.0; // Assume 30 FPS
      
      // Simple continuous loop - just wrap at led_count
      if (runner.position >= static_cast<double>(led_count_)) {
        runner.position = std::fmod(runner.position, static_cast<double>(led_count_));
        runner.color_index = color_dist(rng_); // Change color on wrap
      }
      
      RGB runner_color = theme_colors_[runner.color_index];
      
      // Render head and trail
      for (int trail_offset = 0; trail_offset < trail_length_; trail_offset++) {
        // Calculate LED position with wrapping
        double trail_pos = runner.position - trail_offset;
        
        // Handle wrapping for trail (can be negative)
        while (trail_pos < 0) trail_pos += led_count_;
        int led_pos = static_cast<int>(trail_pos) % led_count_;
        
        // Brightness falloff: head is brightest, tail fades
        double brightness = static_cast<double>(trail_length_ - trail_offset) / trail_length_;
        brightness = brightness * brightness; // Quadratic falloff
        
        RGB trail_color = rgb_scale(runner_color, brightness);
        RGB& existing = frame[led_pos];
        
        // Additive blending
        existing.r = std::min(255, existing.r + trail_color.r);
        existing.g = std::min(255, existing.g + trail_color.g);
        existing.b = std::min(255, existing.b + trail_color.b);
      }
    }
    
    return frame;
  }
};

// Bounce - segment bouncing back and forth
class BounceAnimation : public BaseAnimation {
  double period_;
  int segment_size_;
  
public:
  BounceAnimation(int led_count, const std::vector<std::string>& theme_colors,
                  double period = 2.0, int segment_size = 5)
    : BaseAnimation(led_count, theme_colors), period_(period), segment_size_(segment_size) {}
  
  std::vector<RGB> render_frame() override {
    double t = get_elapsed_time();
    double phase = (t / period_) * 2 * M_PI;
    double max_pos = std::max(0, led_count_ - segment_size_);
    double position = (std::sin(phase) * 0.5 + 0.5) * max_pos;
    
    std::vector<RGB> frame;
    for (int i = 0; i < led_count_; i++) {
      frame.push_back(rgb_scale(get_led_base_color(i), 0.2));
    }
    
    double color_position = position / std::max(1.0, static_cast<double>(led_count_ - 1));
    RGB bounce_color = get_color_at_position(color_position);
    
    int center = static_cast<int>(std::round(position));
    for (int i = 0; i < segment_size_; i++) {
      int led_pos = center + i;
      if (led_pos >= 0 && led_pos < led_count_) {
        double segment_center = segment_size_ / 2.0;
        double distance_from_center = std::abs(i - segment_center) / segment_center;
        double brightness = 1.0 - (distance_from_center * 0.5);
        
        frame[led_pos] = rgb_scale(bounce_color, brightness);
      }
    }
    
    return frame;
  }
};

// Sparkle - random twinkling
class SparkleAnimation : public BaseAnimation {
  double sparkle_rate_;
  int sparkle_duration_;
  std::map<int, int> sparkles_; // led_index -> frames_remaining
  std::mt19937 rng_;
  
public:
  SparkleAnimation(int led_count, const std::vector<std::string>& theme_colors,
                   double sparkle_rate = 0.1, int sparkle_duration = 15)
    : BaseAnimation(led_count, theme_colors), sparkle_rate_(sparkle_rate),
      sparkle_duration_(sparkle_duration), rng_(std::random_device{}()) {}
  
  std::vector<RGB> render_frame() override {
    std::vector<RGB> frame;
    for (int i = 0; i < led_count_; i++) {
      frame.push_back(rgb_scale(get_led_base_color(i), 0.4));
    }
    
    std::uniform_real_distribution<double> dist(0.0, 1.0);
    
    // Add new sparkles
    for (int i = 0; i < led_count_; i++) {
      if (sparkles_.find(i) == sparkles_.end() && dist(rng_) < sparkle_rate_ / 30.0) {
        sparkles_[i] = sparkle_duration_;
      }
    }
    
    // Update sparkles
    std::vector<int> to_remove;
    for (auto& [led_idx, frames_remaining] : sparkles_) {
      if (frames_remaining <= 0) {
        to_remove.push_back(led_idx);
        continue;
      }
      
      double progress = 1.0 - (static_cast<double>(frames_remaining) / sparkle_duration_);
      double brightness = (progress < 0.5) ? (progress * 2.0) : ((1.0 - progress) * 2.0);
      
      frame[led_idx] = rgb_scale(get_led_base_color(led_idx), brightness);
      sparkles_[led_idx]--;
    }
    
    for (int idx : to_remove) {
      sparkles_.erase(idx);
    }
    
    return frame;
  }
};

// Strobe - fast flashing
class StrobeAnimation : public BaseAnimation {
  double frequency_;
  
public:
  StrobeAnimation(int led_count, const std::vector<std::string>& theme_colors, double frequency = 10.0)
    : BaseAnimation(led_count, theme_colors), frequency_(frequency) {}
  
  std::vector<RGB> render_frame() override {
    double t = get_elapsed_time();
    double phase = std::fmod(t * frequency_, 1.0);
    double brightness = (phase < 0.5) ? 1.0 : 0.0;
    
    std::vector<RGB> frame;
    for (int i = 0; i < led_count_; i++) {
      frame.push_back(rgb_scale(get_led_base_color(i), brightness));
    }
    return frame;
  }
};

// Gradient Shift - smooth color transitions across entire strip
class GradientShiftAnimation : public BaseAnimation {
  double period_;
  double shift_amount_;
  
public:
  GradientShiftAnimation(int led_count, const std::vector<std::string>& theme_colors,
                         double period = 10.0, double shift_amount = 1.0)
    : BaseAnimation(led_count, theme_colors), period_(period), shift_amount_(shift_amount) {}
  
std::vector<RGB> render_frame() override {
    double t = get_elapsed_time();
    // Create continuous cycling shift (0.0 to shift_amount_)
    double shift = std::fmod(t / period_, 1.0) * shift_amount_;
    
    std::vector<RGB> frame;
    for (int i = 0; i < led_count_; i++) {
      double base_position = i / std::max(1.0, static_cast<double>(led_count_ - 1));
      double raw_position = base_position + shift;
      
      RGB color;
      
      // Handle smooth wrapping for all positions
      if (raw_position >= 1.0) {
        // We've wrapped around - need smooth transition
        double wrapped_pos = raw_position - std::floor(raw_position);
        
        // Create a larger transition zone to catch the last pixel
        double transition_width = 0.25; // 25% of gradient for smooth transition
        
        if (wrapped_pos < transition_width) {
          // Smooth blend from last color to first color
          double blend_factor = wrapped_pos / transition_width;
          blend_factor = blend_factor * blend_factor; // Quadratic easing
          
          RGB last_color = get_color_at_position(0.98); // Very near end
          RGB first_color = get_color_at_position(wrapped_pos);
          color = rgb_interpolate(last_color, first_color, blend_factor);
        } else {
          color = get_color_at_position(wrapped_pos);
        }
      } else {
        // Check if we're near the end and about to wrap
        double distance_to_end = 1.0 - raw_position;
        double pre_wrap_zone = 0.1; // 10% before wrap for anticipation
        
        if (distance_to_end < pre_wrap_zone && theme_colors_.size() >= 2) {
          // Start blending early to prevent sudden change
          double blend_factor = 1.0 - (distance_to_end / pre_wrap_zone);
          blend_factor = blend_factor * blend_factor; // Quadratic easing
          
          RGB current_color = get_color_at_position(raw_position);
          RGB next_color = theme_colors_.front(); // First color in theme
          color = rgb_interpolate(current_color, next_color, blend_factor * 0.3); // Subtle anticipation
        } else {
          color = get_color_at_position(raw_position);
        }
      }
      
      frame.push_back(color);
    }
    return frame;
  }
};

// Drift - each LED independently drifts through gradient with optional twinkle
class DriftAnimation : public BaseAnimation {
  struct LEDState {
    double gradient_position;  // Current position on gradient (0.0 to 1.0)
    double speed;              // How fast this LED cycles (positions per second)
    double twinkle_phase;      // Random phase offset for twinkle effect
  };
  
  std::vector<LEDState> led_states_;
  double twinkle_intensity_;
  std::mt19937 rng_;
  
public:
  DriftAnimation(int led_count, const std::vector<std::string>& theme_colors, 
                 double min_speed = 0.3, double max_speed = 10.0, double twinkle = 0.0)
    : BaseAnimation(led_count, theme_colors), twinkle_intensity_(twinkle), rng_(std::random_device{}()) {
    
    std::uniform_real_distribution<double> position_dist(0.0, 1.0);
    // Convert seconds to positions per second (inverse)
    std::uniform_real_distribution<double> speed_dist(1.0 / max_speed, 1.0 / min_speed);
    std::uniform_real_distribution<double> phase_dist(0.0, 2.0 * M_PI);
    
    // Initialize each LED with random starting position, speed, and twinkle phase
    for (int i = 0; i < led_count_; i++) {
      led_states_.push_back({
        position_dist(rng_),
        speed_dist(rng_),
        phase_dist(rng_)
      });
    }
  }
  
  std::vector<RGB> render_frame() override {
    double t = get_elapsed_time();
    std::vector<RGB> frame;
    
    for (int i = 0; i < led_count_; i++) {
      auto& state = led_states_[i];
      
      // Update gradient position for this LED
      state.gradient_position = std::fmod(state.gradient_position + state.speed / 30.0, 1.0);
      
      // Get base color from gradient
      RGB color = get_color_at_position(state.gradient_position);
      
      // Apply twinkle effect if intensity > 0
      if (twinkle_intensity_ > 0.0) {
        // Create subtle brightness variation using sine wave
        double twinkle_variation = twinkle_intensity_ * std::sin(t * 3.0 + state.twinkle_phase);
        double twinkle_factor = 1.0 - (twinkle_intensity_ * 0.5) + (twinkle_variation * 0.5);
        color = rgb_scale(color, twinkle_factor);
      }
      
      frame.push_back(color);
    }
    
    return frame;
  }
};

} // namespace forgeworklights
