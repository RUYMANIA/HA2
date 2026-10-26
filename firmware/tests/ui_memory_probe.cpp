#include "ui_v3.h"
#include "system_menu.h"
#include <iostream>
#include <cassert>
using temporary_cards::Card;
size_t bytes(const Card&c){size_t n=0;for(const auto*s:{&c.id,&c.title,&c.text,&c.kind,&c.state,&c.reason,&c.audio})n+=s->capacity();return n;}
int main(){
 temporary_cards::Controller c;ui_v3::HistoryView view;text_scroll::Timing timing;text_scroll::Transcript stt;text_scroll::Playback tts;
 auto measure=[](const std::string&s){return int(s.size()*8);};
 std::string full;for(int i=0;i<2048;i++)full+="á";
 for(int i=0;i<5;i++)c.show(std::string(31,'a')+char('0'+i),std::string(128,'t'),full,"notice",120000,false,i);
 c.layout(measure,measure);view.prepare(c,measure,measure,10,20);
 // Retain both text and newline-heavy table peak capacities through a redraw.
 c.show(std::string(32,'f'),"T",std::string(4000,'\n'),"notice",120000,false,20);c.layout(measure,measure);view.prepare(c,measure,measure,20,20);
 for(int i=0;i<4;i++)timing.put(full.substr(0,4094)+std::to_string(i),600000,i);
 stt.new_turn();stt.metadata(full,0);stt.receive(full.substr(0,497)+"...",1);stt.new_turn();stt.metadata(full,2);stt.receive(full.substr(0,497)+"...",3);
 tts.begin(full,0,0,true);tts.metadata(full,600000,0);
 size_t history=0;for(const auto &card:c.history)history+=bytes(card);
 size_t current=bytes(c.active)+bytes(c.pending)+bytes(c.status)+c.owner_url.capacity()+c.display_title.capacity();
 size_t descriptors=0;for(const auto&e:timing.entries)descriptors+=e.message.capacity();
 size_t transcript=stt.raw.capacity()+stt.text.capacity()+stt.pending.capacity();
 size_t playback=tts.raw.capacity()+tts.text.capacity();
 size_t linebuf=c.lines.storage_bytes()+view.lines.storage_bytes()+view.title.capacity();
 const size_t objects=sizeof(c)+sizeof(view)+sizeof(timing)+sizeof(stt)+sizeof(tts)+sizeof(system_menu::Controller)+sizeof(ui_v3::Power);
 const size_t capacity=history+current+descriptors+transcript+playback+linebuf;
 assert(c.history_count==5 && c.lines.size()==4000);assert(capacity<150000);
 std::cout<<"{\"basis\":\"host sizeof and retained string/vector capacities; not ESP32 heap\",\"history_count\":5,\"history_capacity_bytes\":"<<history<<",\"active_pending_status_capacity_bytes\":"<<current<<",\"timing_capacity_bytes\":"<<descriptors<<",\"transcript_capacity_bytes\":"<<transcript<<",\"playback_capacity_bytes\":"<<playback<<",\"line_views_capacity_bytes\":"<<linebuf<<",\"objects_sizeof_bytes\":"<<objects<<",\"capacity_sum_bytes\":"<<capacity<<",\"note\":\"capacity sum includes small-string inline storage already counted in sizeof and omits allocator overhead; not an exact allocation total\"}\n";
}
