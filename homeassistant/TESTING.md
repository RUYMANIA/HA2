# Pruebas del snapshot

## Resultado real y alcance ejecutado

`TEST-RESULTS.json` conserva entorno, comandos, códigos de salida y salida real saneada. En la copia: Python **3.11.15**, Node **v22.23.1**; `test_engine.py` **12 OK**, `test_review_gates.py` **3 OK**, Node **54 pass / 0 fail**. No se atribuyen estos resultados al resto de pruebas archivadas ni a HA real.

Desde este directorio, los comandos equivalentes son:

```sh
python -I -B -m unittest discover -s tests/backend -p test_engine.py -v
python -I -B -m unittest discover -s tests/backend -p test_review_gates.py -v
node --test tests/frontend/panel.test.mjs tests/frontend/cron.test.mjs tests/frontend/proactive.test.mjs
```

Los dos comandos Python cargan `engine.py` por ruta, con Store/reloj/sender de memoria y sin importar el setup HA. Sólo biblioteca estándar, incluidos datos de zonas horarias disponibles para `zoneinfo`. No determinan el Python mínimo de Home Assistant. Node usa módulos nativos `node:test`, `structuredClone` y ESM; no hay npm/build, lockfile ni paquetes frontend instalados. El DOM simulado no demuestra renderizado de navegador.

## Resto archivado: offline no significa autosuficiente

Se revisaron fuentes y fronteras de efectos antes de copiarlas: no se incluyen tests que contacten servicios operativos. Aquí «offline» incluye pruebas de clases reales HA con IO simulado; **no** significa que todas usen sólo biblioteca estándar. Estas suites adicionales **no se ejecutaron**.

| Área | Dependencias/fronteras que conserva |
|---|---|
| `backend/test_cron.py` | Engine y `test_engine`; su import de paquete pasa por el setup HA, por lo que requiere un entorno HA o carga aislada externa. No se añadió bootstrap ni runner. |
| Otros `backend/test_*.py` | Clases HA reales, `voluptuous` y dependencias transitivas `aioesphomeapi`; registros/services/state machine locales, Store de prueba y handlers simulados. Algunas escriben configuración de prueba dentro de la copia. No usar discovery global indiscriminado. |
| `audio_followup` | Importa `backend/test_ha.py`; HA real y transporte con reloj, TTS y servicios fixture. Sin reproducción física. |
| `lifecycle_followup` | HA, `voluptuous`; instancia no iniciada, registro local, Store aislado y efectos de dispositivo prohibidos. Puede crear `isolated-config/` en una futura ejecución. |
| `proactive_backend/test_scheduler.py` | Biblioteca estándar, carga por ruta de `proactive.py`, reloj/RNG fixture. |
| `proactive_backend/test_coordinator.py`, `test_native_capability.py`, `test_ownership.py` | Motor/coordinador reales con Store/transport de memoria; imports de paquete HA y fixtures hermanos. No modelos ni hardware. |
| `proactive_backend/test_ws.py` | HA, `voluptuous`, Store local; registro WS sin servidor, worker local y transporte fixture. Puede escribir configuración aislada. |
| `native_conversation/test_adapter_context.py` | HA conversation/chat log y adaptador; cliente inference sustituido por fixture. Conserva ruta `/config/.ha2-development-tests/native-fixture` como literal histórico, no autorización de acceso. |
| `native_conversation/test_client_capability.py` | `aiohttp` y adaptador/HA; `_request_json` se sustituye antes de invocar; `fixture.invalid` no se consulta. |
| `native_conversation/test_native_ingress.py` | HA y `aioesphomeapi` reales; conexión/subscripción/API fixture, sin socket. Guardas/versiones siguen siendo necesarias. |
| `native_conversation/test_native_starter.py`, `test_native_transport.py` | HA/ESPHome reales, anuncio/ACK/modelo/resolver fixture; ruta `/config/.ha2-development-tests/native-flow` conservada. No iniciar en HA vivo. |
| `native_conversation/test_timing_boundary.py` | Depende de `native_provider/ui_timing_runtime.py`, **fuera de esta instantánea**; inference/sender inyectados. No ejecutable de manera autónoma aquí. |
| `contract/test_compat.py` | Engine cargado por ruta, Store y busy sender de memoria; biblioteca estándar. No ejecutada. |
| `integration/test_bridge_engine.py` | Depende de `hermes_bridge.bridge`, **fuera de este directorio**; SQLite y archivos temporales sintéticos con `TMPDIR`, WS cliente fixture. No lee bases vivas ni dispara scheduler/altavoz. No ejecutable de manera autónoma aquí. |

No se han copiado dependencias HA/terceras ni se han instalado para ejecutar suites extra. Para evaluarlas en el futuro, usar sandbox efímero dedicado, resolver imports hermanos y dependencias explícitamente y mantener todas las fronteras offline. No cambiar imports/lógica archivados sólo para obtener PASS.

## Exclusiones deliberadas

No se copian `run.py`, `run-tests.mjs`, runners Docker, pruebas de navegador, fixtures generados, resultados históricos, snapshots de pruebas, wrapper HTML ni capturas. `test_provider_bootstrap.py` se excluye aunque use fixtures: crea servidores HTTP/socket locales y requiere `native_provider`, por lo que no es una prueba pura sin red.

Se conservan sólo los tres `*.test.mjs`, `dom-harness.mjs`, `build-wrapper.mjs` y el **fuente** `wrapper-fixture.js`. `build-wrapper.mjs` escribe `wrapper.html`: se archiva como fuente, **no se ejecutó** y su resultado no se incluye. Los comandos Node anteriores no lo necesitan.
