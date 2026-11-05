# Pendientes técnicos y mantenimiento

## Funcionales

- Aceptación específica de los controles de mantenimiento y demo completa que no esté documentada; las fotos del menú no prueban que se hayan ejecutado. La versión actual documentada del firmware es 1.3.2.
- Proactivo ya está aprobado y figura ACTIVO en cierres posteriores: no mantener su activación como pendiente. Conservar separada la observación de una oportunidad natural/enriquecida que no esté acreditada; no provocarla para actualizar GitHub.
- Okey Hermes: integración y prueba física inicial aceptadas; uso en español e inglés confirmado el 1 de noviembre de 2026. No dejar su activación o prueba inicial pendientes. Las métricas acústicas prolongadas no medidas no son un bloqueo obligatorio nuevo.
- Pruebas de recorridos completos de avisos/tareas, modo noche y lectura/TTL con versiones exactas.
- Medición de heap/underruns en hardware si se quiere afirmar comportamiento de memoria/audio; flash libre no demuestra RAM libre.

## Red y arranque

- Incidencia de 2-11-2026: conexión recuperada al corregir el host de la entrada ESPHome. No confundir con una confirmación física de salida de START/menú si ésta no está documentada.
- Reserva DHCP **confirmada por RUYMANIA el 3-11-2026**. No se mantiene su creación como pendiente ni se afirma una inspección nueva del router. Investigar por separado el descubrimiento automático que no actualizó la dirección; no asumir que cualquier cambio de IP falla. [Procedimiento de recuperación](SOLUCION-START-IP.md).
- Error `stt-provider-missing` del 3-11: servicios Whisper/puente recuperados y entradas HA recargadas. **Pendiente conversación física nueva posterior**, sin reabrir la aceptación del detector. Arranque/recuperación automática siguen desactivados por decisión del usuario, no son una tarea autorizada pendiente. [Diagnóstico separado](SOLUCION-STT-PUENTE.md).

## Distribución

- Transformar los snapshots con rutas sustituidas en paquetes configurables sin debilitar allowlists, guards, identidad ni permisos.
- Unificar metadatos de instalación y dependencias; crear pruebas HA en contenedor independiente, nunca en producción.
- Completar suite portable de C++/lambdas y fixtures sin baselines privados. El archivo preserva pruebas, no promete que todas funcionen desde cualquier ruta.
- Resolver entidad de idioma fija del panel frente al prefijo configurable antes de anunciar soporte genérico.
- Evaluar versiones HA nuevas con fingerprints/contratos y pruebas; no retirar guardas para aceptar cualquier versión.
- Preparar firmware construido con ejemplos/secretos nuevos sólo tras configuración y compilación; no publicar OTA original.

## Editorial y derechos

- Licencia propia decidida por RUYMANIA el 5 de noviembre de 2026: **MIT**, con avisos de terceros conservados. La licencia no convierte el snapshot en una distribución instalable validada.
- Logo/GIF identificados con base Nous Research y aviso MIT conservado; Cori/Bryce Beattie, QR y composición procedural documentados en [procedencia](../THIRD_PARTY.md). No conceder derechos de marca ni atribuir a RUYMANIA las bases de terceros.
- **Okey Hermes incluido fuera de MIT, sin licencia abierta alternativa ni permiso comercial concedidos.** Completar trazabilidad/derechos de entrenamiento antes de conceder permisos más amplios sobre sus pesos; no deducir una licencia automáticamente del corpus. [Aviso del modelo](../firmware/models/okey-hermes/LICENSE.md).
- Revisar dependencias descargadas (fuentes, sonidos y modelos stock) si se redistribuyen; no están vendorizadas como una distribución completa.
- Aprobar documentación y después traducir al inglés la parte técnica.
- Decidir si corregir «Assitant» en una **nueva** revisión funcional; no modificar retrospectivamente fuentes instaladas como parte de documentación.

## Seguridad y publicación

Mantener revisión de secretos/datos e historial, pruebas en copia y manifiestos verificables antes de cada publicación. RUYMANIA ha autorizado expresamente la apertura pública y MIT el 5 de noviembre de 2026; no publicar configuración doméstica ni presentar las pruebas pendientes como completadas.
