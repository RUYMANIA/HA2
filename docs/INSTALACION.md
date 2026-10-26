# Instalación y dependencias — guía de ingeniería

> **No es una distribución plug-and-play.** Este snapshot sanea rutas/identidades y omite credenciales y artefactos privados. No desplegarlo sobre una instalación existente sin revisión, configuración local, pruebas y autorización. Los originales operativos no se han alterado para preparar GitHub.

## Matriz de referencia

| Capa | Referencia documentada | Precaución |
|---|---|---|
| Hardware | XiaoZhi Ball V2 ESP32-S3, flash 16 MB, PSRAM octal | No reutilizar pinout de otra variante |
| Firmware | ESPHome 2026.9.1, ESP-IDF | Fuentes/modelos/sonidos remotos y toolchain se resuelven por separado |
| Home Assistant | 2026.7.2 para la vía proactiva auditada | Versión y fingerprints exactos; otras versiones no están acreditadas |
| Python pruebas puras | 3.11 en la referencia local | No equivale al Python mínimo del runtime HA |
| Node pruebas DOM | 22.23.1 en la referencia local | Tests ESM nativos; no acredita navegador autenticado |
| Hermes | Runtime gestionado, referencia de commit en THIRD_PARTY | No inferir release a partir del pyproject local 0.0.0 |

## Orden recomendado

1. Leer SECURITY, derechos y README de cada superficie. Crear un entorno de trabajo separado, no usar el contenedor HA de producción para tests.
2. Revisar la configuración ESPHome de ejemplo: nombres y entidades heredados deben corresponder a la instalación destinataria. Crear secretos **localmente** a partir del ejemplo, con claves propias; nunca versionarlos.
3. Resolver el origen de TTS permitido de forma coordinada entre firmware y backend. `192.0.2.10` es una dirección documental; no ampliar la allowlist para que la demo funcione con cualquier URL. Ejecutar config/build y pruebas en un entorno aislado antes de plantear flasheo. No se incluyen binarios originales.
4. Preparar Hermes Agent y el companion compatibles, con sus dependencias, autenticación local y helper de timing. Revisar las rutas reemplazadas y las guardas de perfil; copiar el snapshot no registra un servicio ni configura un LaunchAgent.
5. Preparar el adaptador HA `hermes_agent` y `ha2_notifications` en `<config>/custom_components/`. Respaldar fuentes/configuración propia de forma privada y revisar compatibilidad antes de reiniciar. No hay integración HACS verificada.
6. Tras la autorización correspondiente, recargar/reiniciar sólo los procesos necesarios y verificar exactamente qué código está cargado. No confundir reiniciar companion con recargar plugin/gateway/HA.
7. Añadir HA² Notifications mediante el flujo de integración. Requiere prefijo de satélite y entidad `weather.*` reales; el formulario valida entidades y servicios. No inventar sensores para salvar la validación.
8. Comprobar panel vacío y nuevos controles desactivados antes de programar avisos. No importar reglas domésticas del autor. Proactivo sigue BETA y apagado hasta superar puertas específicas.

## Entidades y acciones exigidas por el config flow

Para `<prefix>`: sensores `card_status`, `ui_status`, `ui_night`; binario `card_active`; media player; assist_satellite y selector de asistente. Las acciones ESPHome de tarjeta deben existir con el mismo prefijo. La UI heredada conserva un selector de idioma fijo: consultar README de Home Assistant, no anunciar soporte multidispositivo genérico.

## Actualización, recuperación y desinstalación

Verificar versión, identidad, hashes y salud propios antes y después. Respaldar únicamente lo que se modifica; no congelar/restaurar checkpoints de un observador vivo ni registros globales HA como atajo. Una diferencia de configuración global no se declara benigna sin baseline.

La reversión afecta sólo a fuentes/integración/entrada propias y requiere su procedimiento privado. Esta publicación no incluye un instalador o rollback universal, ni da permiso para reinicios/OTA. Cada prueba de audio, escucha, reinicio y flash exige su alcance operativo correspondiente.
