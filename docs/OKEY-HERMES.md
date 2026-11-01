# «Okey Hermes»: integración y validación en español e inglés

**Estado: integrado, activo y con prueba física aceptada. RUYMANIA confirma que funciona hablando en español y en inglés.** Confirmación bilingüe recibida el **1 de noviembre de 2026**.

## Versiones y evidencia

- Firmware **HA² 1.3.2**, build **2026-10-29 13:28:53 UTC**, instalado el 29 de octubre según cierre posterior a staging.
- Integración append-only: quinto modelo, ID `okey_hermes_experimental`, visible para el selector HA, sin cambiar los cuatro modelos y preferencias anteriores.
- El cierre OTA conservó el detector previo; después el usuario eligió **Okey Hermes**. La aceptación inicial del 29 de octubre fue corroborada por selector y evento de detección concordantes. No atribuir a Hermes el cambio de selección ni restaurar el detector anterior.
- La confirmación de 1 de noviembre amplía la aceptación humana a uso **en ambos idiomas**. No se ha lanzado otra prueba de escucha, audio o selección para documentarlo.

## Archivos publicados

- [Pesos TFLite](../firmware/models/okey-hermes/okey_hermes.tflite), **137.984 bytes**.
- [Manifiesto ESPHome original](../firmware/models/okey-hermes/okey_hermes.esphome.json).
- [Hashes y alcance del modelo](../firmware/models/okey-hermes/README.md).
- [Entrada del firmware](../firmware/xiaozhi-ball-v2.yaml) y metadatos de versión/Info actualizados a 1.3.2.

SHA-256 TFLite: `c3a747d398c526c0d1f092ae315a9aa10d3df8e3051379c2227dd14aec56b974`. El manifiesto referencia el archivo por ruta relativa y conserva nombre, autoría, website, cutoff **0.99**, ventana **7** y `trained_languages: [es]`.

## Qué significa «funciona en ambos idiomas»

La frase de activación es **Okey Hermes**. RUYMANIA la ha probado hablando en español y en inglés y comunica que funciona para ambos. Eso acredita esa experiencia física; **no significa que el entrenamiento se haya hecho en dos idiomas**, ni convierte las métricas de calibración en un benchmark de las voces del hogar.

Se mantienen separadas:
1. Detección local de la frase mediante microWakeWord.
2. Idioma elegido para menús English/Español.
3. Idiomas STT/TTS y conversación de la pipeline seleccionada.

**Okey Hermes** no es el modelo anterior **Hey Hermes**, ni debe publicarse renombrando sus pesos o etiquetas. El entrenador y los datasets no se necesitan para detección en la Ball compilada; no se incluyen corpus ni grabaciones.

## Pruebas históricas y límites

El cierre de firmware documenta compilación ESPHome 2026.9.1/ESP-IDF 5.5.5, 67 puertas host, 25 recursos previos preservados y una única adición de pesos idénticos, más inferencias CPU sintéticas. Son evidencia histórica, no nuevas ejecuciones de esta actualización del repositorio ni pruebas de audio por sí mismas.

La confirmación humana ya cierra la activación y la primera prueba del detector; no se mantienen como pendientes. No se han cuantificado distancia, tasa prolongada de falsos positivos, latencia o heap. No se inventan cifras ni se exige otra prueba para aceptar lo ya confirmado.

La publicación no ha cambiado firmware, selección, voz, canalizaciones o servicios. No se incluyen binarios OTA/ELF del hogar ni recibos privados. Se mantiene el repositorio privado y la política de derechos; no se aplica automáticamente la licencia MIT del modelo inglés a este entrenamiento local.
