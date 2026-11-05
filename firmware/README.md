# HA² — Home Hermes Agent Assistant · firmware

Snapshot documental saneado actualizado a **HA² 1.3.2**, basado en el cierre de `ha2-okey-hermes-20261029`, para publicación del archivo saneado bajo **MIT en su código/aportaciones originales no excluidas**, conservando avisos de terceros. **Okey Hermes está incluido fuera de MIT**, sin licencia abierta alternativa concedida para los pesos. Los recursos y pruebas sin cambios conservan su procedencia 1.3.1 en el manifiesto. No es firmware nuevo, rediseño, portabilidad ni entrega compilable validada. No se ha tocado el árbol original, Home Assistant, el dispositivo, USB, OTA ni servicios.

## Qué contiene

Once encabezados, entrada ESPHome, configuración y hardware originales, cinco YAML vendor, once GIF finales, los dos PNG QR de producción/comparación, saludo Cori v2 y aviso WAV, paquete Hey Hermes con su licencia, modelo local **Okey Hermes** con manifiesto original y hashes, pruebas C++ y cuatro pruebas Python seleccionadas. No incluye secretos, binarios OTA/factory/ELF, cachés, logs originales, respaldos, informes domésticos ni herramientas operativas de despliegue.

Los únicos cambios a archivos copiados son sustituciones documentales de IP LAN por `192.0.2.10`, directorio de usuario por `/path/to/user` y MAC por `00:00:00:00:00:00`, donde proceda. Se mantiene el puerto y la allowlist de URL TTS; no se amplían hosts admitidos ni se parametriza/rediseña la lógica. El endpoint documental no debe usarse para despliegue.

Se conservan entidades y nombres técnicos heredados (por ejemplo `weather.forecast_casa`, IDs `xiaozhi_*`, etiquetas de habitaciones), que son ejemplos heredados y deben revisarse para otra instalación. La grafía histórica **Agent Assitant** se conserva en código/recursos; la denominación editorial es **Agent Assistant**.

## Wake word aceptada: Okey Hermes

**Okey Hermes funciona en las pruebas físicas de RUYMANIA hablando en español y en inglés**, confirmado el 1 de noviembre de 2026. Entrenado en español (`trained_languages: [es]`), integrado en 1.3.2 y distinto del modelo Hey Hermes anterior. [Artefactos, configuración y derechos](models/okey-hermes/README.md) · [Alcance de aceptación](../docs/OKEY-HERMES.md). La actualización de GitHub no vuelve a instalar ni activa el detector.

## Configuración y pruebas: límites

`secrets.example.yaml` contiene únicamente valores ficticios, incluida una clave API pública de ceros, y no configura un dispositivo. No copiar secretos reales al repositorio. No ejecutar ESPHome ni herramientas de dispositivo como parte de esta publicación documental.

Las pruebas copiadas no constituyen una suite portable: los cuatro Python conservan rutas sustituidas por `/path/to/user` y dependencias históricas; no se ejecutaron. El modo opcional HA2_MUTATE_AVATAR necesita un baseline externo no incluido. No se incorporan runners operativos ni se adaptan expectativas históricas para producir un PASS artificial.

Las ejecuciones de la primera copia se limitaron a C++ host autónomo con clang++ y AddressSanitizer/UndefinedBehaviorSanitizer; comandos y retornos exactos en `TEST-RESULTS.json`, balance en `SNAPSHOT.md`. La apertura documental del 5 de noviembre no las reejecuta. Los fallos de expectativas históricas, si existen, se conservan como tales. `ui_memory_probe.cpp` mide un host, no heap ESP32. No se compiló producción, no se probó hardware/audio/tacto y no se reejecutó la suite histórica completa. El cierre histórico de instalación de 1.3.1 no acredita el estado vivo actual.

## Licencia y avisos

**MIT para el código y las aportaciones originales no excluidas de RUYMANIA**, por su autorización expresa. Conservar `THIRD_PARTY/RealDeco-LICENSE`, `THIRD_PARTY/NousResearch-hermes-agent-LICENSE` y `models/hey-hermes/LICENSE` con sus ámbitos. **Los pesos Okey Hermes están fuera de MIT, sin licencia abierta alternativa ni permiso comercial concedidos**; véase [models/okey-hermes/LICENSE.md](models/okey-hermes/LICENSE.md). No se concede una autorización general de reutilización de esos pesos. La licencia propia no sustituye derechos de terceros sobre modelos, voces o marcas. Véanse los avisos de `THIRD_PARTY/PROVENANCE.md` y `../THIRD_PARTY.md`.

Para futuras incorporaciones, verificar derechos y dependencias remotas (fuentes, FLAC, stock wake words), secretos y metadatos antes de añadirlas. La preparación de fixtures/configuración reproducibles sigue siendo trabajo separado: no se promete compilación offline ni suites portables.

`SHA256-MANIFEST.json` registra SHA-256 origen/copia por archivo seleccionado y hashes de los auxiliares nuevos. `SNAPSHOT.md` registra sustituciones sin revelar los valores privados.
