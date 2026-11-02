# Ball detenida en START después de reiniciar o cambiar de IP

[Volver al README](../README.md) · [Guía visual del menú](MENU-VISUAL.md) · [Instalación](INSTALACION.md)

> **Primero comprueba la dirección y la conexión ESPHome.** Si START continúa animándose y la pulsación de aproximadamente un segundo no abre el menú, puedes recuperar la conexión desde Home Assistant sin utilizar la pantalla de la Ball. No empieces por borrar el dispositivo, restaurar de fábrica o reinstalar firmware.

## Síntomas

- La pantalla permanece en **START** con el GIF repitiéndose, sin avanzar a la interfaz habitual.
- Mantener pulsada la pantalla aproximadamente **1 segundo** no permite acceder al menú.
- Home Assistant puede mostrar el satélite y sensores ESPHome como **No disponible / unavailable** aunque el propio Home Assistant esté funcionando.
- El problema puede coincidir con un reinicio y una dirección nueva asignada por la red.

**El GIF en movimiento no demuestra que todo el sistema funcione, pero tampoco demuestra un bloqueo total del microcontrolador.** No todos los casos de START tienen la misma causa.

## Incidencia documentada — 2 de noviembre de 2026

En la instalación de referencia con firmware **HA² 1.3.2** se comprobó lo siguiente:

1. Home Assistant conservaba una **dirección anterior** de la Ball y no podía conectar con ella.
2. El nombre mDNS `xiaozhi-ball-v2.local` resolvía a **otra dirección**.
3. En la nueva dirección, la **API cifrada** respondía y su identidad coincidía con la Ball esperada. Versión/build y uptime eran legibles: el dispositivo seguía ejecutándose.
4. Se corrigió el host mediante el **flujo nativo de configuración de ESPHome**, conservando la entrada, la identidad y los dispositivos/entidades existentes.
5. La lectura posterior confirmó la dirección actualizada, la disponibilidad del satélite, estados en reposo y el diagnóstico de saludo de arranque finalizado. Okey Hermes y el firmware se conservaron.

La recuperación de conexión **no requirió otro reinicio de la Ball ni de Home Assistant**, ni OTA, cambio de detector, modificación de voz o restauración de fábrica. No se lanzó una locución de prueba; el saludo normal se completó al recuperarse la conexión.

**Límite de la evidencia:** se recuperó y verificó la conexión. El cierre técnico disponible dejó pendiente la comprobación física de que desaparecía START y volvía a abrirse el menú. No se presenta la telemetría como una confirmación del LCD/táctil. Tampoco se ha demostrado por qué no se actualizó automáticamente la dirección ni por qué cambió la concesión del router. No afirmar que cada cambio de IP vaya a provocar necesariamente START.

Las IP reales, MAC, claves, identificadores de entrada y recibos privados del incidente no se incluyen en esta guía.

## Recuperación paso a paso, sin acceder al menú de la Ball

### 1. Comprueba Home Assistant y la entrada ESPHome

Abre **Ajustes → Dispositivos y servicios → ESPHome** y localiza la entrada existente de la Ball. Comprueba si sus entidades están disponibles y qué dirección utiliza la integración. Si Home Assistant completo no responde, diagnostica primero ese servicio; una reserva de IP de la Ball no lo reparará.

No confundas la integración **ESPHome** con **HA² Notifications**, el adaptador de conversación Hermes o ESPHome Device Builder. La conexión al dispositivo pertenece a la entrada ESPHome.

### 2. Averigua la dirección actual y confirma la identidad

Consulta la lista de clientes/concesiones DHCP del router y contrasta la **MAC Wi-Fi de tu propia Ball**. Como vía complementaria, resuelve su nombre mDNS desde la misma red; para el nombre de este proyecto, en macOS:

```sh
dns-sd -G v4 xiaozhi-ball-v2.local
```

Este comando observa la resolución y puede permanecer abierto; sal con **Ctrl+C**. Si has cambiado el nombre del nodo, utiliza el tuyo. Ejecutarlo en el Mac no demuestra que mDNS funcione también desde el host o contenedor de Home Assistant.

