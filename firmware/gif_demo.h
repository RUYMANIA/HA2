#pragma once
#include <cstdint>
namespace hermes_avatar {
// Observes the real timeline and only counts fully rendered cycles.
// It owns no audio, preferences, voice phase, network state or card data.
struct Demo {
  bool active{false};
  int index{0};
  unsigned loops{0};
  uint8_t seen{0};
  int last{-1};
  void start(){active=true;index=0;loops=0;seen=0;last=-1;}
  void cancel(){active=false;}
  bool boundary(int frame){
    if(!active || frame!=0 || last!=7)return false;
    const bool complete=seen==255;
    seen=0;last=-1;
    if(!complete)return false;
    if(++loops<2)return false;
    loops=0;seen=0;last=-1;
    if(++index==11)active=false;
    return true;
  }
  void rendered(int frame){if(active && frame>=0 && frame<8){seen|=uint8_t(1u<<frame);last=frame;}}
};
inline Demo &demo(){static Demo value;return value;}
}
