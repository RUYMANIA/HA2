# Pendientes y puertas antes de distribución pública

## Funcionales

- Aceptación específica de los controles de mantenimiento y demo completa que no esté documentada; las fotos del menú no prueban que se hayan ejecutado. La versión actual documentada del firmware es 1.3.2.
- Proactivo ya está aprobado y figura ACTIVO en cierres posteriores: no mantener su activación como pendiente. Conservar separada la observación de una oportunidad natural/enriquecida que no esté acreditada; no provocarla para actualizar GitHub.
- Okey Hermes: integración y prueba física inicial aceptadas; uso en español e inglés confirmado el 1 de noviembre de 2026. No dejar su activación o prueba inicial pendientes. Las métricas acústicas prolongadas no medidas no son un bloqueo obligatorio nuevo.
- Pruebas de recorridos completos de avisos/tareas, modo noche y lectura/TTL con versiones exactas.
- Medición de heap/underruns en hardware si se quiere afirmar comportamiento de memoria/audio; flash libre no demuestra RAM libre.

## Red y arranque

- Incidencia de 2-11-2026: conexión recuperada al corregir el host de la entrada ESPHome. No confundir con una confirmación física de salida de START/menú si ésta no está documentada.
- Reserva DHCP recomendada para dirección estable: no estaba aplicada en el cierre y esta publicación no configura el router. Investigar por separado el descubrimiento automático que no actualizó la dirección; no asumir que cualquier cambio de IP falla. [Procedimiento de recuperación](SOLUCION-START-IP.md).

## Distribución

- Transformar los snapshots con rutas sustituidas en paquetes configurables sin debilitar allowlists, guards, identidad ni permisos.
- Unificar metadatos de instalación y dependencias; crear pruebas HA en contenedor independiente, nunca en producción.
- Completar suite portable de C++/lambdas y fixtures sin baselines privados. El archivo preserva pruebas, no promete que todas funcionen desde cualquier ruta.
- Resolver entidad de idioma fija del panel frente al prefijo configurable antes de anunciar soporte genérico.
- Evaluar versiones HA nuevas con fingerprints/contratos y pruebas; no retirar guardas para aceptar cualquier versión.
- Preparar firmware construido con ejemplos/secretos nuevos sólo tras configuración y compilación; no publicar OTA original.

## Editorial y derechos

- Decidir licencia del código propio con RUYMANIA.
- Consolidar derechos de logo/GIF, QR, voz y mezcla musical antes de apertura pública.
- Revisar dependencias descargadas (fuentes, sonidos y modelos stock) si se redistribuyen; conservar separada la política de derechos del modelo propio Okey Hermes sin aplicarle la MIT del modelo Hey Hermes.
- Aprobar documentación y después traducir al inglés la parte técnica.
- Decidir si corregir «Assitant» en una **nueva** revisión funcional; no modificar retrospectivamente fuentes instaladas como parte de documentación.

## Seguridad y publicación

Revisión completa de secretos/datos e historial, pruebas en copia, manifiestos verificables y confirmación explícita antes de cambiar visibilidad. El carácter privado es una decisión vigente, no una fase con fecha automática de apertura.
