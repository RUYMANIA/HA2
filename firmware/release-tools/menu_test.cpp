#include "system_menu.h"
#include <cassert>
#include <iostream>
int main(){
 system_menu::Controller m;m.open(0);assert(m.page==5);
 const int order[]={5,7,2,0,3,4,6,1,8};
 for(int i=1;i<=18;++i){assert(m.swipe(1,i)==system_menu::Event::Page);assert(m.active);assert(m.page==order[i%9]);}
 for(int i=1;i<=18;++i){m.swipe(-1,20+i);assert(m.page==order[(18-i)%9]);}
 m.active=false;m.begin(120,120,100);assert(m.release(1100,true)==system_menu::Event::Open);assert(m.page==5);
 // Real increasing/decreasing finger coordinates in production C++.
 m.begin(80,120,1200);m.move(160,120);assert(m.release(1400,true)==system_menu::Event::Page);assert(m.page==7);
 m.begin(160,120,1500);m.move(80,120);assert(m.release(1700,true)==system_menu::Event::Page);assert(m.page==5);
 m.tap(220,120,1800);assert(m.page==7);m.tap(20,120,1900);assert(m.page==5);
 std::cout<<"nine-page ring/reverse/wrap, hold Project, real finger coordinates and arrows PASS\n";
}
