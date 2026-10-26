#pragma once
#include <cstdint>
namespace hermes_avatar {
// Stores no image data. The approved GIF delays determine the timeline.
class Timeline {
 public:
  bool update(uint32_t now, int state, const uint16_t* delays, uint8_t count) {
    const int old_frame = frame_;
    const int old_state = state_;
    if (state < 0 || delays == nullptr || count == 0) {
      state_ = -1; frame_ = -1;
      return old_state != -1 || old_frame != -1;
    }
    if (state != state_) { state_ = state; epoch_ = now; }
    uint32_t cycle = 0;
    for (uint8_t i = 0; i < count; ++i) cycle += delays[i];
    uint32_t offset = (now - epoch_) % cycle;
    frame_ = 0;
    while (frame_ < count - 1 && offset >= delays[frame_]) {
      offset -= delays[frame_]; ++frame_;
    }
    return frame_ != old_frame || state_ != old_state;
  }
  int frame() const { return frame_; }
  int state() const { return state_; }
 private:
  int state_{-1};
  int frame_{-1};
  uint32_t epoch_{0};
};
inline Timeline& timeline() {
  static Timeline instance;
  return instance;
}
}  // namespace hermes_avatar
