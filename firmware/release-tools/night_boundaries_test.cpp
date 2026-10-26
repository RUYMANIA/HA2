#include "ui_v3.h"
#include <cassert>
#include <iostream>
ui_v3::LocalClock value{true,1380};
ui_v3::LocalClock read_clock(){return value;}
int main(){
 ui_v3::NightState n;
 for(int m=0;m<1440;++m)assert(n.contains(true,m)==(m<420 || m>=1380));
 assert(!n.contains(false,1380));assert(!n.contains(true,-1));assert(!n.contains(true,1440));
 n.start=32;n.end=40;for(int m=0;m<1440;++m)assert(n.contains(true,m)==(m>=480&&m<600));
 n.end=32;for(int m=0;m<1440;++m)assert(n.contains(true,m));n.enabled=false;assert(!n.contains(true,500));
 ui_v3::clock_reader()=&read_clock;ui_v3::Power p;
 p.touch_begin(5);assert(p.consume_touch(6));assert(p.awake);assert(p.manual_override);
 p.sleep(7);assert(!p.auto_wake(8,true,100020,0,0));assert(!p.awake);assert(p.auto_count==0);
 p.sleep_index=2;p.wake(0xfffffff0u,"touch");p.tick(0xfffffff0u+299999u,true);assert(p.awake);p.tick(0xfffffff0u+300000u,true);assert(!p.awake);
 value.minute=420;p.wake(400000,"card");assert(p.awake);value.minute=1380;p.tick(400001,true);assert(!p.awake);
 p.wake(400002,"menu");assert(p.awake);p.night.start=91;p.refresh_night(400003);assert(p.awake);
 value.valid=false;p.tick(400004,true);assert(!p.night_active);assert(p.awake);
 std::cout<<"all-minute boundaries/daytime/equal/invalid/DST local slots, dark first touch, no automatic count, wrap timeout PASS\n";
}
