#include "ui_v3.h"
#include <cassert>
#include <iostream>
int main(){
 ui_v3::Power p;assert(p.sleep_index==0 && p.auto_index==0);assert(p.awake);
 p.tick(59999,false);assert(p.awake);p.tick(60000,false);assert(!p.awake);
 p.touch_begin(60001);assert(p.awake);assert(p.consume_touch(60500));
 p.touch_begin(61000);assert(!p.consume_touch(61100));
 p.tick(120000,true);p.tick(150000,false);assert(p.awake);p.tick(210000,false);assert(!p.awake);
 p.wake(0xfffffff0u,"touch");p.tick(0x10000u,false);assert(!p.awake);
 for(int sleep=0;sleep<4;sleep++)for(int au=0;au<4;au++){
  ui_v3::Power q;q.sleep_index=sleep;q.auto_index=au;q.sleep(0);
  assert(!q.auto_wake(100, true, 900, 15, 1));
  bool expected=sleep!=3 && au==0;
  assert(q.auto_wake(100,true,900,15,0)==expected);
  assert(!q.auto_wake(101,true,900,15,0));
  q.sleep(102);q.wake(103,"card");assert(q.awake);
 }
 ui_v3::Power q;assert(!q.auto_wake(0,false,0,0,0));
 assert(q.auto_wake(0,true,3600,0,0));q.sleep(1);assert(!q.auto_wake(1,true,3600,0,0));
 assert(!q.auto_wake(2,true,2700,45,0)); // clock moved backwards: no duplicate slots
 assert(q.auto_wake(3,true,4500,15,0));
 for(int sleep=0;sleep<4;sleep++)for(int au=0;au<4;au++)for(int minute=0;minute<60;minute++){
  ui_v3::Power all;all.sleep_index=sleep;all.auto_index=au;all.sleep(0);
  const int period=au==0?15:(au==1?30:60);
  const bool due=sleep!=3 && au!=3 && minute%period==0;
  assert(all.auto_wake(10,true,3600+minute*60,minute,0)==due);
  assert(!all.auto_wake(11,true,3600+minute*60,minute,0));
 }
 ui_v3::Power dst;assert(dst.auto_wake(0,true,3600,0,0));dst.sleep(1);assert(dst.auto_wake(2,true,7200,0,0));
 std::cout<<"power combinations, wrap, clock slots PASS\n";
}
