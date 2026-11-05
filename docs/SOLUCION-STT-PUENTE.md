# Error tras Okey Hermes: STT y puente Hermes

[Volver al README](../README.md) · [Incidencia distinta: START/IP](SOLUCION-START-IP.md) · [Estado y pruebas](ESTADO-Y-PRUEBAS.md)

## Incidencia documentada — 3 de noviembre de 2026

Después de reconocer **Okey Hermes**, la Ball mostraba el GIF de error. Las trazas de Assist fallaban con **`stt-provider-missing` antes de transcribir**, sin llegar al agente ni a TTS. Esto no identifica un fallo del detector, ni es el mismo incidente que una IP antigua en ESPHome. El usuario ya había confirmado la reserva DHCP de la Ball en el router.

Se comprobaron dos servicios auxiliares detenidos:

- El contenedor **Whisper** existente, sin evidencia suficiente para establecer la causa de la parada. El dato disponible no indicaba OOM; no se inventa una causa.
- El **proveedor/puente Hermes**: registrado en launchd, pero sin proceso ni listener. La API principal de Hermes sí estaba saludable; la salud del core no demuestra la del puente.

En Home Assistant, las entradas Wyoming/Whisper y Hermes estaban en `setup_retry`; sus entidades de STT, conversación y TTS aparecían `unavailable`.

## Recuperación realizada y alcance

Con autorización específica del propietario se arrancaron **los servicios existentes**, sin reinstalarlos ni cambiar modelos, voz, parámetros o configuración del detector. Se verificó conectividad desde el host y desde el entorno de HA. Como las entradas seguían en reintento, se recargaron únicamente las dos entradas afectadas; la respuesta indicó que no era necesario reiniciar Home Assistant.

**Readback del 3 de noviembre de 2026, 11:04 UTC:**

- Whisper en ejecución y saludable; health del proveedor Hermes correcto.
- Ambas entradas HA en `loaded`; las entidades dejaron de estar `unavailable`.
- STT `unknown` antes de una nueva transcripción es compatible con disponibilidad; no demuestra un turno nuevo.
- Satélite en reposo y Okey Hermes seleccionado, mismo firmware 1.3.2.
- Marcas antiguas de último uso en conversación/TTS no se cuentan como nueva prueba.

No se reiniciaron HA ni la Ball; no hubo OTA, cambios de IP/modelo/detector/voz ni locución o captura de prueba por parte de Hermes. Las identidades, direcciones, secretos, transcripciones y recibos privados se excluyen de esta guía.

## Política de arranque conservada

El contenedor mantiene **`restart=no`**. El proveedor mantiene **`RunAtLoad=false` y `KeepAlive=false`**. Se respetó la decisión de no activar arranque/recuperación automática. Si vuelven a pararse, estas políticas no los recuperarán por sí solas. No cambiar esa política como efecto colateral de diagnosticar una conversación.

## Si ocurre de nuevo

1. Identifica la fase real del error: conectividad ESPHome, STT, agente o TTS. No cambies el detector sólo porque después de la palabra clave aparezca un error.
2. Comprueba por separado la salud del STT, del proveedor/puente y del core de Hermes. La mera existencia de un contenedor o un registro launchd no prueba que estén ejecutándose.
3. Contrasta la conectividad también desde HA, no sólo desde el Mac.
4. Recupera únicamente los servicios existentes y autorizados. No adoptes comandos de otra instalación ni sustituyas modelos/voz como atajo.
5. Si HA sigue en `setup_retry`, valora la recarga exclusiva de las entradas afectadas; conserva sus identidades y comprueba el resultado. No borres integraciones ni reinicies todo el sistema por defecto.
6. Verifica estados recientes y una conversación nueva **sólo cuando esté autorizada**. No publiques transcripciones o tokens en un issue.

## Pendiente físico real

**No consta una conversación física nueva completada después de esta recuperación**: queda por confirmar respuesta audible sin GIF de error. Esto no reabre ni invalida la aceptación bilingüe de Okey Hermes del 1 de noviembre. La apertura del repositorio el 5 de noviembre sólo actualiza documentación; no arranca servicios ni ejecuta esta prueba, y no afirma que el estado del día 3 siga siendo el estado vivo actual.
