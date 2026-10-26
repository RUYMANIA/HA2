#include "ui_v3.h"
#include "temporary_cards.h"
#include <cassert>
#include <iostream>
std::string ident(int i){return std::string(31,'a')+char('0'+i);}
int main(){
 temporary_cards::Controller c;auto measure=[](const std::string&s){return int(s.size()*8);};
 assert(c.show(ident(0),"Long",std::string(4090,'x'),"notice",120000,false,100));
 assert(c.active.text.size()==4000);assert(c.active.truncated);assert(c.history_count==1);
 c.layout(measure,measure);assert(c.lines.size()>5);assert(c.history_count==1);
 assert(!c.show(ident(0),"duplicate","duplicate","notice",0,false,101));
 c.cancel(ident(0));assert(c.history_count==1);
 for(int i=1;i<7;i++)assert(c.show(ident(i),"Title","body","notice",0,false,100+i));
 assert(c.history_count==5);assert(c.history[0].id==ident(6));assert(c.history[4].id==ident(2));
 assert(!c.show(ident(3),"dup","dup","notice",0,false,200));assert(c.history_count==5);
 temporary_cards::Controller d;std::string body;for(int i=0;i<2000;i++)body+="á";
 assert(d.show(ident(0),"Title",body,"notice",0,false,0));d.layout(measure,measure);
 assert(d.active.text.size()==4000 && !d.active.truncated);assert(temporary_cards::valid_utf8(d.active.text));
 assert(d.lines.size()>5 && !d.active.truncated);
 c.history_index=0;assert(c.history_step(1));assert(c.history_index==1);assert(c.history_step(-1));assert(c.history_index==0);assert(c.history_step(-1));assert(c.history_index==4);assert(!c.history_step(0));
 temporary_cards::Controller empty;assert(!empty.history_step(1));
 ui_v3::HistoryView v;assert(v.prepare(d,measure,measure,0,20));assert(v.lines.size()>5);assert(!v.prepare(d,measure,measure,100,20));
 d.show(ident(1),"next","small","notice",0,false,101);assert(v.prepare(d,measure,measure,101,20));assert(v.lines.size()==1);assert(text_scroll::history().offset(99999)==0);
 temporary_cards::Controller worst;assert(worst.show(ident(0),"T",std::string(4000,'\n'),"notice",0,false,0));worst.layout(measure,measure);assert(worst.lines.size()==4000);assert(worst.lines.storage_bytes()<18000);
 for(const auto &line:worst.lines)assert(line.empty());
 std::cout<<"history bounded five; UTF8 cap 4096 bytes/4000 chars; full layout PASS\n";
}
