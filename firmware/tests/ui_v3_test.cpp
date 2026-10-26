#include "system_menu.h"
#include <cassert>
#include <iostream>
int main(){
 system_menu::Controller m; m.open(0);
 m.begin(180,120,1);m.move(50,120);assert(m.release(400,true)==system_menu::Event::Page);assert(m.page==8);
 for(int i=0;i<9;i++)m.swipe(1,500+i);assert(m.page==8);
 m.swipe(-1,600);assert(m.page==1);
 m.page=0; assert(m.tap(100,180,700)==system_menu::Event::Consumed);assert(m.page==0);
 m.begin(100,100,701);m.tick(30000);assert(m.release(30001,true)!=system_menu::Event::Legacy);
 m.open(0);m.page=2;assert(m.tap(70,200,1)==system_menu::Event::Previous);assert(m.tap(170,200,2)==system_menu::Event::Next);
 m.page=3;assert(m.tap(120,65,3)==system_menu::Event::Select0);assert(m.tap(120,110,4)==system_menu::Event::Select1);assert(m.tap(120,145,5)==system_menu::Event::Select2);assert(m.tap(120,190,6)==system_menu::Event::Select3);
 m.page=2;m.reading_until(100,120000);m.tick(30000);assert(m.active);m.tick(120101);assert(!m.active);
 m.open(0);m.page=2;m.reading_until(0,5001000);m.tick(4000000);assert(m.active);m.tick(5001001);assert(!m.active);
 std::cout<<"menu navigation PASS\n";
}
