#include "textScroll.h"
#include <cassert>
#include <iostream>
int main(){
 text_scroll::Transcript t;std::string full(700,'x');auto raw=full.substr(0,497)+"...";
 t.new_turn();t.receive(raw,10);assert(t.text==raw);assert(t.metadata(full,100));assert(t.text==full);
 t.new_turn();assert(t.text.empty());assert(t.metadata(full,1000)==false);t.receive(raw,1001);assert(t.text==full);
 t.new_turn();t.metadata(full,1000);t.receive(raw,6001);assert(t.text==raw);
 t.new_turn();t.receive("new",10);assert(!t.metadata(full,11));assert(t.text=="new");
 t.new_turn();t.metadata(full,10);t.new_turn();t.receive(raw,11);assert(t.text==raw);
 t.receive(raw,20);assert(!t.metadata(full,5021));
 text_scroll::Timing pending;text_scroll::Playback p;pending.put(full,12000,1);p.begin(raw,2,0,true);assert(text_scroll::apply_pending(p,pending,2));assert(p.text==full && p.confirmed);assert(!text_scroll::apply_pending(p,pending,3));
 pending.put(full,12000,10);pending.put(full+"different",15000,11);p.begin(raw,12,0,true);assert(!text_scroll::apply_pending(p,pending,12));assert(!p.confirmed);
 std::cout<<"STT exact/prefix; pending 5s and new-turn clearing; TTS pending-prefix consume PASS\n";
}
