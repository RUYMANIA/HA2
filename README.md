# HA² (Home Hermes Agent Assistant)

**Un proyecto de RUYMANIA · Archivo privado de desarrollo · Validación física parcial**

[Español](#español) · [English](#english)

## Español

HA² conecta una **XiaoZhi Ball V2**, **Home Assistant** y **Hermes Agent** para ofrecer conversación por voz, una interfaz circular animada y notificaciones coordinadas desde Home Assistant. Hermes aporta conversación, herramientas y resultados de sus tareas; Home Assistant conserva la autoridad sobre las reglas y la entrega de avisos; la Ball presenta información y ejecuta la interacción local.

Este repositorio documenta y conserva una **copia saneada del trabajo existente**, no un producto listo para instalar ni una copia de seguridad de la vivienda. La configuración privada se ha omitido o sustituido por ejemplos. Las adaptaciones de publicación **no se han desplegado** en los equipos operativos.

### Estado de referencia

| Superficie | Base documentada | Alcance |
|---|---|---|
| Ball / ESPHome | HA² 1.3.1, build 2026-10-25 21:47:53 UTC | Instalación acreditada por el cierre local; revisión física del nuevo menú pendiente |
| HA² Notifications | 0.3.0 | Integración y panel documentados como instalados; no lectura en vivo durante esta publicación |
| Companion de Hermes / adaptador HA | 0.1.0 con ampliaciones locales | El número nominal no identifica todos los parches |
| Plugin Home Assistant para Hermes | 2.0.1 con puente HA² | El puente conserva internamente versión 0.2.0; admite backend 0.2.0/0.3.0 |
| Proactivo | BETA | Recorrido manual con aceptación auditiva documentada; automático OFF en el último cierre, oportunidad automática pendiente |

**No todas las funciones han sido probadas físicamente.** Un ACK, una prueba host o un hash correcto no demuestran audibilidad, tacto ni reproducción en el dispositivo.

### Contenido

- [`firmware/`](firmware/): fuentes ESPHome/C++, configuración ejemplo, animaciones, recursos y modelo de activación con su licencia.
- [`homeassistant/`](homeassistant/): integración HA² Notifications, panel y adaptador de conversación Hermes.
- [`hermes/`](hermes/): companion, backend de tarjetas y plugin/puente de tareas.
- [`docs/`](docs/): arquitectura, uso, instalación, seguridad, pruebas y pendientes, en español.
- Cada superficie conserva un manifiesto de procedencia y los límites de su snapshot.

### Empieza aquí

1. [Índice de documentación](docs/INDICE.md).
2. [Arquitectura y contratos](docs/ARQUITECTURA.md).
3. [Instalación y dependencias](docs/INSTALACION.md): guía de ingeniería, **no instalador automático**.
4. [Estado, pruebas y aceptación pendiente](docs/ESTADO-Y-PRUEBAS.md).
5. [Seguridad y límites del archivo](SECURITY.md).
6. [Procedencia y derechos](THIRD_PARTY.md). **No hay una licencia abierta global elegida para el código propio ni para todos los recursos creativos.**

El título del proyecto utiliza **Assistant**, como ha solicitado RUYMANIA. Algunas fuentes instaladas y recursos históricos conservan **Assitant**. No se han cambiado esos textos ni identificadores técnicos como efecto lateral del archivo.

## English

HA² links a **XiaoZhi Ball V2**, **Home Assistant**, and **Hermes Agent** to provide voice interaction, an animated circular display, and coordinated notifications. Hermes handles conversations, tools, and task results. Home Assistant owns notification rules and delivery coordination. The Ball provides the local user interface.

This is a **private, sanitized development snapshot**, not a turnkey release or a backup of a household installation. Private configuration is omitted or replaced with examples. Publication changes have **not** been deployed to the running systems.

The documented baseline is firmware **1.3.1** and HA² Notifications **0.3.0**. Versioned deployment records were inspected locally; this publication does not assert a new live hardware check. Proactive conversation remains **BETA**: a manual native conversation has documented audio acceptance, while automatic activation and the first real scheduled opportunity remain pending. The last recorded automatic setting was OFF.

See [`firmware/`](firmware/), [`homeassistant/`](homeassistant/), and [`hermes/`](hermes/) for each surface. Technical documentation is currently **in Spanish**; English translation will follow project approval. See [the documentation index](docs/INDICE.md) and [security notes](SECURITY.md) before attempting installation.

Do not flash compiled binaries from the original household installation, commit credentials, or run deployment/live test scripts against production. Original OTA/ELF binaries, sessions, private rules, databases and logs are deliberately excluded. Preserved tests are not all portable; each snapshot describes its prerequisites and verified subset.

Third-party notices remain applicable. No blanket open-source license has been selected for original HA² code or all artwork/audio. Keeping an asset in this private archive does not certify that it is cleared for public redistribution. The display spelling **Assitant** in historical resources is preserved; the repository title is **HA² (Home Hermes Agent Assistant)**.
