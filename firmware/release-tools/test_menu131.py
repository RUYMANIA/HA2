from pathlib import Path
import sys,unittest
sys.path.insert(0,str(Path(__file__).parent))
from test_actual_lambdas import cpp
class Menu131(unittest.TestCase):
 def test_three_deliberate_buttons_and_labels(self):
  cpp('''#include "system_menu.h"
#include "ui_catalogue.h"
#include <cassert>
#include <cstring>
int main(){system_menu::Controller m;m.open(0);m.page=8;
 assert(m.tap(120,120,1)==system_menu::Event::Restart);assert(m.active);
 assert(m.tap(120,168,2)==system_menu::Event::DemoStart);assert(m.active);
 assert(m.tap(120,72,3)==system_menu::Event::Close);assert(!m.active);
 assert(!strcmp(ui_i18n::text(ui_i18n::Key::ExitMenu,1),"Salir del Menú"));
 assert(!strcmp(ui_i18n::text(ui_i18n::Key::Restart,0),"Restart"));
 assert(!strcmp(ui_i18n::text(ui_i18n::Key::TestAnimations,1),"Test Animaciones"));
}''')
 def test_real_timeline_two_complete_rendered_cycles(self):
  cpp('''#include "gif_demo.h"
#include "avatar_timeline.h"
#include "system_menu.h"
#include <cassert>
int main(){hermes_avatar::Demo d;d.start();hermes_avatar::Timeline t;
 const uint16_t delays[]={1000,1000,1000,80,80,80,80,520};
 unsigned now=0,transitions=0;int previous=0;
 while(d.active){int s=d.index;bool changed=t.update(now,s,delays,8);
 if(changed){if(d.boundary(t.frame())){++transitions;assert(d.index==previous+1 || !d.active);previous=d.index;}else d.rendered(t.frame());}
 now+=20;assert(now<100000);}
 assert(transitions==11);assert(now>=11*2*3840);
 system_menu::Controller m;m.open(0);m.page=8;m.demo_active=true;assert(!m.tick(200000));
 m.begin(120,120,200001);assert(m.release(201001,true)==system_menu::Event::DemoCancel);assert(m.active&&m.page==8&&!m.demo_active);
 assert(!m.tick(220000));assert(m.tick(221001));
 // Incomplete rendered cycles cannot count as complete.
 m.open(10);m.page=8;m.demo_active=true;m.begin(120,120,11);
 assert(!m.demo_active); // cancellation requested immediately at touch-down
 // The demo may finish/preempt before release; its contact still owns the release.
 m.close();assert(m.release(100,true)==system_menu::Event::DemoCancel);assert(!m.active);
 d.start();d.rendered(0);d.rendered(7);assert(!d.boundary(0));assert(d.loops==0);
}''')
if __name__=='__main__':unittest.main(verbosity=2)
