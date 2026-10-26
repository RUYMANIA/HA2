from pathlib import Path
import subprocess,tempfile,yaml,unittest
R=Path('/path/to/user/.hermes/projects/ha2-menu-1.3.1')
class Loader(yaml.SafeLoader):pass
Loader.add_multi_constructor('!',lambda l,t,n:l.construct_scalar(n))
def load(s):return yaml.load(s,Loader=Loader)

def cpp(source):
 with tempfile.TemporaryDirectory(dir='/path/to/user/.hermes/cache/scratch') as tmp:
  p=Path(tmp);(p/'t.cpp').write_text(source)
  subprocess.run(['clang++','-std=c++17','-Wall','-Wextra','-Werror','-Wno-unused-variable','-fsanitize=address,undefined','-g','-I',str(R),str(p/'t.cpp'),'-o',str(p/'t')],check=True)
  subprocess.run([str(p/'t')],check=True)
def body(file,ident):return next(x for x in load((R/'config'/file).read_text())['script'] if x['id']==ident)['then'][0]['lambda']
class Lambdas(unittest.TestCase):
 def test_real_power_sync_no_flash_and_brightness_restore(self):
  cpp('''#include "ui_v3.h"
#include "system_menu.h"
#include <cassert>
uint32_t now_ms=1;uint32_t millis(){return now_ms;}
ui_v3::LocalClock clock_value{true,1379};
struct Flag{bool state=false;bool is_running(){return state;}}clock_enabled,va,timer_ringing;
bool show_clock=false;
struct Script{int calls=0;void execute(){++calls;}}menu_render,draw_display;
struct Light{int ons=0,offs=0;float restored=0;struct Remote{float get_brightness(){return .42f;}}remote_values;
 struct Call{Light*l;bool on;float b=0;Call&set_transition_length(int){return *this;}Call&set_brightness(float v){b=v;return *this;}void perform(){if(on){++l->ons;l->restored=b;}else ++l->offs;}};
 Call turn_on(){return {this,true,0};}Call turn_off(){return {this,false,0};}}Sled;
#define id(x) x
void sync(){'''+body('ui_v3.yaml','ui_power_sync')+'''}
int main(){auto&p=ui_v3::power();ui_v3::clock_reader()=[](){return clock_value;};sync();assert(Sled.ons==0);
 clock_value.minute=1380;sync();assert(!p.awake);assert(Sled.offs==1);assert(Sled.ons==0);
 p.wake(++now_ms,"card");sync();assert(Sled.ons==0);
 p.wake(++now_ms,"touch");sync();assert(Sled.ons==1);assert(Sled.restored==.42f);
 now_ms+=60000;p.tick(now_ms,true);sync();assert(!p.awake);assert(Sled.offs==2);p.wake(++now_ms,"tts");sync();assert(Sled.ons==1);
 clock_value.minute=420;p.wake(++now_ms,"card");sync();assert(Sled.ons==2);assert(Sled.restored==.42f);
}
''')
 def test_actual_night_select_callbacks_no_ha_manual_override(self):
  cfg=load((R/'config/ha2.yaml').read_text());callbacks=[x['on_value'][0]['lambda'] for x in cfg['select'] if x['id']!='ui_language']
  cpp('''#include "ui_v3.h"
#include "system_menu.h"
#include <optional>
#include <cassert>
uint32_t millis(){return 100;}
struct Select{int index;std::optional<int>active_index(){return index;}}screen_night_start{92},screen_night_end{28};
struct Script{void execute(){ui_v3::power().refresh_night(millis());}}ui_power_sync,menu_render;
#define id(x) x
void start(){'''+callbacks[0]+'''}
void end(){'''+callbacks[1]+'''}
int main(){auto&p=ui_v3::power();ui_v3::clock_reader()=[]()->ui_v3::LocalClock{return {true,1380};};
 p.refresh_night(0);assert(!p.awake);start();end();assert(!p.awake);assert(p.persist_changes==0);
 screen_night_start.index=91;start();assert(!p.awake);assert(!p.manual_override);assert(p.persist_changes==1);start();assert(p.persist_changes==1);
 ui_v3::night_edit()=true;screen_night_end.index=29;end();ui_v3::night_edit()=false;assert(p.awake);assert(p.manual_override);assert(p.persist_changes==2);
}
''')
 def test_real_dark_release_prefix_is_consumed_before_legacy_voice(self):
  hw=load((R/'config/HW/ball_v2_hw.yaml').read_text())
  release=hw['touchscreen'][0]['on_release']['then'][0]['lambda'].split('            // Scale thresholds')[0]
  # YAML deindents the body; split at the literal boundary, before legacy audio/HA.
  release=release.split('// Scale thresholds')[0]
  cpp('''#include "ui_v3.h"
#include "system_menu.h"
#include <cassert>
uint32_t now_ms=0;uint32_t millis(){return now_ms;}
bool gs_touch_active=false,init_in_progress=false;
int gs_start_x=120,gs_start_y=120,gs_last_x=120,gs_last_y=120,voice_assistant_phase=1;
uint32_t gs_start_ms=0;
struct Flag{bool state=false;}timer_ringing;
struct Script{void execute(){ui_v3::power().refresh_night(millis());}}ui_power_sync;
struct Handler{int last=-1;void execute(int event){last=event;}}menu_handle_event;
int legacy_voice_calls=0;
#define id(x) x
void release(){'''+release+'''++legacy_voice_calls;}
void begin(){gs_touch_active=true;gs_start_ms=now_ms;ui_v3::power().touch_begin(now_ms);system_menu::state().begin(120,120,now_ms);}
int main(){ui_v3::clock_reader()=[]()->ui_v3::LocalClock{return {true,1380};};
 auto&p=ui_v3::power();p.refresh_night(0);assert(!p.awake);begin();now_ms=100;release();assert(p.awake);assert(legacy_voice_calls==0);assert(!system_menu::state().active);
 p.sleep(now_ms);now_ms=200;begin();now_ms=1200;release();assert(legacy_voice_calls==0);assert(system_menu::state().active);assert(system_menu::state().page==5);assert(menu_handle_event.last==int(system_menu::Event::Open));
 now_ms=1300;begin();system_menu::state().move(180,120);gs_last_x=180;now_ms=1500;release();assert(system_menu::state().page==7);assert(legacy_voice_calls==0);
 gs_last_x=120;now_ms=1600;begin();system_menu::state().move(60,120);gs_last_x=60;now_ms=1800;release();assert(system_menu::state().page==5);assert(legacy_voice_calls==0);
}
''')
 def test_real_card_show_preserves_logical_visible_and_audio_in_dark(self):
  cfg=load((R/'config/temporary_cards.yaml').read_text());show=cfg['api']['actions'][0]['then'][0]['lambda']
  cpp('''#include "ui_v3.h"
#include "system_menu.h"
#include <cassert>
uint32_t now_ms=1;uint32_t millis(){return now_ms;}
struct Script{void execute(){ui_v3::power().refresh_night(millis());}}ui_power_sync,menu_render;
int avatar_preview_state=0;
#define id(x) x
void show(const std::string&request_id,const std::string&title,const std::string&body,const std::string&kind,int ttl_ms,bool audio_expected){'''+show+'''}
int main(){ui_v3::clock_reader()=[]()->ui_v3::LocalClock{return {true,1380};};auto&p=ui_v3::power();p.refresh_night(0);
 auto&c=temporary_cards::state();
 for(int i=0;i<6;++i){show(std::string(31,'a')+char('0'+i),"private title","private body","notice",30000,true);c.tick(++now_ms,false,true);assert(!p.awake);assert(c.visible());}
 assert(c.history_count==5);assert(c.status_json().find("\\\"visible\\\":true")!=std::string::npos);
 assert(!c.play(c.active.id,"http://192.0.2.10:8123/api/tts_proxy/test.wav",++now_ms,false,true,true));assert(!c.owns_audio());assert(c.active.audio=="suppressed");assert(!p.awake);
}
''')
if __name__=='__main__':unittest.main(verbosity=2)
