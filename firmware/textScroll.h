#pragma once
#include <algorithm>
#include <array>
#include <cstdint>
#include <string>
#include <atomic>
#ifdef ESP_PLATFORM
#include <freertos/FreeRTOS.h>
#include <freertos/portmacro.h>
#endif
#include "temporary_cards.h"
namespace text_scroll {
// Pixel progression, not word timestamps. Inject actual audio elapsed via offset_elapsed.
struct Scroll {
 uint32_t started_at{0},duration{0},paused_at{0},paused_total{0};
 int overflow{0};bool paused{false};
 void reset(uint32_t now,int content,int viewport,uint32_t total){started_at=now;duration=total;overflow=std::max(0,content-viewport);paused=false;paused_total=0;}
 uint32_t elapsed(uint32_t now)const{return uint32_t((paused?paused_at:now)-started_at)-paused_total;}
 int offset_elapsed(uint32_t elapsed_ms)const{
  const uint32_t lead=duration?std::min<uint32_t>(2000u,duration/3):2000u;
  if(elapsed_ms<=lead)return 0;
  if(duration)return int(std::min<uint64_t>(overflow,uint64_t(elapsed_ms-lead)*overflow/std::max<uint32_t>(1u,duration-lead)));
  return int(std::min<uint64_t>(overflow,uint64_t(elapsed_ms-lead)*16/1000));
 }
 int offset(uint32_t now)const{return offset_elapsed(elapsed(now));}
 bool ended(uint32_t now)const{return offset(now)>=overflow;}
 void pause(uint32_t now){if(!paused){paused_at=now;paused=true;}}
 void resume(uint32_t now){if(paused){paused_total+=uint32_t(now-paused_at);paused=false;}}
};
struct Timing {
 struct Entry{std::string message;uint32_t duration{0},at{0};uint64_t generation{0};};
 std::array<Entry,4> entries;size_t next{0};uint64_t generation{0};
 void next_generation(){++generation;for(auto&e:entries)e=Entry{};}
 bool put(const std::string &message,int duration,uint32_t now){
  if(message.empty() || message.size()>4096 || duration<=0 || duration>600000)return false;
  // An updated exact metadata record replaces the previous one, never duplicates it.
  for(auto&e:entries)if(e.message==message){e={message,uint32_t(duration),now,generation};return true;}
  entries[next]={message,uint32_t(duration),now,generation};next=(next+1)%4;return true;
 }
 uint32_t take(const std::string &message,uint32_t now){
  uint32_t duration=0;
  for(auto&e:entries){
   if(e.generation!=generation || uint32_t(now-e.at)>=120000){e=Entry{};continue;}
   if(e.message==message){duration=e.duration;e=Entry{};}
  }return duration;
 }
};
#ifdef ESP_PLATFORM
// Xtensa's std::atomic<uint32_t> is not guaranteed lock-free in the installed toolchain.
// The DMA callback runs in the speaker task, not an ISR. Copy/add one 32-bit scalar only.
struct FrameCounter {
 portMUX_TYPE mux=portMUX_INITIALIZER_UNLOCKED;uint32_t value{0};
 uint32_t load(std::memory_order =std::memory_order_relaxed){portENTER_CRITICAL(&mux);const auto v=value;portEXIT_CRITICAL(&mux);return v;}
 void fetch_add(uint32_t n,std::memory_order =std::memory_order_relaxed){portENTER_CRITICAL(&mux);value+=n;portEXIT_CRITICAL(&mux);}
};
#else
using FrameCounter=std::atomic<uint32_t>;
#endif
inline FrameCounter &frames(){static FrameCounter n{};return n;}
inline bool matches(const std::string &full,const std::string &raw){return full==raw || (full.size()>500 && raw.size()==500 && raw==full.substr(0,497)+"...");}
struct Playback {
 Scroll scroll;std::string text,raw;
 uint32_t real_duration{0},baseline{0},prepared_at{0},final_elapsed{0};
 int last_offset{0};bool confirmed{false},active{false},attributable{false};
 bool uri_ready{false},announced{false};float player_volume{0};bool player_muted{false};
 void revoke_audio(){final_elapsed=0;attributable=false;}
 void uri(const std::string &url,bool clean){if(active && attributable && !uri_ready && !announced && clean && temporary_cards::valid_url(url))uri_ready=true;else revoke_audio();}
 void announcement(float volume,bool muted,bool timer){
  if(timer || !active || !uri_ready){revoke_audio();return;}
  if(announced){
   // Public state publications also occur for volume/mute changes. Only those
   // observable changes are benign; identical duplicate announcements fail closed.
   if(volume==player_volume && muted==player_muted)revoke_audio();
  }else {announced=true;baseline=frames().load(std::memory_order_relaxed);}
  player_volume=volume;player_muted=muted;
 }
 void begin(const std::string &value,uint32_t now,uint32_t frame_baseline,bool clean){
  raw=value;bool cap=false;text=temporary_cards::bounded(value,4000,4096,false,cap);
  uri_ready=false;announced=false;player_volume=0;player_muted=false;
  baseline=frame_baseline;prepared_at=now;real_duration=0;confirmed=false;active=true;attributable=clean;last_offset=0;final_elapsed=0;scroll.reset(now,0,0,0);
 }
 bool metadata(const std::string &full,int duration,uint32_t now){
  if(confirmed || !active || !attributable || uint32_t(now-prepared_at)>=120000 || duration<=0 || duration>600000 || full.size()>4096 || !temporary_cards::valid_utf8(full) || !matches(full,raw))return false;
  bool cap=false;text=temporary_cards::bounded(full,4000,4096,false,cap);real_duration=duration;confirmed=true;scroll.duration=duration;return true;
 }
 void start(const std::string &value,uint32_t now,uint32_t duration){begin(value,now,frames().load(std::memory_order_relaxed),true);if(duration)metadata(value,duration,now);}
 void geometry(int width,int viewport){scroll.overflow=std::max(0,width-viewport);}
 uint32_t elapsed(uint32_t frame_count)const{return !attributable?0:(active?uint32_t(uint64_t(uint32_t(frame_count-baseline))*1000/48000):final_elapsed);}
 int offset(uint32_t frame_count){if(!attributable)return 0;last_offset=std::max(last_offset,scroll.offset_elapsed(elapsed(frame_count)));return std::min(last_offset,scroll.overflow);}
 void stop(uint32_t /*now*/){final_elapsed=elapsed(frames().load(std::memory_order_relaxed));active=false;}
};
inline bool apply_pending(Playback &p,Timing &t,uint32_t now){
 size_t count=0;
 for(auto &e:t.entries){
  if(e.generation!=t.generation || uint32_t(now-e.at)>=120000){e=Timing::Entry{};continue;}
  if(matches(e.message,p.raw))++count;
 }
 bool adopted=false;
 for(auto &e:t.entries)if(matches(e.message,p.raw)){
  if(count==1)adopted=p.metadata(e.message,e.duration,now);
  e=Timing::Entry{}; // Drop all ambiguous prefixes; never guess which full string was spoken.
 }
 return adopted;
}
struct Transcript {
 std::string raw,text,pending;uint32_t at{0},pending_at{0};
 void new_turn(){raw.clear();text.clear();pending.clear();}
 void receive(const std::string &value,uint32_t now){
  raw=value;at=now;bool cap=false;text=temporary_cards::bounded(value,4000,4096,false,cap);
  if(!pending.empty() && uint32_t(now-pending_at)<5000 && matches(pending,raw))text=pending;
  pending.clear();
 }
 bool metadata(const std::string &full,uint32_t now){
  if(full.size()>4096 || !temporary_cards::valid_utf8(full))return false;
  bool cap=false;const auto bounded=temporary_cards::bounded(full,4000,4096,false,cap);
  if(raw.empty() || raw=="..."){pending=bounded;pending_at=now;return false;}
  if(uint32_t(now-at)>=5000 || !matches(full,raw))return false;
  text=bounded;return true;
 }
};
inline Transcript &transcript(){static Transcript t;return t;}
inline Timing &timing(){static Timing t;return t;}
inline Playback &playback(){static Playback p;return p;}
inline Scroll &stt(){static Scroll s;return s;}
inline Scroll &card(){static Scroll s;return s;}
inline Scroll &history(){static Scroll s;return s;}
}
