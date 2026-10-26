#include "system_menu.h"
#include "ui_v3.h"
#include <cassert>
#include <cstring>
int main(){
 system_menu::Controller m;m.open(100);assert(m.page==5);
 const int ring[]={7,2,0,3,4,6,1,8,5};
 for(int p:ring){assert(m.swipe(1,110)==system_menu::Event::Page);assert(m.page==p);}
 for(int i=0;i<9;i++)m.swipe(-1,120);assert(m.page==5);
 m.swipe(1,130);assert(m.tap(120,90,140)==system_menu::Event::Select0);assert(m.tap(120,160,150)==system_menu::Event::Select1);assert(m.tap(120,200,160)==system_menu::Event::Consumed);
 assert(std::strcmp(ui_v3::page_name(7),"language")==0);
}
