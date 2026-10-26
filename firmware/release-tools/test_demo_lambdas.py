from pathlib import Path
import sys,unittest,os
sys.path.insert(0,str(Path(__file__).parent))
from test_actual_lambdas import cpp,load,R
class ActualDemo(unittest.TestCase):
 def test_actual_avatar_tick_from_page8_priority_and_completion(self):
  body=load((R/'config/hermes_avatar.yaml').read_text())['interval'][0]['then'][0]['lambda']
  if os.environ.get('HA2_MUTATE_AVATAR')=='1':
   baseline=Path('/path/to/user/.hermes/projects/xiaozhi-ball-esphome/config/hermes_avatar.yaml')
   body=load(baseline.read_text())['interval'][0]['then'][0]['lambda']
  body=body.replace('${voice_assist_idle_phase_id}','1')
  menu=load((R/'config/system_menu.yaml').read_text())
  script=lambda name:next(x for x in menu['script'] if x['id']==name)['then'][0]['lambda']
  source='''#include "ui_v3.h"
#include "system_menu.h"
#include "avatar_timeline.h"
#include "avatar_damage.h"
#include "gif_demo.h"
#include <cassert>
uint32_t now_ms=0;uint32_t millis(){return now_ms;}
namespace media_player{enum{MEDIA_PLAYER_STATE_IDLE=0,MEDIA_PLAYER_STATE_ANNOUNCING=1,MEDIA_PLAYER_STATE_PLAYING=2};}
struct Flag{bool state=false;bool is_running(){return state;}}va,mute,timer_ringing,box_speaker,show_text;
struct Player{int state=0;}external_media_player;
int voice_assistant_phase=1,avatar_preview_state=-1;bool init_in_progress=false,show_clock=true;
uint32_t avatar_preview_started=0,avatar_preview_duration=4000,idle_seconds=0,avatar_seen_frames=0,avatar_render_count=0,avatar_max_render_ms=0;
namespace esphome{namespace display{struct DisplayPage{};}namespace animation{struct Animation{int frame=-1;unsigned counts[8]={};void set_frame(int n){frame=n;++counts[n];}};}}
esphome::display::DisplayPage pg[11];
esphome::display::DisplayPage *idle_page=&pg[0],*listening_page=&pg[1],*thinking_page=&pg[2],*replying_page=&pg[3],*timer_finished_page=&pg[4],*error_page=&pg[5],*initializing_page=&pg[6],*muted_page=&pg[7],*now_playing_page=&pg[8],*no_wifi_page=&pg[9],*no_ha_page=&pg[10];
esphome::animation::Animation an[11];
esphome::animation::Animation *casita_idle=&an[0],*casita_listening=&an[1],*casita_thinking=&an[2],*casita_replying=&an[3],*casita_timer_finished=&an[4],*casita_error=&an[5],*casita_initializing=&an[6],*casita_muted=&an[7],*casita_playing=&an[8],*error_no_wifi=&an[9],*error_no_ha=&an[10];
struct Display{bool ready=true;int renders=0;esphome::display::DisplayPage*p=nullptr;void show_page(esphome::display::DisplayPage*q){p=q;}auto get_active_page(){return p;}bool is_ready(){return ready;}void update(){if(hermes_avatar::demo().active && (p==thinking_page || p==replying_page))assert(ui_v3::gif_pass());++renders;}void start_clipping(int,int,int,int){}void end_clipping(){}}main_display;
struct Script{int calls=0;void execute(){++calls;}}draw_display,menu_render,menu_publish;
struct End{int calls=0;void execute(bool preempted);}menu_demo_end;
struct Sensor{void publish_state(const char*){}}avatar_state;
#define ESP_LOGI(...) ((void)0)
#define id(x) x
void End::execute(bool preempted){++calls;'''+script('menu_demo_end')+'''}
void start(){'''+script('menu_demo_start')+'''}
void tick(){'''+body+'''}
int main(){auto&m=system_menu::state();auto&d=hermes_avatar::demo();m.open(0);m.page=8;show_text.state=true;start();assert(m.demo_active&&d.active);
 tick();assert(hermes_avatar::timeline().state()==0);assert(main_display.renders==1);assert(m.active&&d.active);
 unsigned masks[11]={};unsigned finished=0;
 while(d.active){now_ms+=20;tick();int i=hermes_avatar::timeline().state();if(i>=0&&i<11)masks[i]|=avatar_seen_frames;assert(now_ms<50000);}
 assert(menu_demo_end.calls==1&&m.active&&m.page==8&&!m.demo_active);assert(now_ms>28000);
 for(unsigned mask:masks)assert(mask==255);(void)finished;
 for(auto &animation:an)for(unsigned count:animation.counts)assert(count==2);
 assert(show_text.state&&!ui_v3::gif_pass());
 for(int cause=0;cause<5;++cause){d.start();m.demo_active=true;m.active=true;
 va.state=cause==0;timer_ringing.state=cause==1;box_speaker.state=cause==2;external_media_player.state=cause==3?2:0;voice_assistant_phase=cause==4?5:1;
 tick();assert(!d.active&&!m.active);}
 va.state=false;timer_ringing.state=false;box_speaker.state=false;external_media_player.state=0;voice_assistant_phase=1;
 auto &cards=temporary_cards::state();m.open(now_ms);m.page=8;start();assert(d.active);
 assert(cards.show(std::string(32,'b'),"foreign","card","notice",30000,false,now_ms));
 tick();assert(!d.active&&!m.active&&cards.exists());
 m.open(now_ms);m.page=8;start();assert(!d.active&&!m.demo_active);
 assert(cards.cancel(std::string(32,'b')));m.page=7;start();assert(!d.active);
 m.page=8;start();assert(d.active&&m.demo_active);m.begin(120,120,++now_ms);tick();assert(!d.active&&m.active&&m.page==8);
 assert(m.release(++now_ms,true)==system_menu::Event::DemoCancel);
}'''
  cpp(source)
if __name__=='__main__':unittest.main(verbosity=2)