- **No adoptes una IP sólo porque responde a ping.** Contrasta primero la identidad del cliente en el router y, en la conexión ESPHome autenticada, la identidad del dispositivo. No envíes una clave a una dirección de un equipo desconocido.
- Si el router y mDNS discrepan, revisa que no haya nombres duplicados o respuestas antiguas antes de cambiar nada.
- mDNS/multicast puede no atravesar redes de invitados, VLAN o contenedores. Que no resuelva `.local` no prueba que la Ball esté apagada.
- La API ESPHome usa normalmente el puerto **6053**. Un puerto abierto por sí solo no valida identidad ni autenticación.

### 3. Reconfigura la entrada existente con la dirección correcta

En la **entrada ESPHome de la Ball**, abre el menú de la entrada y elige **Reconfigurar / Reconfigure**. La ubicación o el rótulo puede variar con la versión de Home Assistant.

1. Introduce la **dirección actual comprobada** y conserva el puerto correcto.
2. Si el flujo pide la **clave de cifrado API**, utiliza de forma privada la que ya corresponde a esa Ball. No es la contraseña Wi-Fi ni la contraseña OTA. No la publiques ni la pegues en un issue o captura.
3. Completa el flujo y comprueba que se conserva el dispositivo existente.

**No borres la integración, no añadas una segunda Ball y no edites `.storage` manualmente.** Si aparece un conflicto de identidad o una propuesta para sobrescribir/migrar otro dispositivo, detente y revisa la MAC: actualizar la IP del mismo equipo no debería convertirse en sustituir hardware desconocido.

Para automatizaciones de mantenimiento: en el incidente, el flujo devolvió `type=abort, reason=already_configured_updates` **después de actualizar la entrada existente**. Un verificador que esperaba otro resultado lanzó un error aunque el cambio ya estaba aplicado. No interpretes cualquier `abort` como éxito: lee después el host persistido, la identidad y la disponibilidad. No repitas la escritura sólo por un error del verificador.

### 4. Verifica conexión y funcionamiento por separado

- Confirma que la entrada utiliza la dirección nueva y sigue siendo la misma Ball, sin duplicados.
- Comprueba que satélite/sensores dejan de estar `unavailable` y que su estado es reciente; un texto auxiliar antiguo que diga «desconectado» puede no haberse vuelto a publicar todavía.
- Espera a que termine el arranque/saludo normal, sin enviar anuncios de prueba ni interrumpir audio.
- **Mira la pantalla:** ¿ha desaparecido START?
- **Mantén pulsado aproximadamente 1 segundo:** ¿se abre Proyecto y se puede navegar por el menú?

La recuperación sólo se da por completa para LCD/táctil cuando se comprueban los dos últimos puntos. Si HA vuelve a conectar pero START o el menú siguen fallando, continúa con el diagnóstico de la sección siguiente; no declares que la IP explica todo el síntoma visual.

### 5. Revisa clientes auxiliares que guardasen la dirección antigua

Los scripts o herramientas locales con IP literal también pueden apuntar a una dirección obsoleta. Actualiza su configuración operativa por su procedimiento correspondiente y verifica la identidad. Cuando la versión del CLI de tarjetas lo permita, `--host` cambia el destino de la **Ball** para esa invocación; no cambia el origen de Home Assistant/TTS ni configura una reserva DHCP. No ejecutes herramientas del snapshot saneado como si ya contuviesen tus credenciales y rutas reales.

## Prevención recomendada: reserva DHCP en el router

**Sí: para esta instalación se recomienda una dirección estable para la Ball, preferiblemente mediante una reserva DHCP del router asociada a su MAC Wi-Fi.** Es una recomendación preventiva del proyecto para reducir el riesgo observado, no una garantía de eliminar cualquier fallo de arranque.

Una reserva DHCP permite mantener el firmware usando DHCP y administrar en el router qué dirección se asigna a ese dispositivo. No requiere compilar o flashear la Ball y evita introducir otra configuración de red fija dentro del firmware.

1. Identifica inequívocamente la Ball en la lista de clientes del router.
2. Crea una **reserva de dirección / DHCP reservation / static lease** para su MAC Wi-Fi.
3. Elige una dirección válida y sin conflictos según las reglas de ese router. Reservar la dirección actual comprobada suele reducir los cambios necesarios. No copies direcciones de documentación ni reutilices la de otro equipo.
4. Guarda y lee de nuevo la reserva. Si el cambio requiere renovar la concesión o reconectar, hazlo de forma controlada y con el equipo desocupado; no reinicies el router ni desconectes a otros clientes como atajo.
5. Alinea la entrada ESPHome y los clientes auxiliares con la dirección reservada y vuelve a comprobar conectividad/identidad.

