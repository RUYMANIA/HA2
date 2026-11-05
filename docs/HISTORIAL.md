# Historial y decisiones preservadas

Este documento resume hitos; no sustituye los recibos privados ni presume una historia Git completa del desarrollo anterior.

- Base Ball V2 sobre RealDeco y conversación Assist/Hermes; se mantiene separación entre firmware, HA y companion.
- Avatar local de once estados y menú de volumen/sistema. Desarrollo posterior de tarjetas con TTL, identidad, protección de audio y pruebas host/API.
- 19 de octubre de 2026: cierre histórico de tarjetas y avisos temporales; distinguir aceptación por telemetría de legibilidad/audibilidad física.
- HA² 1.2.0: audio de arranque Cori/mezcla v2 y tres notas locales de aviso; recursos conservados en revisiones posteriores.
- Evolución de idioma, cinco tarjetas RAM, reposo/despertar y prioridad de modo noche; se preservan selecciones y no se añaden servidores para suplir el firmware.
- HA² Notifications evoluciona 0.1.x → 0.2.0 → 0.3.0; versiones UI y backend no se confunden con firmware.
- 25 de octubre de 2026: cierre de panel/Proactivo 0.3.0, ruta nativa de conversación y aceptación auditiva manual. Automático seguía OFF; no se elimina BETA por una prueba manual.
- 25 de octubre de 2026: firmware 1.3.1 con menú final Salir/Reiniciar/Test Animaciones instalado según cierre posterior a staging. Validación física nueva pendiente.
- 26 de octubre de 2026: RUYMANIA autoriza repositorio privado `RUYMANIA/HA2`, README español/inglés y documentación técnica española. Se crea un archivo saneado separado de operación; no se elige licencia pública global ni se abre el repositorio.

- 27 de octubre de 2026: Log de Actividad unificado para HA, tareas Hermes y Proactivo; retención de 200 eventos. Proactivo ACTIVO y aprobado por RUYMANIA, retirada de BETA sólo en esa sección. Nuevo evento doméstico mantiene BETA.
- 29 de octubre de 2026: firmware 1.3.2 instalado con el modelo local **Okey Hermes**, añadido sin sustituir modelos/IDs previos. Prueba física inicial aceptada y detección corroborada por HA.
- 29 de octubre de 2026: instaladas las restricciones de invitaciones proactivas breves, sin cambiar conversaciones normales ni el detector.
- 1 de noviembre de 2026: RUYMANIA confirma que **Okey Hermes funciona hablando en español e inglés**. Se sincronizan en GitHub modelo, manifiesto, fuentes y documentación; se mantiene el idioma de entrenamiento `es` y el archivo privado. No se repiten pruebas de voz ni despliegues.

- 2 de noviembre de 2026: incidencia de START persistente y menú no accesible. Se detectó una IP desactualizada en ESPHome y se recuperó la conexión reconfigurando la entrada existente, sin otro reinicio ni OTA. La comprobación física de LCD/táctil quedó separada del readback técnico. Se documenta recuperación y reserva DHCP recomendada, todavía no aplicada en ese cierre; el motivo de que no se actualizase automáticamente la IP sigue sin determinar.

- 3 de noviembre de 2026: RUYMANIA confirma reserva DHCP existente. El error posterior tras detectar Okey Hermes se identifica como `stt-provider-missing`; se recuperan Whisper y puente Hermes y se recargan sólo las entradas afectadas, manteniendo desactivado el autoinicio y sin reiniciar HA/Ball. La conversación física nueva posterior no queda acreditada.
- 5 de noviembre de 2026: RUYMANIA autoriza abrir el repositorio con MIT para el código propio y condiciones separadas para Okey Hermes. Los pesos permanecen incluidos, **fuera de MIT y sin licencia abierta alternativa ni permiso comercial concedidos**. Se documentan procedencia, exclusiones e incertidumbres, sin asignar automáticamente al detector la licencia del corpus; no se reescribe el historial ni se cambian los equipos operativos.

Decisiones: una única autoridad HA para avisos; Hermes conserva su cron; herencia de voz y modelo sin fijaciones adicionales; no activar nuevas reglas por defecto; no publicar configuración, sesiones o binarios privados. La expansión histórica «Assitant» se conserva dentro de las fuentes; título editorial solicitado «Assistant».
