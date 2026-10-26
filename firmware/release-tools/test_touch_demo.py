from pathlib import Path
import sys,unittest
sys.path.insert(0,str(Path(__file__).parent))
from test_actual_lambdas import cpp,load,R
class TouchDemo(unittest.TestCase):
 def test_real_contact_cancels_before_legacy_voice_or_restart(self):
  hw=load((R/'config/HW/ball_v2_hw.yaml').read_text())['touchscreen'][0]
  touch=hw['on_touch']['then'][0]['lambda']
  release=hw['on_release']['then'][0]['lambda'].split('// Scale thresholds')[0]
  cpp('''#include "ui_v3.h"
#include "system_menu.h"
#include <cassert>
uint32_t now_ms=100,gs_start_ms=0;uint32_t millis(){return now_ms;}
bool gs_touch_active=false,init_in_progress=false;int gs_start_x=0,gs_start_y=0,gs_last_x=0,gs_last_y=0,voice_assistant_phase=1;
struct Point{int x=120,y=120;}touch;
struct Flag{bool state=false;}timer_ringing;
struct Script{void execute(){}}ui_power_sync;
struct Handler{int last=-1,calls=0;void execute(int e){last=e;++calls;}}menu_handle_event;
int legacy_calls=0;
#define id(x) x
void down(){'''+touch+'''}
void up(){'''+release+'''++legacy_calls;}
int main(){auto&m=system_menu::state();m.open(0);m.page=8;m.demo_active=true;down();assert(!m.demo_active);
 // The stopping tick may restore the menu before this release. The same
 // contact over Restart must not press Restart or start Assist.
 now_ms=300;up();assert(menu_handle_event.last==int(system_menu::Event::DemoCancel));assert(m.active&&m.page==8);assert(legacy_calls==0);
 int calls=menu_handle_event.calls;up();assert(menu_handle_event.calls==calls);
 now_ms=400;down();now_ms=500;up();assert(menu_handle_event.last==int(system_menu::Event::Restart));assert(legacy_calls==0);
 // Foreign audio can close the menu during a held demo cancellation.
 m.demo_active=true;now_ms=600;down();m.close();now_ms=1600;up();assert(menu_handle_event.last==int(system_menu::Event::DemoCancel));assert(!m.active&&legacy_calls==0);
}''')
if __name__=='__main__':unittest.main(verbosity=2)
