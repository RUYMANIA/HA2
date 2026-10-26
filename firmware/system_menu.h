#pragma once
#include <cstdint>
#include <algorithm>
#include <cmath>
#include <string>
#include <vector>
namespace system_menu {
// No connectivity dependency: local settings stay accessible without HA/Wi-Fi.
inline bool can_open(bool boot,bool timer,int phase) {
  return !boot && !timer && phase!=2 && phase!=3 && phase!=4 && phase!=11 && phase!=20;
}
struct Rect {
  int x,y,w,h;
  bool contains(int px,int py) const { return px>=x && py>=y && px<x+w && py<y+h; }
};
inline constexpr Rect BUTTONS[]={{32,73,36,64},{172,73,36,64},{76,167,89,27},{74,197,93,28}};
inline constexpr Rect EXIT_ACTION{42,52,156,40};
inline constexpr Rect RESTART_ACTION{42,100,156,40};
inline constexpr Rect DEMO_ACTION{42,148,156,40};
inline bool inside_circle(int x,int y) {
  if (x<0 || y<0 || x>=240 || y>=240) return false;
  const int dx=x-120,dy=y-120; return dx*dx+dy*dy<=118*118;
}
// Sanitize invalid UTF-8 and controls, then remove complete codepoints only.
// ASCII three-dot ellipsis is available in the existing fonts.
template<class Measure> std::string ellipsize(const std::string &input,int width,Measure measure) {
  std::string text;
  std::vector<size_t> ends;
  for (size_t i=0;i<input.size();) {
    const unsigned char c=input[i];
    size_t n=c<128?1:(c>=194 && c<=223?2:(c>=224 && c<=239?3:(c>=240 && c<=244?4:0)));
    bool valid=n && i+n<=input.size();
    if (valid) for(size_t j=1;j<n;++j) if ((static_cast<unsigned char>(input[i+j])&192)!=128) valid=false;
    if(valid && n>=3) {
      const unsigned char d=input[i+1];
      if((c==224 && d<160)||(c==237 && d>=160)||(c==240 && d<144)||(c==244 && d>=144)) valid=false;
    }
    if (!valid) { text+='?'; ++i; }
    else { if(c<32 || c==127) text+='?'; else text.append(input,i,n); i+=n; }
    ends.push_back(text.size());
  }
  if(measure(text)<=width) return text;
  if(measure("...")>width) return "";
  while(!ends.empty()) {
    ends.pop_back(); text.resize(ends.empty()?0:ends.back());
    if(measure(text+"...")<=width) return text+"...";
  }
  return "...";
}
enum class Event { Legacy, Consumed, Open, Minus, Plus, Page, Close, Previous, Next, Select0, Select1, Select2, Select3, NightToggle, NightStartMinus, NightStartPlus, NightEndMinus, NightEndPlus, Restart, DemoStart, DemoCancel };
struct Controller {
  bool active{false};
  bool demo_active{false};
  int page{0};
  bool pending{false};
  uint32_t touched_at{0};
  uint32_t reading_at{0},reading_ms{0};
  void reading_until(uint32_t now,uint32_t duration){reading_at=now;reading_ms=std::min<uint32_t>(duration,6000000u);}
  void open(uint32_t now) { active = true; demo_active=false; page = 5; touched_at = now; }
  void close() { active = false; demo_active=false; if(tracking_) owned_=true; }
  bool tick(uint32_t now) {
    if(pending && uint32_t(now-requested_)>=1500) pending=false;
    const bool reading=page==2 && reading_ms && uint32_t(now-reading_at)<reading_ms;
    if(active && !demo_active && !reading && uint32_t(now-touched_at)>=(page==5?60000u:20000u)) { close(); return true; }
    return false;
  }
  bool request_volume(int direction,float confirmed,uint32_t now,float &target) {
    if(pending || !std::isfinite(confirmed) || (direction!=1 && direction!=-1)) return false;
    target=std::clamp(confirmed+direction*0.05f,0.0f,1.0f);
    if(std::fabs(target-confirmed)<0.0001f) return false;
    target_=target; requested_=now; pending=true; return true;
  }
  void confirm_volume(float value) {
    if(pending && std::isfinite(value) && std::fabs(value-target_)<0.001f) pending=false;
  }
  void begin(int x, int y, uint32_t now) {
    tracking_ = true; owned_ = active; x0_ = x_ = x; y0_ = y_ = y;
    began_ = now; max_dist2_ = 0;
    demo_contact_=demo_active;
    if(demo_contact_) { demo_active=false;page=8;touched_at=now; }
  }
  void move(int x, int y) {
    if (!tracking_) return;
    x_ = x; y_ = y;
    const int dx=x-x0_, dy=y-y0_;
    max_dist2_ = std::max(max_dist2_, dx*dx+dy*dy);
  }
  Event swipe(int direction,uint32_t now) {
    if(demo_active) { demo_active=false; page=8; touched_at=now; return Event::DemoCancel; }
    if(!active || (direction!=1 && direction!=-1)) return Event::Consumed;
    static constexpr int order[]={5,7,2,0,3,4,6,1,8};
    int index=0;for(int i=0;i<9;++i)if(order[i]==page)index=i;
    touched_at=now; page=order[(index+direction+9)%9]; return Event::Page;
  }
  Event tap(int x, int y, uint32_t now) {
    if(demo_active) { demo_active=false; page=8; touched_at=now; return Event::DemoCancel; }
    if (!active || !inside_circle(x,y)) return Event::Consumed;
    touched_at = now;
    if (page==8 && EXIT_ACTION.contains(x,y)) { close(); return Event::Close; }
    if (page==8 && RESTART_ACTION.contains(x,y)) return Event::Restart;
    if (page==8 && DEMO_ACTION.contains(x,y)) return Event::DemoStart;
    if(Rect{8,103,22,34}.contains(x,y))return swipe(-1,now);
    if(Rect{210,103,22,34}.contains(x,y))return swipe(1,now);
    if(page==6){
      if(Rect{52,48,136,30}.contains(x,y))return Event::NightToggle;
      if(Rect{42,96,38,36}.contains(x,y))return Event::NightStartMinus;
      if(Rect{160,96,38,36}.contains(x,y))return Event::NightStartPlus;
      if(Rect{42,148,38,36}.contains(x,y))return Event::NightEndMinus;
      if(Rect{160,148,38,36}.contains(x,y))return Event::NightEndPlus;
    }

    if (page==0) {
      if (BUTTONS[0].contains(x,y)) return Event::Minus;
      if (BUTTONS[1].contains(x,y)) return Event::Plus;
    }
    if(page==2 && Rect{51,188,68,28}.contains(x,y))return Event::Previous;
    if(page==2 && Rect{121,188,68,28}.contains(x,y))return Event::Next;
    if(page==7 && x>=46 && x<194 && y>=72 && y<188 && (y-72)%64<52)
      return static_cast<Event>(static_cast<int>(Event::Select0)+(y-72)/64);
    if((page==3 || page==4) && x>=46 && x<194 && y>=54 && y<210 && (y-54)%40<36)
      return static_cast<Event>(static_cast<int>(Event::Select0)+(y-54)/40);
    return Event::Consumed;
  }
  Event release(uint32_t now, bool allowed) {
    if (!tracking_) return Event::Consumed;
    tracking_ = false;
    const uint32_t dt=now-began_;
    // A demo owns the whole contact, including long presses and swipes.
    if(demo_contact_ || demo_active) { demo_contact_=false; demo_active=false; page=8; touched_at=now; return Event::DemoCancel; }
    if (owned_ || active) {
      const int dx=x_-x0_,dy=y_-y0_;
      if(active && dt<=1500 && std::abs(dx)>=30 && std::abs(dx)>std::abs(dy)) return swipe(dx>0?1:-1,now);
      if (active && max_dist2_<=144 && dt<=700) return tap(x_,y_,now);
      return Event::Consumed;
    }
    if (dt>=900 && max_dist2_<=144) {
      if (allowed) { open(now); return Event::Open; }
      return Event::Consumed;
    }
    // An excursion that returned to its origin must not become a legacy tap.
    const int dx=x_-x0_,dy=y_-y0_;
    if (max_dist2_>400 && dx*dx+dy*dy<=400) return Event::Consumed;
    return Event::Legacy;
  }
 private:
  bool tracking_{false}, owned_{false}, demo_contact_{false};
  int x0_{0},y0_{0},x_{0},y_{0},max_dist2_{0};
  uint32_t began_{0}, requested_{0};
  float target_{0};
};
inline Controller &state() { static Controller value; return value; }
}
