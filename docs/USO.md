# Funciones y operación

Descripción del sistema documentado, no garantía de que cualquier copia del snapshot esté configurada.

## Ball

Menú circular: **Proyecto → Idioma → Tarjetas → Volumen → Reposo → Despertar → Modo noche → Info → Salir**. Acceso por pulsación estable aproximada de un segundo. La última sección ofrece Salir del Menú, Reiniciar y Test Animaciones; la presencia de botones no equivale a validación física de su ejecución.

Idioma de interfaz English/Español, sin cambiar STT/TTS ni contenido de tarjetas. Once GIF conservados; etiquetas internacionales START, MUTED, NO WIFI, NO HA. Reposo y despertares programados son ajustes separados de Modo noche. El primer toque corto con pantalla dormida despierta sin lanzar voz. Historial de cinco tarjetas en RAM; reiniciar lo vacía.

**[Ver la guía visual del menú con fotografías en español e inglés](MENU-VISUAL.md).** Mantén pulsada la pantalla aproximadamente **1 segundo** para abrirlo; las flechas permiten recorrer las secciones. Las fotografías ilustran la interfaz, no certifican la ejecución de cada función.

## Tarjetas por conversación o CLI

Peticiones de ejemplo: «Muestra este recordatorio en la Ball», «Muestra el tiempo», «Avisa y dilo en voz alta». Sin locución no significa silencio absoluto: puede sonar el aviso local aprobado de tres notas fuera de modo noche.

Ejemplo conceptual, tras configurar la copia local:

```sh
python backend.py show --kind notice --title Aviso --text 'Mensaje de ejemplo'
python backend.py show --kind notice --title Aviso --text 'Mensaje de ejemplo' --speak
python backend.py status
```

Usar el `--help` real de la versión configurada. Mostrar ahora no programa mañana. Cancelar exige leer y conservar el ID exacto; no sobrescribir una tarjeta ocupada. No ejecutar una espera de idle en primer plano dentro de la misma pregunta de voz: bloquearía el turno que mantiene ocupado el satélite.

Meteorología toma la entidad configurada, condición/unidades y hora del estado HA; esa hora no representa una medición instantánea. Si existe recorte real, informarlo; desplazamiento no garantiza que termine antes del TTL.

## Panel HA² Notifications

- Avisos HA: reglas temporales/semanales/estado/manual, cue o voz, revisión optimista y pausa.
- Tareas Hermes: decidir qué resultados recibir, con extractos/voz opt-in; no modificar el cron original.
- Proactivo BETA: opciones y disponibilidad, sin activar por guardar ni lanzar pruebas automáticamente.
- Actividad real: ingestión, cola, entrega y rechazo son estados distintos.

`enqueued` es entrada en cola, no entrega; `tts_end` sólo acredita URL lista, no reproducción. Para voz, exigir fin real de audio y confirmación humana cuando importe la audibilidad.

## Modo noche y audio

Conservar la escucha, conectividad y alarmas. Las tarjetas nocturnas mantienen texto/historial sin tres notas ni locución automática, sin cola de voz al amanecer. No extender ese silencio a una respuesta de conversación solicitada. Mantener un volumen único y arbitraje: no cancelar una conversación ni audio ajeno para mostrar un aviso.

## Pruebas físicas pendientes

Seguir la matriz de aceptación en ESTADO-Y-PRUEBAS. No repetir una locución ya aceptada sólo para demostrar de nuevo un ACK. Probar cada recorrido con autorización explícita y registrar su alcance, sin generalizar una aceptación a todo el sistema.
