# Alcance y cambios de la instantánea

## Actualización — 1 de noviembre de 2026

Se sincronizan cuatro fuentes por SHA instalado exacto en los cierres posteriores del 27 y 29 de octubre, **sin copiar candidatos completos**. Detalles y autoridades en `UPDATE-20261101.md`; procedencia origen/copia actual y anterior en `MANIFEST.json`. Se incorporan pruebas puras de actividad/cron/coordinador/frontend y la ampliación nativa de invitaciones cortas (ésta requiere HA y no se ejecuta completa). El runner offline añadido y los probes AST no son runners Docker ni una simulación de HA compatible.

Ejecución final de esta copia: **71 casos Python y 58 Node PASS**; salida actual separada de la histórica en `TEST-RESULTS.json`. No se suman pasadas ni recuentos de otros cierres. No se modifica firmware, voz, guards ni lógica respecto de los fuentes seleccionados. El resto de componentes retiene la procedencia original. No se ha accedido a servicios, producción ni hardware; sin despliegue/reinicio, inferencia, micrófono, stage/commit/push ni licencia propia.

Los cierres documentan Proactivo activo y aprobado sin BETA; eso no modifica el default OFF de una instalación nueva ni prueba estado vivo actual. El Log de Actividad comparte Store y retiene 200 eventos; la primera actividad nueva enriquecida y la primera invitación natural no quedan acreditadas por estas pruebas. No reconstruir historia ni apagar configuraciones a partir de staging congelado.

## Registro histórico inalterado — 26 de octubre de 2026

**Lo que sigue describe sólo la fase inicial, no el estado ni el alcance de la actualización anterior.** Sus contadores, selección de una sola raíz y frases de futura aceptación se conservan como historia; para el estado documentado posterior prevalecen los cierres resumidos en `UPDATE-20261101.md`.

Fecha de trabajo: **2026-10-26**. Estado: **snapshot privado de fuentes**, no distribución portable, no despliegue y no lectura del estado vivo. Se parte exclusivamente de la raíz lógica `ha2-notifications-0.3.0`; no se mezclan versiones anteriores, firmware o receipts operativos.

## Lista positiva y cambios

- Se copiaron los dos componentes preservando estructura: únicamente `.py`, `.json`, `.yaml`, `.js`, PNG de `brand/` y el recurso `static/proactive-three-notes.wav`. `VERSION` y archivos fuera de esa lista no se copian; el manifest y constantes conservan 0.3.0.
- Backend: únicamente `test_*.py`. Frontend: únicamente `*.test.mjs`, `dom-harness.mjs`, `build-wrapper.mjs`, `wrapper-fixture.js`.
- Otras áreas: fuentes `test_*.py` revisadas, sin acciones live. Sus necesidades de HA real, archivos sintéticos y módulos de otro subsistema se explican en `TESTING.md`. Se excluye `test_provider_bootstrap.py` por sus servidores HTTP de prueba; no se confunde fixture de red con prueba pura.
- Saneamiento **sólo en la copia**: cuatro apariciones de IPv4 RFC1918 en `tests/backend/test_ha.py` se reemplazaron por `192.0.2.10`. No se registran aquí valores anteriores. No hubo rutas de usuario o MAC que sustituir en la lista seleccionada. Los hashes registran esta única diferencia de fuentes.
- No se alteraron prefijos, entidades, lógica, guardas, orden de UI, defaults o código operativo original. Los 28 archivos de componentes quedan byte a byte iguales a su origen.
- Se añadió documentación nueva, MIT upstream separada y resultados de ejecución de la copia. No se eligió licencia propia ni global. WAV permitido para archivo privado, con puerta de derechos pendiente antes de público.

## Evidencia propia y límites

Se ejecutaron **12 + 3 = 15 pruebas Python puras** y **54 Node**, todas correctas con salida real conservada en `TEST-RESULTS.json`. Las demás pruebas archivadas no se ejecutaron. El parseo AST de los 40 Python copiados fue correcto. No se generó wrapper, caché Python ni resultado histórico de navegador.

`MANIFEST.json` contiene por cada archivo copiado ruta relativa, SHA-256/longitud de origen y de copia, y contadores de reemplazos; los nombres de raíz son lógicos y no contienen rutas domésticas. La licencia upstream tiene su propia procedencia y hashes. La sección `generated_files` identifica y verifica la documentación y el resultado nuevos, no finge que tengan un origen histórico. El manifiesto no incluye su propio hash para evitar autorreferencia.

Se verifican nuevamente los hashes de origen y copia al cierre, el total de archivos y la lista positiva. Los hashes no publican el contenido excluido ni prueban despliegue. No hay acceso a hardware, HA vivo, servicios, Store, credenciales, sesiones ni contenedor operativo. No se ejecutaron runners Docker, instaladores, comandos de git stage/commit/push ni cambios fuera de `homeassistant/` del repositorio.

El backend 0.3.0 y el hash del panel son identidad de fuentes, no estados actuales. No se importan reglas, colas o configuraciones domésticas ni se reproducen resultados históricos de instalación. La futura activación/aceptación física queda fuera del alcance de este archivo.
