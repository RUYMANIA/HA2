#include <cassert>
#include <cstring>
#if __has_include("ui_catalogue.h")
#include "ui_catalogue.h"
int main(){
 using namespace ui_i18n;assert(language_index("English")==0);assert(language_index("Español")==1);assert(language_index("invalid")==0);
 assert(std::strcmp(text(Key::Exit,0),"Exit")==0);assert(std::strcmp(text(Key::Exit,1),"Salir")==0);
 assert(std::strcmp(text(Key::Creator,0),"Creator RUYMANIA")==0);
 assert(std::strcmp(sleep_option(0,0),"1 minute")==0);assert(std::strcmp(sleep_option(0,1),"1 minuto")==0);
 assert(std::strcmp(auto_option(0,0),"Every 15 min")==0);assert(std::strcmp(auto_option(0,1),"Cada 15 min")==0);
 for(int lang=0;lang<2;lang++)for(int k=0;k<int(Key::Count);k++)assert(std::strlen(text(static_cast<Key>(k),lang))>0);
 assert(std::strcmp(kind("notice",0),"Notice")==0);assert(std::strcmp(kind("weather",1),"Tiempo")==0);
}
#else
int main(){assert(false && "UI-only catalogue missing");}
#endif
