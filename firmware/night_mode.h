#pragma once
#include <cstdint>
namespace ui_v3 {
struct NightState {
 bool enabled{true};
 uint8_t start{92},end{28};
 bool contains(bool valid,int minute)const {
  if(!enabled || !valid || minute<0 || minute>=1440)return false;
  const int a=int(start)*15,b=int(end)*15;
  if(a==b)return true;
  return a<b?(minute>=a && minute<b):(minute>=a || minute<b);
 }
};
struct LocalClock {bool valid;int minute;};
using ClockReader=LocalClock(*)();
inline ClockReader &clock_reader(){static ClockReader reader=nullptr;return reader;}
}
