# Okey Hermes — modelo local microWakeWord

**Integrado en HA² 1.3.2 y probado físicamente por RUYMANIA. Funciona en sus pruebas tanto hablando en español como en inglés.** Confirmación bilingüe aportada el **1 de noviembre de 2026**; no se ha repetido ni grabado esa prueba para publicar el repositorio.

## Qué contiene

- `okey_hermes.tflite`: pesos originales, **137.984 bytes**, SHA-256 `c3a747d398c526c0d1f092ae315a9aa10d3df8e3051379c2227dd14aec56b974`.
- `okey_hermes.esphome.json`: manifiesto original para ESPHome microWakeWord, schema v2, nombre exacto **Okey Hermes** y referencia local relativa al TFLite.
- `SHA256SUMS`: integridad de ambos artefactos, no firma ni garantía acústica.

El manifiesto conserva la autoría y website del exportador original. No se ha renombrado a «Okay», «Hey» ni «Ey Hermes». El modelo inglés anterior **Hey Hermes** es un recurso distinto y se conserva como tal.

## Entrenamiento frente a prueba de uso

El modelo se entrenó con `trained_languages: [es]`. Que RUYMANIA lo haya probado con éxito hablando en **español e inglés** no cambia el idioma declarado de entrenamiento ni implica entrenamiento bilingüe. Una wake word detecta la frase de activación; idioma del menú y STT/TTS de la conversación son capas distintas.

La prueba física inicial de 29-10-2026 ya estaba aceptada y corroborada por el diagnóstico de detección de HA. La confirmación posterior amplía el alcance de uso aceptado a ambos idiomas, sin inventar porcentaje de aciertos, distancia, latencia ni tasa de falsas activaciones.

## Integración preservada

La entrada `firmware/xiaozhi-ball-v2.yaml` añade este quinto modelo al final con ID `okey_hermes_experimental` e `internal: false`, manteniendo los cuatro anteriores y sus IDs. El identificador histórico no se cambia por actualizar su aceptación. ESPHome aplica sus defaults y después restaura preferencias propias; no se fuerza desactivación en cada arranque. La configuración elegida por el usuario no se publica como secreto ni se cambia mediante esta actualización.

- Cutoff original: **0.99**.
- Ventana: **7**.
- Feature step: **10**.
- Arena mínima declarada: **30.000 bytes**; no equivale al heap total ni a una medición de RAM ESP32.
- ESPHome mínimo declarado por el manifiesto: **2024.7.0**. Entorno con que se compiló el firmware instalado: **2026.9.1**.

No se necesitan el entrenador ni los datasets para detectar la frase en el dispositivo ya compilado. No se incluyen corpus, grabaciones, checkpoints, bundle Tater ni credenciales. El manifiesto ESPHome es el artefacto de integración, no el bundle del entrenador.

## Derechos y límites

**Incluido públicamente, pero expresamente fuera de MIT.** RUYMANIA no concede una licencia abierta alternativa ni permiso comercial para estos pesos; tampoco una autorización general de reutilización no comercial. Véase [LICENSE.md](LICENSE.md), con el ámbito exacto, los derechos que se conservan, las atribuciones y las incertidumbres. La disponibilidad en GitHub no equivale a que todo uso esté autorizado.

Se han identificado negativos de entrenamiento de un corpus **CC BY-NC 4.0**. La receta de síntesis contempla generadores con pesos NC, sin trazabilidad suficiente para atribuir su uso efectivo en esta corrida. No se concluye que esas condiciones se transmitan automáticamente al detector ni se les asigna automáticamente CC BY-NC. La licencia del código de HA² no elimina derechos de terceros. No se publican el entrenador, datasets, grabaciones o checkpoints; tampoco OTA/ELF/factory del hogar. Pesos y manifiesto se conservan byte-idénticos, sin tocar el detector instalado.
