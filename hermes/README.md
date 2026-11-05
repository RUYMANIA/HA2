# Hermes — snapshot documental saneado

Archivo del estado existente, no instalador ni distribución portable. No se ha modificado la instalación, activado proactividad, enviado tarjetas, ejecutado cron ni iniciado el provider. No copiar este árbol sobre una instalación operativa. La parametrización y el empaquetado quedan fuera de alcance.

## Contenido y layout

- `companion/provider/hermes_ha_provider/`: seis módulos operativos; `managed_launcher.py`, `run_provider.py`, `ui_timing_runtime.py` y tres tests del companion en su raíz relativa original.
- `xiaozhi-ui-v3/ui_tts_timing_send.py`: helper externo real, separado como en el proyecto original.
- `cards/`: `backend.py`, `test_backend.py`, `backend.md` del coordinador bajo demanda; sin herramientas de OTA/aceptación.
- `plugin/`: base operativo seleccionado (`__init__`, adapter, tools, metadatos, README, LICENSE, pytest.ini y tests), más los cinco módulos de `hermes_bridge/`.
- `plugin/tests/{bridge,runtime,plugin_wiring}/`: únicamente `test_*.py` de ha2-notifications-0.3.0. Se conserva la relación `tests/<grupo>/../.. → raíz con hermes_bridge/`; no se copia el resto de N ni runners live. Se añaden a los tests de la base sin sobrescribirlos.
- `manifest.json`: SHA-256 origen/copia, procedencia y cambios; `test-results.json`: resultados reales de la última verificación; `verify_snapshot.py`: verificador aislado.

Las versiones se conservan: companion 0.1.0, plugin 2.0.1 y puente 0.2.0, con adaptación local documentada 0.3.0. No se han unificado artificialmente.

## Saneamiento, no refactorización

Sólo en las copias: IP privadas/LAN/CGNAT → `192.0.2.10`, raíz de usuario → `/path/to/user`, MAC del dispositivo → `00:00:00:00:00:00`; ID de propietario → ID ficticio `1000000`, entidades → ejemplos y zona doméstica → `Etc/UTC`. Los fixtures meteorológicos esperan ahora 17:00 UTC en lugar de la hora doméstica anterior. Fixtures negativos usan `198.51.100.20` y `02:00:00:00:00:01`, distintos de las identidades ficticias positivas para no anular las pruebas de rechazo. No se han quitado comparaciones, guards, allowlists, validación de URL/MAC/esquema, permisos, ACK booleano, correlación, restricción de perfil/home ni herencia TTS.

No se incluyen provider.env, .env, secretos YAML, credenciales, venvs, logs, recibos operativos, DB de la instalación, skill privada, audio ni resultados históricos. Las cadenas SECRET/TOKEN-PRIVATE de ciertos tests son estímulos sintéticos de redacción, no secretos extraídos. El informe de tests nuevo sólo contiene fixtures y diagnósticos saneados.

## Dependencias

Python **3.11+** (verificado con 3.11.15). Para las pruebas offline: `aiohttp>=3.9,<4`, `pytest` y `pytest-asyncio`. SQLite es de la biblioteca estándar. No se instala nada por este snapshot ni se aporta lock reproducible.

Operación conceptual del companion: Hermes core con su API nativa y runtime gestionado, aiohttp; herencia STT/TTS del perfil activo. Tarjetas/helper nativos: `aioesphomeapi` y PyYAML; el adaptador WS de tarjetas requiere además `websockets.sync.client`. Audio comprimido/timing mantiene `/usr/bin/afconvert` (macOS) y los límites de procesos. Los tests del plugin base y wiring que usan APIs del core necesitan un checkout compatible de Hermes; se verificaron contra revisión local documentada `bf0203a794a07aac3ff764972ab9087baa4e4f4e`, no contra un stub. `test_tts_inheritance.py` exige además la integración/dependencias Home Assistant y no se ejecuta en la batería offline.

## Arranque conceptual y límites de rutas

Flujo histórico: runtime gestionado de Hermes → `managed_launcher.py` → `run_provider.py` → CLI del companion + wrapper timing → API nativa de Hermes. El helper sólo entrega metadata UI; las tarjetas coordinan servicios HA y API nativa del dispositivo bajo demanda. El plugin carga el puente observador del ledger; Hermes sigue siendo el planificador y HA conserva políticas/entrega. Ingestión aceptada no equivale a reproducción física.

`companion/provider.env.example` documenta nombres reales de `Settings.from_env` con valores ficticios. **No basta renombrarlo para arrancar**: `run_provider.py` aún lee `/path/to/user/.hermes/.env` y `API_SERVER_KEY`, sobrescribe host/puerto/API/sesión/scratch, y entra directamente al CLI al importarlo. No importarlo para comprobar sintaxis. El launcher depende de `~/.hermes/hermes-agent/.hermes/bin/hermes --print-runtime-command`.

Las rutas absolutas saneadas se dejan como evidencia: el wrapper espera el helper bajo `/path/to/user/.hermes/projects/xiaozhi-ui-v3/`, no descubre automáticamente esta copia hermana; espera intérprete/scratch externos y el backend espera sus secretos e intérprete WS externos. El wiring mantiene la home exacta ficticia y perfil default. No cambiar estos guards para hacerlo arrancar. `test_ui_timing.py` completo también conserva rutas absolutas a scratch/helper; no se anuncia portable ni se ejecuta íntegramente. La prueba TTS depende de superficies HA no incluidas. Este archivo NO autoriza ejecutar entradas operativas ni crear secretos.

## Pruebas ejecutables sin HA ni servicios reales

Desde esta carpeta, con un Python de pruebas ya preparado:

```sh
python -I -B verify_snapshot.py
# Opcional: base + wiring con APIs del core, sin iniciar gateway/cron/provider:
python -I -B verify_snapshot.py --hermes-source /path/to/hermes-agent
```

El verificador compila todos los `.py` **en memoria**, usa HOME/HERMES_HOME/TMPDIR efímeros dentro del snapshot, entorno mínimo sin credenciales heredadas, bytecode y caché pytest deshabilitados. Ejecuta launcher (sólo constructor de comando), tarjetas con dobles, bridge, runtime con SQLite de fixtures/WS loopback efímero, y ocho pruebas puras de timing con sender inyectado. Con `--hermes-source` añade pytest de la base y de los tres grupos, incluido wiring. No ejecuta el main del launcher/provider/backend; no consulta HA ni DB/cron reales. Algunas pruebas importan APIs del core como dependencia, no simulan que ese core esté contenido aquí.

Última batería: launcher **1 PASS**, tarjetas **32 PASS**, bridge **15 PASS**, runtime **9 PASS**, timing puro **8 PASS**; pytest conjunto plugin **95 PASS, 1 SKIP y 11 subtests PASS**. Bridge/runtime se vuelven a recoger por pytest: **no sumar esos contadores como pruebas únicas**. El skip de la base y el detalle constan en el informe. No se ejecutan tests completos de timing/procesos/helper, TTS HA, runners operativos, aceptación física, firmware o frontend. Estas pruebas no demuestran instalación ni servicio activo.

## Licencias y procedencia

Ver `THIRD_PARTY.md`, `companion/LICENSE` (MIT Bailey Dixon 2026, revisión upstream exacta) y `plugin/LICENSE` (MIT Nous Research 2026). Se conservan modificaciones locales y sus límites. **MIT para las aportaciones originales de RUYMANIA**, autorizada el 5 de noviembre de 2026; véase `../LICENSE`. Las licencias y avisos upstream siguen vigentes. Las referencias de preparación inicial no constituyen un estado de publicación actual.
