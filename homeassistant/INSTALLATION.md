# Instalación manual conceptual — no ejecutar en producción

Este documento explica las fronteras de las fuentes archivadas. **No es un procedimiento de despliegue aprobado**, no ejecuta órdenes, no proporciona runners operativos y no autoriza reiniciar HA ni acceder a un servicio o dispositivo. Preparar cualquier futura instalación en un laboratorio aislado y revisado, con derechos resueltos y autorización independiente.

## Dependencias reales

HA² declara `requirements: []` y dependencias HA `http`, `websocket_api`, `frontend`, `panel_custom`, `assist_pipeline`, `tts`, `esphome`. Importa `homeassistant`, `voluptuous` y `aioesphomeapi`. Hermes HA usa además `aiohttp` y `yarl`. Se consumen las librerías de HA, no versiones pip independientes acreditadas por este archivo. No instalar pip sobre un HA vivo para forzar compatibilidad.

El modo nativo exige satélite ESPHome compatible, pipeline seleccionada, TTS y agente/companion Hermes con bootstrap de sesión y contexto real. El bridge cron, plugins y runtime/proveedor están fuera de este directorio: copiar HA no hace autónomas esas funciones.

## Restricción fail-closed

`NativeConversationStarter.compatible()` exige exactamente HA **2026.7.2** y SHA-256 del código fuente de `EsphomeAssistSatellite.handle_pipeline_start`:

`44dc85329f3b6957f6d4711c59531e5045455fb1b04403b5ed6d912e8338c559`

`NativeIngressGate` exige además el SHA-256 de `APIClient.subscribe_voice_assistant` y la estructura esperada de su suscripción:

`3eb68c90fe2a4103e8361d360c83a66e8798db3d86436fe26c1673bd8c4ec922`

Accede a estado privado del satélite. Otra versión o estructura debe fallar cerrada; **no borrar guardas, falsear versiones o sustituir hashes** para activarlo. La coincidencia de hashes tampoco acredita disponibilidad, reproducción ni aceptación física. Estas pruebas no han importado una instalación real de HA 2026.7.2.

## Secuencia conceptual en un laboratorio futuro

1. Resolver derechos y dependencias, revisar cambios y preparar un respaldo privado de fuentes/configuración propias. Nunca versionar credenciales, `.storage`, reglas o sesiones. No sobrescribir una instalación existente por copiar este archivo.
2. La estructura manual sería `<config>/custom_components/ha2_notifications/`; para conversación, el adaptador `hermes_agent` y un companion compatible requieren revisión separada. No hay empaquetado HACS verificado ni instalador portable incluido.
3. Validación de configuración, carga de Python y cualquier reinicio de HA requieren un procedimiento y autorización propios. Esto no concede permiso para reiniciar Ball, gateway, Mac o servicios ajenos. Un cambio exclusivamente JS en una ruta ya registrada es una frontera distinta de la carga Python.
4. La integración se añade por Ajustes → Dispositivos y servicios → Añadir integración → HA² Notifications. Es entrada única, no configuración YAML. El formulario pide prefijo y entidad meteorológica; los defaults heredados son sólo ejemplos (véase README).
5. Deben existir `sensor.<prefix>_card_status`, `sensor.<prefix>_ui_status`, `sensor.<prefix>_ui_night`, `binary_sensor.<prefix>_card_active`, `media_player.<prefix>`, `assist_satellite.<prefix>_assist_satellite`, `select.<prefix>_assistant`, la entidad `weather.*`, y acciones ESPHome `<prefix>_card_show`, `<prefix>_card_play`, `<prefix>_card_cancel`. La UI además conserva la entidad fija `select.xiaozhi_ball_v2_language`.
6. Si faltan entidades/servicios, el formulario devuelve `config_error` y el setup falla con `ConfigEntryNotReady`. No inventar entidades o modificar registros globales para salvar la validación. El terminal necesita poder alcanzar las URLs internas de recursos/TTS de HA.
7. El código registra panel administrador **HA² - RUYMANIA**, ruta `/ha2-notifications`, módulo `/ha2-notifications-static/panel.js?v=0.3.0`. El acceso WS y la acción están restringidos a administradores. Cargar vacío, sin importar reglas ni activar funciones automáticamente.
8. HA es la autoridad del horario y la entrega. Store privado `.storage/ha2_notifications` guarda reglas/configuración/cola/historial; no se incluye ni debe sembrarse con el del autor. Un resultado `enqueued` no significa entrega o reproducción.
9. Una instalación nueva parte con Proactivo desactivado por defecto; no confundir ese default con la instalación del autor: los cierres posteriores del 27 y 29 de octubre de 2026 documentan Proactivo ACTIVO y aprobación humana expresa. El panel ya no lo etiqueta BETA; Nuevo evento doméstico y su editor sí conservan BETA. Capacidades, ocupación y noche se revalidan fail-closed. Nuevas recepciones cron OFF; extracto y voz opt-in. No crear un cron paralelo ni interpretar guardar como permiso para enviar una prueba. No importar la configuración activa del autor ni restaurar un estado OFF histórico. Véase `UPDATE-20261101.md` para el registro compartido y la política del opener.
10. Rollback futuro limitado a fuentes/entrada propias, sin restaurar registros globales o estado vivo de observadores. Envíos, audio, micrófono, idioma y reinicios necesitan permisos independientes.

Nada de esta secuencia se ha ejecutado en esta tarea.