**En el cierre del incidente no se había configurado esta reserva. Esta publicación sólo la recomienda: no la aplica al router.** Una reserva no corrige por sí sola una entrada de HA que ya apunta a otra IP, ni un problema de Wi-Fi, alimentación, cifrado, mDNS, audio o firmware.

### Alternativa avanzada: IP estática en ESPHome

ESPHome permite `wifi.manual_ip`. Su documentación señala que puede acelerar la conexión al evitar la negociación DHCP. Es una alternativa válida si no se puede reservar en el router y se conoce la configuración de red, pero **no es la primera intervención para esta incidencia**: implica modificar configuración, validar, compilar y desplegar firmware con su autorización y recuperación previstas.

Ejemplo conceptual que debe **integrarse en el bloque Wi-Fi existente**, sin duplicarlo ni borrar SSID, contraseña, AP de recuperación u otros ajustes:

```yaml
wifi:
  manual_ip:
    static_ip: !secret ball_static_ip
    gateway: !secret lan_gateway
    subnet: !secret lan_subnet
```

Esas claves de ejemplo no están configuradas por esta guía. Define valores propios de forma privada, evita solapamientos con asignaciones DHCP no reservadas y verifica gateway/subred. No copies una IP o una máscara genérica sin comprobar tu red. Una configuración incorrecta puede dejar la Ball inaccesible por red.

`wifi.use_address` es una opción de destino para las herramientas de conexión/subida: **no reserva una dirección, no configura por sí sola la IP del dispositivo y no actualiza la entrada ESPHome de Home Assistant**. No debe confundirse con `manual_ip` ni con una reserva del router.

## Si la IP es correcta y continúa START

| Observación | Siguiente comprobación |
|---|---|
| La Ball no aparece en clientes del router ni responde en una dirección confirmada | Alimentación, asociación Wi-Fi y red correcta; no asumir que sólo cambió de IP. |
| La dirección responde pero falla la autenticación ESPHome | Confirmar identidad y clave existente, sin desactivar cifrado ni resetear secretos para salir del paso. |
| ESPHome está conectado, pero START o la pulsación de 1 s siguen fallando | Revisar versión/build, uptime y motivo de reinicio, fase de inicialización/voz, estado de audio y errores recientes. Registrar separadamente la observación física. |
| El uptime se reinicia repetidamente | Investigar reinicios reales/alimentación/crash con registros acotados; no deducirlos de un GIF que se repite. |
| Sólo falla `.local`, pero conecta por dirección verificada | Investigar descubrimiento/multicast entre las redes de HA y la Ball, sin cambiar toda la red a ciegas. |

El menú está diseñado sin una dependencia directa de HA/Wi-Fi en `system_menu::can_open`, pero tiene guardas de inicialización, alarma y fases de voz. Eso no identifica por sí solo qué condición intervino en este incidente. No se ha aplicado un parche de firmware que garantice resolver todo START persistente.

**Evita reinicios repetidos, factory reset, borrado de NVS, reflasheo o cambios de Okey Hermes como primera solución.** Un corte de alimentación o una intervención USB/OTA son pasos distintos que sólo deben valorarse si el diagnóstico los justifica y existe un plan de recuperación; abrir USB de diagnóstico puede provocar un reset. Publicar esta guía no ha ejecutado ninguno de esos pasos.

## Fuentes y alcance

Consultadas el **2 de noviembre de 2026**:

- [Integración ESPHome de Home Assistant: reconfiguración y direcciones](https://www.home-assistant.io/integrations/esphome/).
- [ESPHome Wi-Fi: `manual_ip`, `use_address` y funcionamiento DHCP](https://esphome.io/components/wifi/).
- [Flujo ESPHome en Home Assistant 2026.7.2, versión de referencia del proyecto](https://github.com/home-assistant/core/blob/2026.7.2/homeassistant/components/esphome/config_flow.py).
- Fuentes archivadas del proyecto: [guarda del menú](../firmware/system_menu.h), [eventos de conexión y arranque](../firmware/config/core.yaml), [apertura local](../firmware/config/system_menu.yaml).

El caso se ha redactado a partir del cierre privado de diagnóstico, sin exportar sus recibos, direcciones o claves. Los enlaces oficiales respaldan el procedimiento general; no constituyen una prueba adicional del dispositivo ni de que la reserva DHCP ya esté aplicada.
