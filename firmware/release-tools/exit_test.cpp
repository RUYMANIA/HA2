#include "system_menu.h"
#include <cassert>
#include <iostream>
int main(){system_menu::Controller m;
 for(int page=0;page<8;++page){m.open(0);m.page=page;assert(m.tap(120,page==5?227:211,1)!=system_menu::Event::Close);assert(m.active);
  for(int x=74;x<167;++x)for(int y=197;y<234;++y){assert(m.tap(x,y,1)!=system_menu::Event::Close);assert(m.active);}
 }
 m.open(0);m.swipe(-1,1);assert(m.page==8&&m.active);
 assert(m.tap(120,72,2)==system_menu::Event::Close);assert(!m.active);
 m.open(0);m.page=8;assert(m.tap(120,40,3)==system_menu::Event::Consumed);assert(m.active);
 m.tap(220,120,4);assert(m.page==5&&m.active);m.tap(20,120,5);assert(m.page==8&&m.active);
 for(int p:{3,4}){m.page=p;assert(m.tap(120,205,6)==system_menu::Event::Select3);}
 m.page=7;assert(m.tap(120,160,7)==system_menu::Event::Select1);
 m.page=2;assert(m.tap(80,200,8)==system_menu::Event::Previous);assert(m.tap(155,200,9)==system_menu::Event::Next);
 std::cout<<"only Exit closes, arrows retained, resized control hitboxes PASS\n";
}
