#include "temporary_cards.h"
#include <cassert>
const std::string a(32,'a'),b(32,'b'),url="http://192.0.2.10:8123/api/tts_proxy/test.wav";
int main(){
 temporary_cards::Controller c;
 assert(c.show(a,"Aviso","Conservar texto","notice",30000,true,10,true));
 c.tick(11,false,true);assert(c.visible());assert(c.active.audio=="suppressed" && c.active.reason=="night_mode");
 assert(!c.play(a,url,12,false,true,true,false));assert(c.visible());assert(!c.owns_audio());assert(c.status.audio=="suppressed");assert(c.history[0].text=="Conservar texto");
 temporary_cards::Controller boundary;assert(boundary.show(a,"T","B","notice",30000,true,10,false));boundary.tick(11,false,true);
 assert(!boundary.play(a,url,12,false,true,true,true));assert(boundary.active.audio=="suppressed");assert(boundary.visible());
 assert(!boundary.play(a,url,13,false,true,true,false));assert(!boundary.owns_audio());
 temporary_cards::Controller day;assert(day.show(b,"T","B","notice",30000,true,10,false));day.tick(11,false,true);assert(day.play(b,url,12,false,true,true,false));assert(day.owns_audio());
 c.tick(30011,false,true);assert(!c.exists());assert(c.history[0].text=="Conservar texto");
}
