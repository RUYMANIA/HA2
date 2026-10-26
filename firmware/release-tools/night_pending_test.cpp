#include "temporary_cards.h"
#include <cassert>
#include <limits>
int main(){
 temporary_cards::Controller c;const std::string a(32,'a'),b(32,'b'),url="http://192.0.2.10:8123/api/tts_proxy/test.wav";
 assert(c.show(a,"Día","Audio previo","notice",30000,true,0));c.tick(1,false,true);assert(c.play(a,url,2,false,true,true));const auto owner=c.owner_generation;
 assert(c.show(b,"Noche","Texto pendiente","notice",30000,true,3,true));assert(c.pending.audio=="suppressed");
 assert(!c.play(b,url,4,false,false,false,true));assert(c.status.id==b);assert(c.status.state=="pending");assert(c.status.audio=="suppressed");assert(c.status.reason=="night_mode");assert(c.owner_generation==owner);assert(c.owner_url==url);
 assert(c.tts_start("__hermes_card__"+a,5));assert(c.tts_end(url,owner));c.player_started(6);c.finished(owner,true,true,7);c.tick(8,false,true);
 assert(c.active.id==b && c.active.visible);assert(!c.play(b,url,9,false,true,true,false));assert(c.active.audio=="suppressed");assert(!c.owns_audio());assert(c.history[0].text=="Texto pendiente");
 c.status.generation=std::numeric_limits<uint64_t>::max();assert(c.status_json().size()<=255);
 c.tick(30003,false,true);assert(!c.exists());assert(c.history[0].text=="Texto pendiente");
}
