# HA² — Home Assistant: snapshot privado

**Archivo de fuentes, no distribución portable ni candidato de despliegue. No ejecutar en producción.** Este directorio conserva la base `ha2-notifications-0.3.0` y cuatro fuentes seleccionadas por SHA instalado en cierres del 27 y 29 de octubre de 2026, con saneamiento mínimo en la copia y sin modificar los originales. Sincronización documental del **1 de noviembre de 2026**: véase `UPDATE-20261101.md`. No contiene firmware ni el runtime/companion Hermes completo.

- Backend HA² Notifications: **0.3.0**. El panel muestra `snapshot.version`; no tiene una versión semántica independiente. La versión del firmware es otra cosa.
- Adaptador `hermes_agent`: manifest **0.1.0**, con modificaciones locales en `api.py` y `conversation.py`; no es upstream intacto.
- Compatibilidad nativa restringida a **HA 2026.7.2 y fingerprints concretos**. Las guardas fail-closed se conservan sin cambios. Esto no certifica compatibilidad o seguridad actuales de una instalación.
- **No es HACS plug-and-play**, ni soporta por defecto cualquier satélite, prefijo o versión de HA.
- Este snapshot no acredita instalación, estado vivo, entrega de avisos, audio, micrófono, navegador ni hardware. No contiene reglas domésticas, credenciales, config entries ni Store operativo.

## Contenido y consulta

- `custom_components/ha2_notifications/`: fuentes y panel ES module; incluye el WAV necesario para el cue proactivo.
- `custom_components/hermes_agent/`: adaptador HA de origen tercero con parches locales.
- `tests/`: selección positiva de fuentes offline; dependencias y limitaciones en `TESTING.md`.
- `INSTALLATION.md`: manual **conceptual**, sin instalador ni permiso para operar.
- `SNAPSHOT.md` y `MANIFEST.json`: alcance, cambios y hashes SHA-256 de origen/copia por archivo.
- `TEST-RESULTS.json`: ejecución final actual de **71 pruebas Python puras y 58 Node** en esta copia; el resultado del 26 de octubre se conserva separado y no se suma.
- `UPDATE-20261101.md`: cierres instalados, hashes exactos, Log de Actividad de 200 eventos compartidos, Proactivo aprobado sin BETA y política de invitaciones 120 caracteres / 20 palabras / 240 bytes UTF-8, sin truncamiento. Activación histórica y observaciones naturales pendientes se distinguen del estado vivo no consultado.
- `THIRD_PARTY/`: atribución y licencia upstream conservadas.

## Defaults heredados: ejemplos, no configuración de tu casa

Se conservan literalmente `target_prefix = xiaozhi_ball_v2` y `weather_entity = weather.forecast_casa`. Son ejemplos heredados, no entidades que este archivo descubra o cree. El frontend fija `LANGUAGE_ENTITY = select.xiaozhi_ball_v2_language`, utilizada también para resolver el dispositivo del engranaje: cambiar sólo el prefijo del formulario **no** generaliza el panel. No se han cambiado entidades, prefijos, marca histórica o lógica para aparentar portabilidad.

Las direcciones `192.0.2.10`, `/path/to/user` y `00:00:00:00:00:00` son reemplazos documentales, no destinos operativos.

## Derechos y límites de publicación

No se elige ni se aplica una licencia global o propia. Los derechos del código y recursos propios quedan reservados hasta decisión expresa. El audio generado del proyecto `static/proactive-three-notes.wav` se incluye por autorización para **archivo privado**; sus derechos siguen pendientes antes de cualquier publicación pública. No inferir permiso público a partir de esta inclusión.

La MIT de Codename-11 se conserva únicamente para el material upstream correspondiente, con la atribución de Bailey Dixon 2026; no extiende una licencia a todo HA². Véase `THIRD_PARTY/README.md`. Los recursos de marca tampoco implican concesión de derechos de marca.
