#pragma once
#include <cstdint>
#include <string>
#include "temporary_cards.h"
#include "textScroll.h"
#include "night_mode.h"
#include "ha2_cue.h"
namespace ui_v3 {
struct Power {
 int sleep_index{0},auto_index{0};
 bool awake{true},was_busy{false},touch_owned{false};
 uint32_t activity_at{0},wakes{0},sleeps{0},auto_count{0};
 int64_t last_auto_epoch{-1};
 std::string cause{"boot"};
 NightState night;
 bool night_active{false},manual_override{false};
 uint32_t manual_at{0},blocked_by_night{0},night_sleeps{0},persist_changes{0};
 void dark(const char* why){if(awake)++sleeps;awake=false;cause=why;}
 uint32_t manual_timeout()const{return timeout()?timeout():60000u;}
 void enforce_night(uint32_t now){
  if(!night_active)return;
  if(manual_override && uint32_t(now-manual_at)>=manual_timeout())manual_override=false;
  if(!manual_override && awake){dark("night");++night_sleeps;}
 }
 void apply_night(uint32_t now,bool valid,int minute){
  const bool active=night.contains(valid,minute);
  if(active!=night_active)manual_override=false;
  night_active=active;enforce_night(now);
 }
 void refresh_night(uint32_t now){if(clock_reader()){const auto c=clock_reader()();apply_night(now,c.valid,c.minute);}else enforce_night(now);}
 uint32_t timeout()const {return sleep_index==3?0u:(sleep_index==1?180000u:(sleep_index==2?300000u:60000u));}
 void wake(uint32_t now,const char* why){
  refresh_night(now);
  const std::string reason=why;
  const bool manual=reason=="touch" || reason=="menu" || reason=="manual";
  if(night_active && !manual){++blocked_by_night;return;}
  if(manual && night_active){manual_override=true;manual_at=now;}
  if(!awake)++wakes;awake=true;activity_at=now;cause=why;
 }
 void sleep(uint32_t /*now*/){if(sleep_index==3 && !night_active)return;manual_override=false;dark("sleep");}
 void touch_begin(uint32_t now){refresh_night(now);touch_owned=!awake;wake(now,"touch");}
 bool consume_touch(uint32_t /*now*/){const bool result=touch_owned;touch_owned=false;return result;}
 void tick(uint32_t now,bool busy){
  refresh_night(now);
  if(night_active){was_busy=busy;return;}
  if(sleep_index==3){if(!awake)wake(now,"sleep_disabled");}
  if(busy){if(!was_busy || !awake)wake(now,"busy");activity_at=now;}
  else if(was_busy)activity_at=now;
  was_busy=busy;
  if(awake && !busy && timeout() && uint32_t(now-activity_at)>=timeout())sleep(now);
 }
 bool auto_wake(uint32_t now,bool valid,int64_t epoch,int minute,int second){
  refresh_night(now);
  if(night_active){if(valid && second==0)++blocked_by_night;return false;}
  if(!valid || auto_index==3 || second!=0 || minute%(auto_index==0?15:(auto_index==1?30:60))!=0)return false;
  const int64_t slot=epoch-epoch%60;
  if(slot<=last_auto_epoch)return false;
  last_auto_epoch=slot;
  if(sleep_index==3)return false;
  ++auto_count;wake(now,"clock");return true;
 }
};
inline const char* page_name(int page){static const char* names[]={"volume","info","history","sleep","auto_wake","project","night","language","exit"};return page>=0&&page<9?names[page]:"closed";}
inline const char* sleep_option(int i){static const char* options[]={"1 minuto","3 minutos","5 minutos","Desactivado"};return options[std::clamp(i,0,3)];}
inline const char* auto_option(int i){static const char* options[]={"Cada 15 min","Cada 30 min","Cada 60 min","Desactivado"};return options[std::clamp(i,0,3)];}
inline int line_height(int font_height){return std::max(18,font_height+2);}
inline std::string &stt_text(){return text_scroll::transcript().text;}
inline uint32_t &voice_revision(){static uint32_t r=0;return r;}
inline bool &gif_pass(){static bool rendering=false;return rendering;}
struct HistoryView {
 temporary_cards::LineTable lines;std::string title;
 uint64_t revision{uint64_t(-1)};size_t index{size_t(-1)};
 void invalidate(){revision=uint64_t(-1);}
 template<class TitleMeasure,class BodyMeasure>bool prepare(temporary_cards::Controller &c,TitleMeasure tm,BodyMeasure bm,uint32_t now,int height){
  if(revision==c.history_revision && index==c.history_index)return false;
  revision=c.history_revision;index=c.history_index;lines.clear();title.clear();
  if(c.history_count){
   temporary_cards::Controller helper;helper.active=c.history[c.history_index];helper.layout(tm,bm);
   lines=std::move(helper.lines);title=std::move(helper.display_title);
  }
  text_scroll::history().reset(now,lines.size()*height,98,0);return true;
 }
};
inline HistoryView &view(){static HistoryView v;return v;}
inline Power &power(){static Power p;return p;}
inline bool &night_edit(){static bool editing=false;return editing;}
}
