#include "ha2_cue.h"
#include <cassert>
int main(){
 ha2::Cue c;
 c.accept(1,false,false,0);assert(c.enter(1,true,true,false,1));assert(!c.enter(1,true,true,false,2));assert(c.owns(1,2));c.idle();assert(!c.owns(1,3));
 c.accept(2,true,false,4);assert(!c.enter(2,true,true,false,5));
 c.accept(3,false,true,6);assert(!c.enter(3,true,true,false,7));
 c.accept(4,false,false,8);assert(!c.enter(4,true,true,true,9));assert(!c.enter(4,true,true,false,10));
 c.accept(5,false,false,11);assert(!c.enter(5,false,true,false,12));assert(!c.enter(5,true,false,false,13));assert(c.enter(5,true,true,false,14));
 assert(c.owns(5,100));assert(!c.owns(6,100));assert(!c.owns(5,3014));
 c.accept(6,false,false,20);assert(!c.enter(6,true,true,false,120020));
 assert(c.played==2);assert(c.suppressed_night==2);
}
