# Okey Hermes — exclusión expresa de MIT

**Estado a 5 de noviembre de 2026: incluido en el repositorio público, pero sin licencia abierta alternativa concedida para los pesos.**

## Alcance

La licencia MIT de la raíz de HA² **no se aplica a `okey_hermes.tflite` ni se atribuye por este documento al manifiesto exportado `okey_hermes.esphome.json`**. No se adopta la licencia del modelo distinto Hey Hermes, la del entrenador o la de las dependencias como licencia automática del detector local.

RUYMANIA autoriza su inclusión como artefacto de referencia del proyecto, **no una concesión adicional de derechos de uso, modificación o redistribución de los pesos**, ni comercial ni no comercial. Se mantienen los derechos que correspondan por la legislación, por las licencias realmente aplicables y por los términos de GitHub —incluida la visualización y el fork dentro del servicio—. No se concede aquí permiso de explotación comercial ni se garantiza que todos los derechos del entrenamiento estén resueltos. Para permisos adicionales, consultar al propietario del proyecto y a los titulares que corresponda.

Esto **no es una licencia CC BY-NC asignada a los pesos**. El modelo no se presenta como software/modelo abierto ni como libre de restricciones. La documentación y el código original de HA² sí tienen el ámbito MIT descrito en [la política general](../../../LICENSE.md).

## Procedencia y motivo de la separación

- Entrenamiento local del proyecto finalizado el **29 de octubre de 2026**, idioma `es`; artefactos originales conservados sin modificar.
- SHA-256 de los pesos: `c3a747d398c526c0d1f092ae315a9aa10d3df8e3051379c2227dd14aec56b974`.
- SHA-256 del manifiesto: `898d95b9c63d6e4c2d40fa5337f15777e532e14ab532acdd6d6b964ce9b79981`.
- Negativos de entrenamiento preparados desde **kahrendt/microwakeword**, cuyo dataset declara **CC BY-NC 4.0**. Su [modelcard histórica fijada](https://huggingface.co/datasets/kahrendt/microwakeword/blob/0da95f94302ca2f4aae3b18fc6560fa6d2bba3d1/README.md) identifica, entre otras fuentes, CHiME6/DipCo, FMA/FSD50K/WHAM y LibriSpeech/VOiCES. Se atribuye el dataset a sus autores y se preservan sus condiciones; **el dataset no se redistribuye aquí**.
- La receta de síntesis `modern` admite varios generadores. La [modelcard fijada de OmniVoice](https://huggingface.co/k2-fsa/OmniVoice/blob/c5fdb5ccb189668d56333f77ba2629f4cd7535f4/README.md) distingue código Apache 2.0 y pesos CC-BY-NC. No se ha acreditado qué generadores produjeron cada positivo de esta corrida: **no se afirma que OmniVoice se utilizara**.
- Tampoco hay inventario completo de augmentaciones efectivamente utilizadas. No se reconstruyen datasets ni se publican grabaciones, checkpoints o el bundle del entrenador.
- El campo `author: Tater Totterson` y su website proceden del exportador; conservarlos no equivale a atribuirle el entrenamiento local ni a afirmar que ha concedido una licencia sobre estos pesos.

Usar datos con condición NC **no demuestra por sí solo que el detector herede automáticamente esa licencia**. Esta exclusión conserva explícita la incertidumbre y evita prometer MIT o uso comercial irrestricto; **no sustituye una revisión específica de derechos ni elimina condiciones de terceros**.

## Interpretación en el historial

Esta aclaración acompaña al mismo artefacto que estaba en el archivo privado y que permanece byte-idéntico. No se ha reescrito el historial ni se pretende que el nuevo MIT de la raíz relicencie estos archivos en revisiones anteriores. Las referencias históricas a «archivo privado» describen su estado anterior, no la visibilidad actual.
