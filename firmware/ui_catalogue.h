#pragma once
#include <algorithm>
#include <cstring>
#include <string>
// Display-only strings. Never use this catalogue for HA entity options or state keys.
namespace ui_i18n {
enum class Key { Project,Creator,Exit,Close,Volume,Pending,Speaker,Info,Night,Enabled,Disabled,Start,End,AllDay,LocalHATime,NoWifi,WifiDisconnected,Connected,NotConnected,Uptime,Battery,BatteryNoData,FreeHeap,FreePSRAM,Cards,NoCards,Previous,Next,Sleep,AutoWake,Language,Reminder,Weather,Result,Notice,ExitMenu,Restart,TestAnimations,Count };
inline constexpr const char* catalogue[][2]={
 {"Project","Proyecto"},{"Creator RUYMANIA","Creador RUYMANIA"},{"Exit","Salir"},{"Close","Cerrar"},
 {"Volume","Volumen"},{"Pending","Pendiente"},{"Speaker","Altavoz"},{"Info","Info"},
 {"Night mode","Modo noche"},{"Enabled","Activado"},{"Disabled","Desactivado"},{"Start","Inicio"},{"End","Fin"},
 {"All day","Todo el día"},{"HA local time","Hora local HA"},{"IP: no Wi-Fi","IP: sin Wi-Fi"},{"Wi-Fi: disconnected","Wi-Fi: sin conexión"},
 {"Connected","Conectado"},{"Not connected","Sin conexión"},{"Uptime","Tiempo activo"},{"Battery","Batería"},{"Battery: no data","Batería: sin datos"},
 {"Free heap","Heap libre"},{"Free PSRAM","PSRAM libre"},{"Cards","Tarjetas"},{"No cards","Sin tarjetas"},{"Previous","Anterior"},{"Next","Siguiente"},
 {"Sleep","Reposo"},{"Auto wake","Despertar"},{"Language","Idioma"},{"Reminder","Recordatorio"},{"Weather","Tiempo"},{"Result","Resultado"},{"Notice","Aviso"},
 {"Exit Menu","Salir del Menú"},{"Restart","Reiniciar"},{"Test Animations","Test Animaciones"}
};
static_assert(sizeof(catalogue)/sizeof(catalogue[0])==static_cast<unsigned>(Key::Count));
inline int language_index(const char* name){return name && std::strcmp(name,"Español")==0?1:0;}
inline const char* text(Key key,int language){return catalogue[static_cast<unsigned>(key)][language==1?1:0];}
inline const char* sleep_option(int i,int language){static constexpr const char* values[][2]={{"1 minute","1 minuto"},{"3 minutes","3 minutos"},{"5 minutes","5 minutos"},{"Disabled","Desactivado"}};return values[std::clamp(i,0,3)][language==1?1:0];}
inline const char* auto_option(int i,int language){static constexpr const char* values[][2]={{"Every 15 min","Cada 15 min"},{"Every 30 min","Cada 30 min"},{"Every 60 min","Cada 60 min"},{"Disabled","Desactivado"}};return values[std::clamp(i,0,3)][language==1?1:0];}
inline const char* kind(const std::string& k,int language){return text(k=="reminder"?Key::Reminder:(k=="weather"?Key::Weather:(k=="result"?Key::Result:Key::Notice)),language);}
}
