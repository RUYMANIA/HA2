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

## Proactivo BETA

Invitaciones efímeras separadas del historial de tarjetas. Ruta vigente: **locución → escucha nativa → respuesta con contexto de la invitación**; no se promete una sesión desconectada como equivalente ni una ventana especial de 30 segundos. No se requiere el candidato experimental de firmware 1.4.0.

Disponibilidad y activación son puertas separadas. Guardas de versión/fingerprint de HA/ESPHome, noche, ocupación y capacidad de bootstrap fallan cerrado. Una prueba manual no valida la primera oportunidad automática. La última evidencia local registra automático desactivado.

## Panel

Módulo JavaScript servido por HA, sin servidor frontend adicional. Orden: avisos HA → tareas Hermes → Proactivo BETA. Acordeones cerrados y mutuamente exclusivos; actividad real aparte al final. La versión visible procede de `snapshot.version` (backend), no de un literal ni del firmware. Las llamadas reutilizan la sesión HA, sin secretos en el navegador.
