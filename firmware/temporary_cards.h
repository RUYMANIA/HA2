#pragma once
// Pure host-testable state; all times are wrap-safe monotonic uint32 milliseconds.
#include <algorithm>
#include <cstdint>
#include <string>
#include <vector>
#include <array>
namespace temporary_cards {
inline bool valid_id(const std::string &s) {
  if(s.size()!=32) return false;
  for(char c:s) if(!((c>='0'&&c<='9')||(c>='a'&&c<='f'))) return false;
  return true;
}
inline bool is_marker(const std::string &s) { return s.size()==47 && s.compare(0,15,"__hermes_card__")==0 && valid_id(s.substr(15)); }
inline bool valid_url(const std::string &url) {
  const std::string prefix="http://192.0.2.10:8123/api/tts_proxy/";
  if(url.compare(0,prefix.size(),prefix)!=0 || url.size()<=prefix.size() || url.size()>384) return false;
  const auto token=url.substr(prefix.size());
  if(token.find("..")!=std::string::npos) return false;
  for(char c:token) if(!((c>='a'&&c<='z')||(c>='A'&&c<='Z')||(c>='0'&&c<='9')||c=='-'||c=='_'||c=='.')) return false;
  return true;
}
inline bool valid_kind(const std::string &s) {
  return s=="reminder" || s=="weather" || s=="result" || s=="notice";
}
inline size_t utf8_length(const std::string &s,size_t i) {
  const unsigned char c=s[i];
  const size_t n=c<128?1:(c>=194&&c<=223?2:(c>=224&&c<=239?3:(c>=240&&c<=244?4:0)));
  if(!n || i+n>s.size()) return 0;
  for(size_t j=1;j<n;++j) if((static_cast<unsigned char>(s[i+j])&192)!=128) return 0;
  if(n>=3) {
    const unsigned char d=s[i+1];
    if((c==224&&d<160)||(c==237&&d>=160)||(c==240&&d<144)||(c==244&&d>=144)) return 0;
  }
  return n;
}
inline bool valid_utf8(const std::string &s) {
  for(size_t i=0;i<s.size();) { const size_t n=utf8_length(s,i); if(!n) return false; i+=n; }
  return true;
}
inline std::string bounded(const std::string &s,size_t cps,size_t bytes,bool multiline,bool &changed) {
  std::string out; size_t count=0;
  for(size_t i=0;i<s.size();) {
    const size_t n=utf8_length(s,i);
    std::string cp=n?s.substr(i,n):"?";
    if(!n) changed=true;
    if(cp.size()==1 && ((static_cast<unsigned char>(cp[0])<32 && !(multiline&&cp[0]=='\n')) || cp[0]==127)) { cp=" "; changed=true; }
    if(count>=cps || out.size()+cp.size()>bytes) { changed=true; break; }
    out+=cp; ++count; i+=n?n:1;
  }
  return out;
}
inline void pop_cp(std::string &s) {
  if(s.empty()) return;
  size_t i=s.size()-1; while(i && (static_cast<unsigned char>(s[i])&192)==128) --i;
  s.resize(i);
}
template<class Measure> inline std::string fit(std::string s,int width,Measure measure,bool &changed,bool force=false) {
  if(!force && measure(s)<=width) return s;
  changed=true;
  while(!s.empty() && measure(s+"...")>width) pop_cp(s);
  return measure(s+"...")<=width?s+"...":"";
}
struct Card {
  std::string id,title,text,kind,state{"idle"},reason{"none"},audio{"none"};
  uint32_t accepted{0},ttl{30000};
  uint64_t generation{0};
  bool truncated{false},audio_expected{false},visible{false};
};
// Compact bounded line storage: at most 4096 text bytes + 4000 uint16 ends,
// rather than 4000 separate heap-allocated std::strings for newline-heavy input.
struct LineTable {
 std::string data;std::vector<uint16_t> ends;
 void clear(){data.clear();ends.clear();}
 void push_back(const std::string &line){data+=line;ends.push_back(static_cast<uint16_t>(data.size()));}
 size_t size()const{return ends.size();}bool empty()const{return ends.empty();}
 std::string operator[](size_t i)const{const size_t begin=i?ends[i-1]:0;return data.substr(begin,ends[i]-begin);}
 std::string back()const{return (*this)[size()-1];}
 size_t storage_bytes()const{return data.capacity()+ends.capacity()*sizeof(uint16_t);}
 struct Iterator{const LineTable*table;size_t i;std::string operator*()const{return (*table)[i];}void operator++(){++i;}bool operator!=(const Iterator&o)const{return i!=o.i;}};
 Iterator begin()const{return {this,0};}Iterator end()const{return {this,size()};}
};
struct Controller {
  std::array<Card,5> history;
  size_t history_count{0},history_index{0};
  bool history_step(int direction){
    if(!history_count || (direction!=1 && direction!=-1))return false;
    history_index=static_cast<size_t>((static_cast<int>(history_index)+static_cast<int>(history_count)+direction)%static_cast<int>(history_count));return true;
  }
  uint64_t history_revision{0},layout_generation{0};
  Card active,pending,status;
  uint64_t generation{0};
  LineTable lines;
  std::string display_title;
  template<class TitleMeasure,class BodyMeasure> void layout(TitleMeasure title_measure,BodyMeasure measure) {
    if(layout_generation==active.generation && active.generation) return;
    layout_generation=active.generation;
    bool cosmetic=false;
    display_title=fit(active.title,156,title_measure,cosmetic);
    lines.clear(); size_t i=0;
    while(i<active.text.size()) {
      std::string line; size_t word=std::string::npos,word_next=i;
      while(i<active.text.size() && active.text[i]!='\n') {
        const size_t n=utf8_length(active.text,i);
        const std::string cp=active.text.substr(i,n);
        if(measure(line+cp)>176) {
          if(word!=std::string::npos) { line.resize(word); i=word_next; }
          else if(line.empty()) { line+=cp; i+=n; }
          break;
        }
        if(cp==" ") { word=line.size(); word_next=i+n; }
        line+=cp; i+=n;
      }
      if(i<active.text.size() && active.text[i]=='\n') ++i;
      lines.push_back(line);
    }

    snapshot(pending.id.empty()?active:pending);
  }
  bool touch_tracking{false},touch_owned{false};
  int touch_x{0},touch_y{0},touch_x0{0},touch_y0{0},touch_dist2{0};
  uint32_t touch_at{0};
  void begin(int x,int y,uint32_t now) {
    touch_tracking=true; touch_owned=visible(); touch_x=touch_x0=x; touch_y=touch_y0=y; touch_dist2=0; touch_at=now;
  }
  void move(int x,int y) {
    if(!touch_tracking) return;
    touch_x=x; touch_y=y; const int dx=x-touch_x0,dy=y-touch_y0;
    touch_dist2=std::max(touch_dist2,dx*dx+dy*dy);
  }
  bool release(uint32_t now) {
    if(!touch_tracking) return false;
    touch_tracking=false;
    if(!touch_owned && !visible()) return false;
    if(visible() && uint32_t(now-touch_at)<=700 && touch_dist2<=144 &&
       touch_x>=68 && touch_x<172 && touch_y>=190 && touch_y<226) cancel(active.id);
    return true;
  }
  bool exists() const { return !active.id.empty() || !pending.id.empty(); }
  bool visible() const { return !active.id.empty() && active.visible; }
  void snapshot(const Card &c) { status=c; }
  bool show(const std::string &id,const std::string &title,const std::string &text,
            const std::string &kind,int ttl,bool expected,uint32_t now,bool night=false) {
    if(!valid_id(id) || !valid_kind(kind)) {
      status=Card{}; status.id=valid_id(id)?id:""; status.state="rejected"; status.reason="invalid_request"; status.generation=generation;
      return false;
    }
    if(active.id==id || pending.id==id) { snapshot(active.id==id?active:pending); return false; }
    for(size_t i=0;i<history_count;++i) if(history[i].id==id) return false;
    Card c; c.id=id; c.kind=kind; c.audio_expected=expected; c.state="pending"; c.reason="accepted";
    c.title=bounded(title,32,128,false,c.truncated);
    c.text=bounded(text,4000,4096,true,c.truncated);
    c.ttl=ttl==0?30000:static_cast<uint32_t>(std::clamp(ttl,2000,120000));
    c.accepted=now; c.generation=++generation;
    if(night && expected) {c.audio="suppressed";c.reason="night_mode";}
    for(size_t i=std::min(history_count,size_t(4));i>0;--i) history[i]=std::move(history[i-1]);
    history[0]=c; history_count=std::min(size_t(5),history_count+1);history_index=0;++history_revision;
    if(owns_audio()) { pending=c; snapshot(pending); }
    else { active=c; pending=Card{}; snapshot(active); }
    return true;
  }
  uint64_t owner_generation{0};
  uint32_t audio_at{0};
  std::string owner_url;
  bool marker_seen{false},uri_seen{false},started{false};
  bool owns_audio() const { return owner_generation && !active.id.empty() && owner_generation==active.generation; }
  void revoke() { owner_generation=0; owner_url.clear(); marker_seen=uri_seen=started=false; }
  bool play(const std::string &id,const std::string &url,uint32_t now,bool menu,bool va_idle,bool player_idle,bool night=false) {
    // This entire method and on_announce must run synchronously in the ESPHome loop.
    tick(now,menu,va_idle&&player_idle);
    // Generation-owned sticky denial: never start delayed automatic card audio
    // after morning or a manual screen wake. Do not mute/stop other producers.
    Card *candidate=active.id==id?&active:(pending.id==id?&pending:nullptr);
    if(candidate && candidate->audio_expected && (night || candidate->audio=="suppressed") && !(owns_audio() && candidate==&active)) {
      candidate->audio="suppressed";candidate->reason="night_mode";
      for(size_t i=0;i<history_count;++i) if(history[i].generation==candidate->generation) {
        history[i].audio="suppressed";history[i].reason="night_mode";
      }
      snapshot(*candidate);return false;
    }
    if(!valid_id(id) || active.id!=id || !active.audio_expected || !valid_url(url) ||
       !visible() || menu || !va_idle || !player_idle || owns_audio() || active.audio!="none") {
      status=Card{}; status.id=valid_id(id)?id:""; status.state="rejected";
      status.reason="play_not_ready"; status.generation=active.id==id?active.generation:generation;
      return false;
    }
    owner_generation=active.generation; owner_url=url; audio_at=now;
    active.audio="waiting"; snapshot(active); return true;
  }
  bool tts_start(const std::string &text,uint32_t now) {
    if(!owns_audio() || uint32_t(now-active.accepted)>=active.ttl || marker_seen ||
       text!="__hermes_card__"+active.id) return false;
    marker_seen=true; snapshot(active); return true;
  }
  bool tts_end(const std::string &url,uint64_t token) {
    if(!owns_audio() || !marker_seen || token!=owner_generation || url!=owner_url) return false;
    uri_seen=true; return true; // URI ready is NOT audible completion.
  }
  void player_started(uint32_t /*now*/) {
    if(!owns_audio()) return;
    // Internal sounds may already occupy the speaker when card_play is called.
    // Only the card-owned TTS URL may transition this card into playing.
    if(!marker_seen || !uri_seen || started) return;
    started=true; active.state="playing"; active.audio="playing"; snapshot(active);
  }
  void finished(uint64_t token,bool player_idle,bool va_idle,uint32_t /*now*/) {
    if(!owns_audio() || token!=owner_generation || !started || !uri_seen || !player_idle || !va_idle) return;
    active.state="audio_done"; active.audio="done"; active.reason="completed";
    revoke(); snapshot(active);
  }
  void interrupt(const std::string &reason) {
    // Never issue STOP here: player offers no trustworthy public URL/owner readback.
    if(!active.id.empty()) { active.state="interrupted"; active.reason=reason; active.visible=false; if(owns_audio()) active.audio="cancelled"; snapshot(active); }
    else if(!pending.id.empty()) { pending.state="interrupted"; pending.reason=reason; snapshot(pending); }
    active=Card{}; pending=Card{}; revoke();
  }
  static std::string quoted(const std::string &s) {
    std::string out="\"";
    for(unsigned char c:s) { if(c=='\"'||c=='\\') out+='\\'; if(c>=32 && c<127) out+=static_cast<char>(c); }
    return out+"\"";
  }
  std::string status_json() const {
    return "{\"request_id\":"+quoted(status.id)+",\"state\":"+quoted(status.state)+
      ",\"visible\":"+(status.visible?"true":"false")+",\"audio\":"+quoted(status.audio)+
      ",\"reason\":"+quoted(status.reason)+",\"generation\":"+std::to_string(status.generation)+
      ",\"truncated\":"+(status.truncated?"true":"false")+"}";
  }
  bool cancel(const std::string &id) {
    if(!valid_id(id)) return false;
    Card *c=active.id==id?&active:(pending.id==id?&pending:nullptr);
    if(!c) return false;
    if(c==&active && owns_audio()) { c->audio="cancelled"; revoke(); }
    c->state="dismissed"; c->reason="cancelled"; c->visible=false; snapshot(*c); *c=Card{}; return true;
  }
  void tick(uint32_t now,bool menu,bool idle) {
    for(Card *c:{&active,&pending}) if(!c->id.empty() && uint32_t(now-c->accepted)>=c->ttl) {
      if(c==&active && owns_audio()) { c->audio="cancelled"; revoke(); }
      c->state="expired"; c->reason="ttl"; c->visible=false; snapshot(*c); *c=Card{};
    }
    if(owns_audio() && uint32_t(now-audio_at)>=(started?120000u:15000u)) {
      active.audio="failed"; active.reason="audio_watchdog"; active.state="shown"; revoke();
    }
    if(!pending.id.empty() && !owns_audio() && idle) { active=pending; pending=Card{}; }
    if(!active.id.empty()) {
      active.visible=!menu && (idle || owns_audio());
      if(active.visible && active.state=="pending") active.state="shown";
      snapshot(pending.id.empty()?active:pending);
    } else if(!pending.id.empty()) snapshot(pending);
  }
};
inline Controller &state() { static Controller value; return value; }
}
