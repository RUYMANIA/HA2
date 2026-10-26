#include "ui_v3.h"
#include <cassert>
#include <iostream>
int main(){temporary_cards::Controller c;std::string text;for(int i=0;i<300;++i)text+="á ";assert(c.show(std::string(32,'a'),"Título",text,"notice",2000,false,0));auto measure=[](const std::string&s){return int(s.size())*7;};c.layout(measure,measure);ui_v3::HistoryView v;v.prepare(c,measure,measure,100,20);assert(v.title==c.display_title);assert(v.lines.size()==c.lines.size());for(size_t i=0;i<v.lines.size();++i)assert(v.lines[i]==c.lines[i]);auto&s=text_scroll::history();assert(s.overflow==int(v.lines.size())*20-98);assert(s.offset(2100)==0);assert(s.offset(3100)==16);assert(s.ended(999999));std::cout<<"actual HistoryView parity UTF8/98px viewport/2s hold/16px per second PASS\n";}
