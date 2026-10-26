#include "ui_v3.h"
#include <cassert>
#include <iostream>
int main(){
 ui_v3::Power p;
 p.apply_night(1,true,23*60);assert(!p.awake);
 p.wake(2,"card");assert(!p.awake);assert(p.blocked_by_night==1);
 p.wake(3,"voice");p.wake(4,"tts");p.wake(5,"timer");p.wake(6,"clock");assert(!p.awake);
 p.wake(7,"touch");assert(p.awake);p.tick(60006,true);assert(p.awake);p.tick(60007,true);assert(!p.awake);
 p.wake(60008,"card");assert(!p.awake);
 p.sleep_index=3;p.wake(70000,"manual");p.tick(130000,true);assert(!p.awake);
 p.apply_night(130001,true,7*60);p.wake(130002,"card");assert(p.awake);
 p.apply_night(130003,false,23*60);assert(!p.night_active);
 std::cout<<"central night block, explicit bounded manual, no busy/audio bypass, invalid clock fail open PASS\n";
}
