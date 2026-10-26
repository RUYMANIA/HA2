#include "system_menu.h"
#include <cassert>
int main(){system_menu::Controller m;m.open(0);
 assert(m.tap(120,211,1)==system_menu::Event::Consumed);assert(m.active);
 assert(m.tap(120,227,2)==system_menu::Event::Consumed);assert(m.active);
 m.open(3);assert(m.tap(220,120,4)==system_menu::Event::Page);assert(m.page==7);
 m.page=6;assert(m.tap(120,63,5)==system_menu::Event::NightToggle);
 assert(m.tap(60,100,6)==system_menu::Event::NightStartMinus);
 assert(m.tap(180,100,7)==system_menu::Event::NightStartPlus);
 assert(m.tap(60,166,8)==system_menu::Event::NightEndMinus);
 assert(m.tap(180,166,9)==system_menu::Event::NightEndPlus);
}
