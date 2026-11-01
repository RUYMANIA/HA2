# Pruebas offline de la copia

## Ejecución final del 1 de noviembre de 2026

`TEST-RESULTS.json` separa `current_execution` de `historical_execution_2026_10_26`. La ejecución final actual tiene **71 casos Python y 58 Node, todos PASS**. No se suman la primera pasada exploratoria, las repeticiones finales, los resultados históricos ni los recuentos de los cierres de instalación. El runner Python verifica IDs únicos en su selección explícita. Son casos ejecutados, no una medida de cobertura ni 129 entregas.

Entorno comprobado: Python **3.12.13**, Node **v22.23.1**. No se instala ninguna dependencia. Desde este directorio, con Python que soporte estas fuentes y `zoneinfo`:

```sh
python -I -B tests/offline/run.py
TZ=America/Los_Angeles node --test tests/frontend/panel.test.mjs tests/frontend/cron.test.mjs tests/frontend/proactive.test.mjs tests/frontend/activity.test.mjs
```

En este Mac se utilizó el intérprete aislado de desarrollo ya existente; el reporte scratch para el padre conserva su ruta local, sin añadirla al repositorio. `HOME`, `HERMES_HOME` y `TMPDIR` se establecieron a directorios fixture efímeros durante la ejecución final. No se lee configuración real de Hermes ni HA. No ejecutar discovery global: hay suites archivadas con otras dependencias.

## Selección Python pura

`tests/offline/run.py` incluye una allowlist explícita. Resuelve el namespace vacío `custom_components.ha2_notifications` sin ejecutar su `__init__.py`; carga los módulos puros reales sin fingir una versión o clase HA. Esto **no acredita integración ni compatibilidad de Home Assistant**. Un audit hook rechaza `socket.connect`, `socket.bind`, `subprocess.Popen` y `os.system`; no es un sandbox de seguridad general.

| Área ejecutada | Frontera |
|---|---|
| `backend/test_engine.py`, `test_review_gates.py` | Engine real, Store/reloj/sender de memoria; retención actualizada a 200. |
| `backend/test_cron.py`, `test_activity.py` | Engine y auxiliares reales, persistencia de memoria, metadatos y revisiones; no puente ni WS real. |
| `proactive_backend/test_scheduler.py`, `test_coordinator.py`, `test_native_capability.py`, `test_ownership.py`, `test_activity_log.py` | Scheduler/coordinador reales con transporte inerte; retención común, estados, cancelación, owner ajeno, duplicados, fallos de commit y conservación de configuración activa fixture. No inferencia ni micrófono. |
| `contract/test_compat.py` | Engine cargado por ruta, Store y sender ocupado de memoria. |
| `offline/test_short_opener.py` | AST sin modificar del validador, constantes y clase de `native_transport.py`; sólo imports stdlib, resolver/client/gate/starter fixture. Ejercita límites 120/20/240, Unicode, formato, no truncar/reintentar, contexto exacto, prompt, doble validación y ownership. **No importa HA, no ejecuta la rama nativa por defecto de `_resolve`, ni valida compatibilidad, audio, escucha o guards HA en ejecución.** |

Los imports se aíslan sólo en el proceso de pruebas, no se modifica código operativo. Los fingerprints y guards de los componentes permanecen intactos. La selección nueva se valida sobre los hashes finales; no se cambian expectativas para ocultar un fallo del código instalado.

## Node

Cuatro `*.test.mjs`: las tres suites existentes más `activity.test.mjs` del cierre de rótulos. Prueban ES/EN, 200 filas sin deduplicarlas, origen legacy honesto, estados no equivalentes a entrega, zona HA/DST con zona de navegador simulada distinta, texto XSS literal, scroll/nodos/borradores y BETA sólo en eventos domésticos. El transporte WS es fixture. Node usa `node:test`, ESM y el DOM simulado local, sin npm ni navegador real: no demuestra layout, accesibilidad física o actualización de Safari.

`dom-harness.mjs`, `build-wrapper.mjs` y `wrapper-fixture.js` conservan sus fuentes originales. **No se ejecuta** `build-wrapper.mjs` ni se genera `wrapper.html`.

## Resto archivado: no ejecutado en esta revisión

| Área | Límite honesto |
|---|---|
| Otros `backend/test_*.py`, `audio_followup`, `lifecycle_followup`, `proactive_backend/test_ws.py` | Requieren clases/dependencias HA reales y registros/servicios fixture. No se usa el contenedor vivo para resolverlas. |
| `native_conversation/test_native_transport.py` | Se incorpora la ampliación del 29 de octubre (límites, no retry, contexto, modos y conversación manual no restringida). La suite completa requiere HA/ESPHome y fixtures hermanos; **no se ejecutó**. Los probes AST anteriores no sustituyen esa suite. |
| Otros `native_conversation/test_*.py` | Dependen de HA, `aioesphomeapi`, `aiohttp` o adaptador real. `test_timing_boundary.py` requiere `native_provider/ui_timing_runtime.py`, fuera de este directorio. |
| `integration/test_bridge_engine.py` | Requiere `hermes_bridge.bridge`, fuera de este directorio; no ejecutable autónomamente aquí. |

No se añaden dependencias ni bootstrap que simule HA compatible. Las rutas históricas `/config/.ha2-development-tests/` de fixtures no son autorización para acceder a una instalación. Una futura comprobación de clases HA requiere laboratorio offline dedicado y dependencias resueltas; no comandos contra producción.

## Exclusiones y procedencia

No se copian runners Docker, instaladores, pruebas de navegador, snapshots/receipts privados, Store, bases de datos, capturas, archivos generados ni resultados operativos. El nuevo `tests/offline/run.py` es un runner **puro**, no el runner Docker del proyecto original. `test_provider_bootstrap.py` sigue excluido: abre sockets y depende de `native_provider` no archivado. No se importan tests de upgrade/plugin/runtime ajenos a esta superficie.

El manifiesto registra hashes de origen/copia y conserva los anteriores. Resultados actuales contienen comandos, salida real saneada y huella de todos los fuentes de componentes y pruebas. Un parseo AST de los Python y hashes de archivo no equivalen a una prueba HA.

## Ejecución histórica — 26 de octubre de 2026

La primera instantánea ejecutó 15 casos Python (12 Engine y 3 review gates) y 54 Node con Python 3.11.15 y Node v22.23.1. Su salida original permanece en `historical_execution_2026_10_26`; no describe los nuevos hashes ni se suma a los resultados actuales. Los cierres privados posteriores conservan sus fases RED/GREEN y sus propios recuentos, que tampoco se reproducen como pruebas nuevas de esta copia.
