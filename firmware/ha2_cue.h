#pragma once
#include <cstdint>
namespace ha2 {
// Bounded visual-card cue, never a voice-assistant/TTS owner. No strings/audio buffers.
struct Cue {
 uint64_t candidate{0},owner{0};
 uint32_t accepted_at{0},owner_at{0},played{0},suppressed_night{0},expired{0};
 bool announced{false};
 void accept(uint64_t generation,bool spoken,bool night,uint32_t now){
  candidate=0;
  if(spoken)return;
  if(night){++suppressed_night;return;}
  candidate=generation;accepted_at=now;
 }
 // Bound file-loading separately from 940 ms output. Only the first callback
 // starts the output lease: repaints/duplicate announcements cannot extend it.
 bool owns(uint64_t generation,uint32_t now)const{return owner && owner==generation && uint32_t(now-owner_at)<(announced?1200u:3000u);}
 void announcement(uint32_t now){if(owner && !announced){announced=true;owner_at=now;}}
 void idle(){owner=0;announced=false;}
 bool enter(uint64_t generation,bool visible,bool safe_idle,bool night,uint32_t now){
  if(owner && !owns(owner,now))idle();
  if(!candidate)return false;
  if(night){candidate=0;++suppressed_night;return false;}
  if(uint32_t(now-accepted_at)>=120000u){candidate=0;++expired;return false;}
  if(candidate!=generation || !visible || !safe_idle || owner)return false;
  owner=candidate;candidate=0;owner_at=now;announced=false;++played;return true;
 }
};
inline Cue &cue(){static Cue value;return value;}
}
