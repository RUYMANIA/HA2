# HA² — Home Hermes Agent Assistant · firmware

Snapshot documental saneado actualizado a **HA² 1.3.2**, basado en el cierre de `ha2-okey-hermes-20261029`, para archivo en un repositorio **privado**. Los recursos y pruebas sin cambios conservan su procedencia 1.3.1 en el manifiesto. No es firmware nuevo, rediseño, portabilidad ni entrega compilable validada. No se ha tocado el árbol original, Home Assistant, el dispositivo, USB, OTA ni servicios.

## Qué contiene

Once encabezados, entrada ESPHome, configuración y hardware originales, cinco YAML vendor, once GIF finales, los dos PNG QR de producción/comparación, saludo Cori v2 y aviso WAV, paquete Hey Hermes con su licencia, modelo local **Okey Hermes** con manifiesto original y hashes, pruebas C++ y cuatro pruebas Python seleccionadas. No incluye secretos, binarios OTA/factory/ELF, cachés, logs originales, respaldos, informes domésticos ni herramientas operativas de despliegue.

Los únicos cambios a archivos copiados son sustituciones documentales de IP LAN por `192.0.2.10`, directorio de usuario por `/path/to/user` y MAC por `00:00:00:00:00:00`, donde proceda. Se mantiene el puerto y la allowlist de URL TTS; no se amplían hosts admitidos ni se parametriza/rediseña la lógica. El endpoint documental no debe usarse para despliegue.

Se conservan entidades y nombres técnicos heredados (por ejemplo `weather.forecast_casa`, IDs `xiaozhi_*`, etiquetas de habitaciones), que son ejemplos heredados y deben revisarse para otra instalación. La grafía histórica **Agent Assitant** se conserva en código/recursos; la denominación editorial es **Agent Assistant**.

## Wake word aceptada: Okey Hermes

**Okey Hermes funciona en las pruebas físicas de RUYMANIA hablando en español y en inglés**, confirmado el 1 de noviembre de 2026. Entrenado en español (`trained_languages: [es]`), integrado en 1.3.2 y distinto del modelo Hey Hermes anterior. [Artefactos, configuración y derechos](models/okey-hermes/README.md) · [Alcance de aceptación](../docs/OKEY-HERMES.md). La actualización de GitHub no vuelve a instalar ni activa el detector.

## Configuración y pruebas: límites

`secrets.example.yaml` contiene únicamente valores ficticios, incluida una clave API pública de ceros, y no configura un dispositivo. No copiar secretos reales al repositorio. No ejecutar ESPHome ni herramientas de dispositivo como parte de esta publicación documental.

Las pruebas copiadas no constituyen una suite portable: los cuatro Python conservan rutas sustituidas por `/path/to/user` y dependencias históricas; no se ejecutaron. El modo opcional HA2_MUTATE_AVATAR necesita un baseline externo no incluido. No se incorporan runners operativos ni se adaptan expectativas históricas para producir un PASS artificial.

Las ejecuciones nuevas se limitan a C++ host autónomo con clang++ y AddressSanitizer/UndefinedBehaviorSanitizer; comandos y retornos exactos en `TEST-RESULTS.json`, balance en `SNAPSHOT.md`. Los fallos de expectativas históricas, si existen, se conservan como tales. `ui_memory_probe.cpp` mide un host, no heap ESP32. No se compiló producción, no se probó hardware/audio/tacto y no se reejecutó la suite histórica completa. El cierre histórico de instalación de 1.3.1 no acredita el estado vivo actual.

## Derechos y pendientes antes de apertura pública

**No hay licencia propia ni licencia global elegida.** Conservar `THIRD_PARTY/RealDeco-LICENSE` y `models/hey-hermes/LICENSE` con sus ámbitos. GIF/logo/QR/audio/voz/música se archivan por autorización privada: derechos y procedencia de redistribución pública **sin validar**. No quedan bajo MIT por acompañar al código. Véase `THIRD_PARTY/PROVENANCE.md`.

Antes de abrir: resolver derechos creativos y dependencias remotas (fuentes, FLAC, stock wake words), revisar secretos y metadatos de todos los recursos, decidir licencia propia y preparar fixtures/configuración reproducibles bajo un encargo separado. No se promete compilación offline ni suites portables.

`SHA256-MANIFEST.json` registra SHA-256 origen/copia por archivo seleccionado y hashes de los auxiliares nuevos. `SNAPSHOT.md` registra sustituciones sin revelar los valores privados.
