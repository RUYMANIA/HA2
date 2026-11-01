# Arquitectura y contratos

## Superficies y responsabilidad

```text
Usuario / voz / interfaz táctil
           │
     XiaoZhi Ball V2 (ESPHome)
           │ API cifrada + Assist + audio
     Home Assistant
       ├─ Assist / STT / TTS / satélite
       ├─ adaptador de conversación Hermes ── companion autenticado ── Hermes Agent
       └─ HA² Notifications
          ├─ catálogo, horarios, cola e historial privados
          ├─ panel JS nativo y API WS/acción administrativa
          ├─ transporte de tarjetas / conversación nativa
          └─ ingestión de resultados de tareas ← puente observador de Hermes
```

No se copia el core completo de Hermes o Home Assistant. El companion, el adaptador HA `hermes_agent` y el plugin Hermes `homeassistant` son componentes distintos. Los dos proyectos upstream denominados `hermes-homeassistant` tienen autores y superficies diferentes.

## Wake word local

**Okey Hermes** se ejecuta mediante microWakeWord en la Ball; el entrenador no es dependencia de ejecución. Modelo entrenado en español y uso físico confirmado por RUYMANIA hablando en español e inglés. Es distinto de Hey Hermes. La detección de la frase, el idioma de interfaz y STT/TTS de la conversación son capas separadas. Véase [integración y aceptación](OKEY-HERMES.md).

## Conversación

La Ball usa la pipeline Assist seleccionada; el adaptador HA llama al companion autenticado y este utiliza el Hermes real. STT/TTS, texto y metadatos de duración son capas distintas. El helper de metadata completa los datos privados necesarios para scroll sin convertir prompts internos en transcripciones públicas ni ampliar sensores con conversaciones completas.

La voz hereda la configuración correspondiente; no se fija una voz alternativa para salvar fallos. La ruta de metadata/audio contiene dependencias macOS y helpers externos: conservar Python no la convierte en un servicio multiplataforma ya empaquetado.

## Tarjetas

Categorías: `reminder`, `weather`, `result`, `notice`. El coordinador de tarjetas es un CLI bajo demanda, **no un LLM ni un planificador**. `show` presenta ahora; no crea por sí solo un recordatorio futuro.

Contrato del dispositivo: `card_show`, `card_play`, `card_cancel`, con identidad exacta, generación y TTL. Respuestas de aceptación/transporte se distinguen de visibilidad lógica y de reproducción completada. La oscuridad nocturna puede mantener visibilidad lógica sin iluminar la pantalla.

Historial local: cinco tarjetas en RAM, nueva primero, sin persistir mensajes. Consultar/repintar historial no genera ID, TTL, audio ni aviso nuevos. Cerrar una tarjeta no cancela audio ajeno. El modo noche tiene prioridad sobre encendidos y locuciones automáticos de tarjetas, sin apagar red, escucha ni respuestas solicitadas.

## Avisos programados y resultados de tareas

**Home Assistant es la autoridad única de reglas y coordinación de entrega.** El catálogo/cola/historial están en Store privado; no se distribuyen como configuración de ejemplo. Hermes puede gestionar reglas mediante conversación, pero no mantiene un calendario paralelo de las mismas ocurrencias.

Hermes conserva su cron. El puente observa jobs/ledger y envía identidades de ejecución correlacionadas; no se inventa un hook universal de fin de tarea. `job_id` debe viajar en el nivel superior, los ACK deben ser booleanos y el guard de versión es un allowlist explícito. `accepted` no significa reproducido. La recepción y los extractos son opt-in; el panel no pausa ni edita el cron de Hermes.

## Proactivo aprobado

Invitaciones efímeras separadas del historial de tarjetas. Ruta vigente: **locución → escucha nativa → respuesta con contexto de la invitación**; no se promete una sesión desconectada como equivalente ni una ventana especial de 30 segundos. No se requiere el candidato experimental de firmware 1.4.0.

Disponibilidad y activación son puertas separadas. Guardas de versión/fingerprint de HA/ESPHome, noche, ocupación y capacidad de bootstrap fallan cerrado. Una prueba manual no acredita por sí sola una oportunidad automática. Los cierres posteriores de 27–29 de octubre registran Proactivo ACTIVO y la aprobación expresa de RUYMANIA; no restaurar el OFF histórico. Las invitaciones automáticas se limitan a una frase completa, una línea, 120 caracteres, 20 palabras y 240 bytes UTF-8; si incumplen se rechazan sin truncar ni repetir inferencia. Esta regla no afecta a la conversación normal.

## Panel

Módulo JavaScript servido por HA, sin servidor frontend adicional. Orden: avisos HA → tareas Hermes → Proactivo. Proactivo ya no muestra BETA por aprobación expresa; Nuevo evento doméstico y su editor conservan su etiqueta experimental. Acordeones cerrados y mutuamente exclusivos; **Log de Actividad / Activity Log** aparte al final. El registro unifica avisos HA, tareas Hermes y Proactivo en el mismo Store, con hasta 200 eventos compartidos, origen/tipo/nombre/fecha-hora HA y resultado. No almacena cuerpos, transcripciones ni secretos; metadatos legacy desconocidos no se inventan. La versión visible procede de `snapshot.version` (backend), no de un literal ni del firmware. Las llamadas reutilizan la sesión HA, sin secretos en el navegador.
