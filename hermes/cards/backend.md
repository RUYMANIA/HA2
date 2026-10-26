# Coordinador bajo demanda de tarjetas Xiaozhi

## Estado

`backend.py` implementa un CLI por invocación, sin servidor, daemon, cron, suscripción de audio de Voice Assistant ni cambios en Home Assistant. `test_backend.py` contiene 31 pruebas host-only con inyección de transporte y reloj; no invocan hardware ni APIs externas.

## Contrato público

- `card_show(request_id:string,title:string,body:string,kind:string,ttl_ms:int,audio_expected:bool)`
- `card_play(request_id:string,url:string)`
- `card_cancel(request_id:string)`
- Estado JSON: `request_id`, `state`, `visible`, `audio`, `reason`, `generation`, `truncated`.
- Estados: `idle`, `pending`, `shown`, `playing`, `audio_done`, `dismissed`, `expired`, `interrupted`, `rejected`.
- IDs UUID hex32; TTL 2–120 s (por defecto 30). El TTL es deadline de extremo a extremo en el host y también TTL local del firmware.
- Éxito hablado solo con mismo ID, `state=audio_done` y `audio=done` antes del deadline. No se acepta `tts_end` ni URI lista como reproducción audible.
- `card_play` usa `va.on_announce` con texto marcador `__hermes_card__<uuid>`, sin `start_conversation`, sin `preannounce_media_id` y sin GET previo del proxy.

## Duración, cierre y llamadas desde el asistente

- Tras completar la locución, la tarjeta permanece hasta el TTL local, salvo cierre o interrupción. Retirar la tarjeta no fuerza STOP del altavoz compartido: la voz termina naturalmente.
- Una tarjeta existente no se sobrescribe ciegamente desde el CLI; devuelve `card_busy`. Solo cancelar por el ID leído si el usuario solicita sustituir o retirar ese aviso.
- El TTL del coordinador es un límite de extremo a extremo (incluye espera y preparación); el firmware recibe el tiempo restante. No garantiza treinta segundos de lectura si el dispositivo estaba ocupado.
- Desde una petición de voz en la propia Ball, no bloquear el turno esperando idle: ese turno mantiene VA ocupado. Iniciar el CLI de forma asíncrona y acotada, y verificar su JSON al terminar; o usar el planificador existente si se solicita un aviso futuro. No afirmar entrega por el mero inicio del proceso.
- Crear un `show --kind reminder` no programa nada para el futuro; los recordatorios con fecha necesitan el cron existente.

## Comandos

Usar el intérprete ESPHome ya instalado, sin instalar dependencias:

```bash
/path/to/user/.hermes/tools/xiaozhi-esphome/venv/bin/python -I backend.py \
  show --kind reminder --title 'Café' --text 'Estará listo en 20 minutos' --seconds 30

/path/to/user/.hermes/tools/xiaozhi-esphome/venv/bin/python -I backend.py \
  show --kind result --title 'Resultado' --text 'Resultado aportado' --speak

/path/to/user/.hermes/tools/xiaozhi-esphome/venv/bin/python -I backend.py \
  weather --title 'El tiempo' --speak

/path/to/user/.hermes/tools/xiaozhi-esphome/venv/bin/python -I backend.py \
  cancel --request-id <uuid-hex32>

/path/to/user/.hermes/tools/xiaozhi-esphome/venv/bin/python -I backend.py status
```

`weather` lee `weather.example` y presenta hasta cinco líneas: condición en español, temperatura, humedad, viento y hora del estado de HA en Etc/UTC. Solo incluye atributos presentes con sus unidades reales; usa coma decimal y etiqueta «Datos HA» sin fingir una medición en tiempo real. `show` no crea recordatorios persistentes ni modifica planificación existente. `result` muestra el texto aportado sin invocar un LLM.

Opciones: `--kind reminder|weather|result|notice`, `--seconds 2..120`, `--speak`, `--idle-wait 0..60`, `--playback-timeout 0..120`, `--host`, `--lock-timeout`.

Salida: un único objeto JSON UTF-8 con ID, estado visible/audio, motivo y generación. No imprime URL/token/path privado ni credenciales. Códigos separables: `0` éxito; `2` entrada/URL insegura; `3` busy/lock; `4` interrupted/conflicto/dismissed; `5` expired/playback timeout; `6` rejected; `1` transporte/TTS genérico.

## Verificación host-only

```bash
cd /path/to/user/.hermes/projects/xiaozhi-cards
python3 -m unittest test_backend -q
/path/to/user/.hermes/tools/xiaozhi-esphome/venv/bin/python -I -m unittest discover -s . -p test_backend.py -q
```

Las pruebas cubren validación UTF-8/título/TTL, pipeline seleccionada por nombre y fallback preferred, opciones WAV 48 kHz mono 16-bit, voz `None` heredada, path rebase solo a LAN validada, clima real, esquema exacto de acciones, colisiones de claves entre dominios, MAC, busy/lock, ack por ID/generación, conflicto de productor, callback tardío, timeout de adaptador, expiración antes de escribir, cancelación compare-ID, estado final honesto, cleanup no bloqueante y señales.

## Integración real

- Credenciales HA se leen únicamente de `~/.hermes/.env`; token solo en memoria y nunca en salida/logs.
- API REST usa `urllib` estándar; el WS privado `assist_pipeline/pipeline/list` usa el Python backup ya instalado a través de stdin privado. No se añade `websockets` al venv ESPHome.
- Pipeline se resuelve con `select.example_satellite_assistant` y `assist_pipeline/pipeline/list`; si el selector es `preferred` o desconocido, usa preferred global. No selecciona preferred global cuando el selector tiene nombre.
- TTS usa `POST /api/tts_get_url` con `engine_id`, `message`, `cache`, `language` y opciones comunes. Generación lazy; no ejecuta pipeline ni cancela conversación de usuario.
- Origen HA permitido: `http://192.0.2.10:8123` (también loopback para ejecución local). Path debe ser `/api/tts_proxy/<token>` y se reescribe solo al host LAN validado.
- ESPHome: verifica MAC `00:00:00:00:00:00`, acciones y tipos exactos, y sensores `card_status`/`card_active`. Suscribe estados nativos, no audio VA. Lee idle desde `assist_satellite.example_satellite_assist_satellite` y `media_player.example_satellite`; nunca llama announce/stop ni `assist_satellite.announce`.
- El firmware objetivo contiene `temporary_cards.h` y `config/temporary_cards.yaml` con TTL, compare-ID, marcador exacto `on_tts_start`, `tts_end` solo URI, watchdog y publicación JSON. Su instalación se acredita por lectura del build real y `firmware-verification.json`, no por esta guía. Este coordinador no edita firmware.

## Dependencias y verificación de fuentes

Las pruebas unitarias no realizan red ni escrituras externas; las pruebas del dispositivo se registran por separado. Fuentes primarias consultadas: HA instalado en `/usr/src/homeassistant/homeassistant/components/tts/__init__.py` y `assist_pipeline`; `aioesphomeapi` instalado; firmware actual en `../xiaozhi-ball-esphome`. Verificación previa: `ha-before.json`, `ha-capabilities-before.json`, `tts-negotiation.json` y WAV real PCM 48000/1/2.
