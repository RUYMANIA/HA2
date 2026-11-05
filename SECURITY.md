# Seguridad y publicación

## Alcance del repositorio

Archivo saneado de fuentes y recursos seleccionados para publicación abierta. No sustituye al respaldo privado de configuración y no contiene las credenciales necesarias para conectar con una vivienda real.

## Exclusiones obligatorias

- Secretos Wi-Fi, API ESPHome, OTA, tokens HA/Hermes, llavero y autenticación GitHub.
- Bases de datos, config entries, `.storage`, perfiles, sesiones, transcripciones, reglas domésticas y registros de voz.
- Backups, snapshots de hardware/HA, recibos de instalación con identidades y herramientas de operación ligadas a la vivienda.
- OTA, factory y ELF de la instalación original: se detectó configuración privada incrustada en el OTA; no debe publicarse en ninguna revisión, independientemente de la visibilidad del repositorio.

Las direcciones `192.0.2.10`, las MAC nulas y `/path/to/user` son sustituciones documentales, **no datos de conexión funcionales**. Los identificadores técnicos heredados del dispositivo se conservan como ejemplos; no representan inventario de una instalación destinataria.

## Defaults heredados

`firmware/config/core.yaml` y `firmware/vendor/core.yaml` conservan una contraseña AP literal del upstream. Es un default heredado, no una credencial doméstica extraída. La entrada principal la sobrescribe mediante `!secret fallback_ap_password`. Para cualquier instalación, configurar un secreto propio y comprobar la configuración efectiva; no usar el default como credencial de producción.

## Fronteras que deben preservarse

- Autenticación y autorización administrativa de HA; no introducir tokens en JavaScript/localStorage.
- Allowlist del origen TTS y de `/api/tts_proxy/`; no sustituirla por aceptación de cualquier URL.
- Correlación por identidad/generación, TTL, propiedad del audio, ACK booleanos y rechazo de cancelaciones antiguas.
- Perfil/home y lecturas protegidas del ledger de Hermes; no habilitar observación de todos los perfiles.
- Guardas fail-closed de compatibilidad del modo proactivo; no retirarlas para aparentar portabilidad.
- Modo noche, ocupación del satélite y herencia de voz de la pipeline correspondiente.

## Mantenimiento

Una actualización de documentación no autoriza OTA, reinicios, recarga de plugins ni pruebas con audio/micrófono. Revisar el alcance operativo antes de cada acción. Mantener aislados los entornos de prueba; no ejecutar los tests dentro del contenedor Home Assistant de producción.

Antes de cualquier apertura pública, revisar secretos en **todo el historial Git**, derechos de recursos, identificadores, dependencias y capacidades anunciadas. Si se detecta un secreto publicado, revocarlo/rotarlo antes de limpiar el historial; borrar el último archivo no elimina las copias históricas.

Comunicar incidencias por un canal privado del propietario. No incluir credenciales, transcripciones ni topología de red en issues.
