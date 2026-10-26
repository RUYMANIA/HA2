#include "temporary_cards.h"
#include <cassert>
#include <iostream>
using namespace temporary_cards;
const std::string A="0123456789abcdef0123456789abcdef", B="abcdef0123456789abcdef0123456789", C="cccccccccccccccccccccccccccccccc";
int main() {
 Controller s;
 assert(s.show(A,"Aviso","Hola","notice",0,false,100));
 assert(s.active.ttl==30000 && s.active.state=="pending");
 s.tick(101,false,true);
 assert(s.visible() && s.active.state=="shown");
 assert(!s.show("\"bad","t","x","notice",30,false,102));
 assert(s.active.id==A);
 assert(!s.cancel(B));
 s.tick(30100,false,true);
 assert(!s.exists() && s.status.state=="expired");
 assert(s.show(B,"T","x","weather",1,false,0xfffffff0));
 assert(s.active.ttl==2000);
 s.tick(0x000007c0,false,true);
 assert(!s.exists());
 assert(s.show(C,"T","x","result",900000,false,0));
 assert(s.active.ttl==120000);
 assert(s.cancel(C) && !s.exists());
 std::cout << "tracer 1 state/TTL: PASS\n";
 auto measure=[](const std::string &v) { return static_cast<int>(v.size())*7; };
 assert(s.show(A,std::string(40,'T'),std::string(511,'a')+"á","reminder",0,false,0));
 assert(s.active.title.size()==32 && s.active.text.size()==511 && s.active.truncated);
 s.layout(measure,measure);
 assert(s.lines.size()<=5 && s.lines.back().find("...")!=std::string::npos);
 for(const auto &line:s.lines) assert(measure(line)<=176 && valid_utf8(line));
 assert(s.show(B,"%s ñ","uno\ndos\ntres\ncuatro\ncinco\nseis","notice",0,false,1));
 s.layout(measure,measure);
 assert(s.lines.size()==5 && s.lines[0]=="uno" && s.lines.back()=="cinco...");
 assert(s.show(C,"Inválido",std::string("a\xffz",3),"notice",0,false,2));
 assert(valid_utf8(s.active.text) && s.active.truncated);
 assert(s.show(A,"ááááááááááááááááááááááááááááááááá","","notice",0,false,3));
 assert(s.active.title.size()==64);
 s.layout(measure,measure);
 assert(measure(s.display_title)<=156 && valid_utf8(s.display_title));
 std::cout << "tracer 2 UTF8/wrap: PASS\n";
 Controller audio;
 const std::string url="http://192.0.2.10:8123/api/tts_proxy/abc-123_es.wav";
 assert(valid_url(url));
 for(const auto &bad:{"https://evil/a", "http://192.0.2.10:8123/api/tts_proxy/../a", "http://user@192.0.2.10:8123/api/tts_proxy/a", "http://192.0.2.10:8123/api/tts_proxy/a?x=1", "http://192.0.2.10:8123/api/tts_proxy/a%2fb"}) assert(!valid_url(bad));
 assert(audio.show(A,"Title","Body","reminder",4000,true,100));
 audio.tick(101,false,false); assert(!audio.visible());
 assert(!audio.play(A,url,102,false,false,true)); // busy VA
 audio.tick(103,true,true); assert(!audio.visible());
 assert(!audio.play(A,url,104,true,true,true)); // menu
 audio.tick(105,false,true); assert(audio.visible());
 assert(audio.play(A,url,106,false,true,true));
 const auto token=audio.owner_generation;
 assert(audio.tts_start("__hermes_card__"+A,107));
 assert(audio.active.state=="shown" && audio.active.audio=="waiting");
 assert(audio.tts_end(url,token));
 assert(audio.active.state!="audio_done");
 audio.player_started(108);
 assert(audio.active.state=="playing");
 audio.tick(109,false,false); assert(audio.visible()); // own voice retains card
 assert(audio.show(B,"B","B","notice",3000,false,110));
 assert(audio.active.id==A && audio.pending.id==B);
 audio.player_started(110);
 assert(audio.active.id==A && audio.active.state=="playing");
 assert(audio.show(C,"C","C","notice",3000,false,111));
 assert(audio.pending.id==C);
 assert(!audio.cancel(B) && audio.active.id==A);
 audio.tick(112,true,false); assert(!audio.visible() && audio.active.id==A);
 audio.finished(token-1,true,true,113); assert(audio.owns_audio());
 audio.finished(token,true,false,114); assert(audio.owns_audio());
 audio.finished(token,true,true,115); assert(!audio.owns_audio() && audio.active.state=="audio_done");
 audio.tick(116,false,true); assert(audio.active.id==C && audio.visible());
 assert(!audio.tts_end(url,token));
 audio.interrupt("new_question"); assert(!audio.exists());
 assert(!audio.play(C,url,117,false,true,true));
 assert(audio.show(A,"T","x","notice",2000,true,200));
 audio.tick(201,false,true); assert(audio.play(A,url,201,false,true,true));
 audio.tick(2200,false,false); assert(!audio.exists() && !audio.owns_audio());
 assert(!audio.tts_start("__hermes_card__"+A,2201));
 assert(audio.show(B,"T","x","notice",120000,true,3000));
 audio.tick(3001,false,true); assert(audio.play(B,url,3002,false,true,true));
 audio.tick(18002,false,false); assert(!audio.owns_audio() && audio.status.reason=="audio_watchdog");
 assert(audio.status_json().find("Title")==std::string::npos && audio.status_json().find("http")==std::string::npos);
 std::cout << "tracer 3 arbitration/audio tokens: PASS\n";
 Controller touch;
 assert(touch.show(A,"T","x","notice",2000,false,0));
 touch.tick(1,false,true);
 touch.begin(120,210,10); touch.move(121,211);
 assert(touch.release(40)); assert(!touch.exists());
 assert(touch.show(B,"T","x","notice",2000,false,100));
 touch.tick(101,false,true); touch.begin(30,90,102); touch.move(210,90);
 assert(touch.release(400) && touch.exists()); // swipe consumed, not dismissed
 touch.begin(120,210,500); touch.tick(2100,false,true);
 assert(touch.release(2150)); // expiry while touching still consumes
 assert(!touch.release(2151));
 assert(touch.show(C,"T","x","notice",2000,false,3000)); touch.tick(3001,false,true);
 touch.begin(120,210,3002); touch.move(160,200); touch.move(120,210);
 assert(touch.release(3050) && touch.exists()); // excursion not a close tap
 std::cout << "tracer 4 touch ownership/expiry: PASS\n";
 assert(is_marker("__hermes_card__"+A));
 assert(!is_marker("__hermes_card__"+A+"x"));
 assert(!is_marker("__hermes_card__not-a-uuid"));
 Controller queue;
 assert(queue.show(A,"A","body","notice",2000,true,0)); queue.tick(1,false,true);
 assert(queue.play(A,url,1,false,true,true));
 queue.tts_start("__hermes_card__"+A,2); queue.tts_end(url,queue.owner_generation); queue.player_started(3);
 assert(queue.show(B,"B","body","notice",5000,false,4));
 queue.tick(5,false,false);
 assert(queue.status.id==B && queue.status.state=="pending");
 queue.tick(2000,false,false); // own audio expires, pending remains deferred
 assert(queue.active.id.empty() && queue.pending.id==B && !queue.owns_audio());
 queue.tick(2001,false,true); assert(queue.visible() && queue.active.id==B);
 assert(!queue.tts_start("__hermes_card__"+A,2002));
 assert(queue.active.id==B);
 for(int c=0;c<256;++c) {
   Controller fuzz; std::string input(600,static_cast<char>(c));
   assert(fuzz.show(A,input,input,"notice",-1,false,0));
   fuzz.layout(measure,measure);
   assert(valid_utf8(fuzz.active.text) && valid_utf8(fuzz.display_title));
   assert(fuzz.active.text.size()<=512 && fuzz.lines.size()<=5);
   for(const auto &line:fuzz.lines) assert(valid_utf8(line) && measure(line)<=176);
 }
 std::cout << "diagnostic=" << queue.status_json() << "\n";
 std::cout << "regression marker/pending/256 UTF8 inputs: PASS\n";
 Controller replace;
 replace.show(A,"A","x","notice",30000,true,0); replace.tick(1,false,true);
 replace.play(A,url,2,false,true,true); const auto old_owner=replace.owner_generation;
 replace.tts_start("__hermes_card__"+A,2); replace.tts_end(url,old_owner); replace.player_started(3);
 replace.show(B,"B","x","notice",30000,false,4);
 replace.finished(old_owner,true,true,5);
 replace.show(C,"C","x","notice",30000,false,6);
 replace.tick(7,false,true);
 assert(replace.active.id==C && replace.pending.id.empty());
 std::cout << "regression latest show replaces stale pending: PASS\n";
}
