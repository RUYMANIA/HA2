#pragma once
#include <cstdint>
namespace ha2 {
// One admission per boot after a real HA native client, bounded local-time readiness.
// No STOP, volume changes, wake control, network probing, or delayed dawn playback.
struct Startup {
 enum class State:uint8_t { New, Waiting, Playing, Done };
 State state{State::New};
 uint32_t admitted_at{0},play_at{0},base_frames{0},frames{0};
 uint32_t admitted{0},started{0},finished{0},skipped{0},timeouts{0};
 uint8_t reason{0};bool announced{false};
 void connect(bool ha,uint32_t now){if(ha && state==State::New){state=State::Waiting;admitted_at=now;++admitted;}}
 void skip(uint8_t why){state=State::Done;reason=why;++skipped;}
 bool tick(uint32_t now,bool ha,bool valid,bool night,bool enabled,bool safe,uint32_t dma){
  if(state==State::Playing){if(uint32_t(now-play_at)>=12000u){state=State::Done;++timeouts;}return false;}
  if(state!=State::Waiting)return false;
  if(!enabled){skip(1);return false;}
  if(valid && night){skip(2);return false;}
  if(uint32_t(now-admitted_at)>=15000u){skip(valid?4:3);return false;}
  if(!ha || !valid || uint32_t(now-admitted_at)<2000u)return false;
  if(!safe){skip(5);return false;}
  state=State::Playing;play_at=now;base_frames=dma;announced=false;++started;return true;
 }
 bool owns()const{return state==State::Playing;}
 void announcement(){if(owns())announced=true;}
 void idle(uint32_t dma){if(owns() && announced){frames=uint32_t(dma-base_frames);++finished;state=State::Done;}}
};
inline Startup &startup(){static Startup value;return value;}
}
