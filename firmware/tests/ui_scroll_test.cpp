#include "textScroll.h"
#include <cassert>
#include <iostream>
int main(){
 text_scroll::Scroll s;s.reset(100,400,100,0);assert(s.offset(2100)==0);assert(s.offset(3100)==16);assert(s.offset(50000)==300);assert(s.ended(50000));
 s.reset(0,40,100,0);assert(s.offset(100000)==0 && s.ended(100000));
 s.reset(0,600,100,12000);assert(s.offset(2000)==0);assert(s.offset(7000)==250);assert(s.offset(12000)==500);
 s.reset(0,600,100,12000);s.pause(4000);assert(s.offset(8000)==100);s.resume(9000);assert(s.offset(10000)==150);
 text_scroll::Timing t;assert(t.put("literal",12345,1));assert(t.take("other",2)==0);assert(t.take("literal",3)==12345);assert(t.take("literal",4)==0);
 t.put("old",9000,5);assert(t.take("old",120005)==0);
 t.put("old turn",9000,1);t.next_generation();assert(t.take("old turn",2)==0);
 for(int i=0;i<5;i++)t.put(std::to_string(i),5000,100+i);assert(t.take("0",110)==0);assert(t.take("4",110)==5000);
 assert(!t.put("bad",-1,0));assert(!t.put(std::string(4097,'x'),1000,0));
 text_scroll::Playback p;std::string full(700,'x');auto raw=full.substr(0,497)+"...";
 p.begin(raw,100,1000,true);p.geometry(1000,100);assert(p.offset(1000)==0);assert(p.offset(97000)==0);assert(p.offset(145000)==16);
 assert(p.metadata(full,12000,101));assert(p.text==full && p.confirmed);int previous=p.offset(145000);assert(p.offset(145000)>=previous);assert(p.offset(145000)==90);
 assert(!p.metadata(full,13000,102));assert(p.real_duration==12000);
 assert(!p.metadata("unrelated",12000,102));p.stop(0);assert(!p.metadata(full,12000,103));
 p.begin("fresh",1,0,true);p.geometry(1000,100);assert(p.offset(0)==0);assert(p.offset(0)==0);assert(p.offset(48000)==0);assert(p.offset(144000)==16);
 p.begin("ambiguous",2,0,false);p.geometry(1000,100);assert(p.offset(900000)==0);
 std::cout<<"vertical/horizontal pause 2s; final hold; real duration, pause, bounded metadata TTL/generation PASS\\n";
}
