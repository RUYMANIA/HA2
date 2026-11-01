# Estado y pruebas

## Qué se acredita

La publicación parte de fuentes y cierres **locales archivados**. No incluye nueva lectura de la Ball/HA vivo ni nuevas pruebas auditivas/táctiles. Los hash manifiestan identidad de archivos, no ausencia de fallos ni equivalencia de un firmware compilado con configuración diferente.

| Elemento | Evidencia histórica | Pendiente/límite |
|---|---|---|
| Firmware 1.3.2 | Cierre de instalación del 29-10-2026, build 13:28:53 UTC; modelo Okey Hermes incorporado | No se ha repetido OTA/build completo ni prueba física durante esta publicación |
| Okey Hermes | Prueba física inicial aceptada 29-10; uso en español e inglés confirmado por RUYMANIA el 1-11-2026 | Aceptación humana de uso, no entrenamiento bilingüe ni benchmark prolongado |
| Fuentes firmware | Base 1.3.1 comprobada en primera publicación y freeze de 43 fuentes 1.3.2 verificado al actualizar Okey Hermes | Copia saneada tiene hashes propios; no mismo artefacto instalado |
| Recursos | Preservación histórica de 25 arrays compilados | No nueva compilación ni medición de heap/audio runtime durante archivo |
| Host firmware | Registro histórico 67 comandos correctos y sanitizers | No 67 pruebas reejecutadas por esta publicación |
| HA/panel | Backend 0.3.0, JS servido con hash acreditado por cierre local | No demuestra navegador actual recargado |
| QA coordinado previo (25-10) | Informe histórico de 237 pruebas correctas, anterior a las ampliaciones de 27–29-10 | No es el QA de las fuentes actuales; pruebas posteriores se registran en cada superficie |
| Proactivo manual | Secuencia nativa, contexto y aceptación auditiva de invitación/respuesta documentados | No valida activación y primera oportunidad automática |
| Proactivo automático | ACTIVO en cierres posteriores de 27–29-10 y aprobado por RUYMANIA; sin etiqueta BETA | No confundir aprobación/activación con una nueva oportunidad natural observada durante esta publicación |
| Log de Actividad | Ampliación instalada 27-10; tres orígenes, metadatos y hasta 200 eventos; rótulos posteriores | No se fabrica atribución de registros antiguos ni se insertan filas de prueba en producción |
| Invitaciones breves | Transporte instalado 29-10; máximo 120 caracteres/20 palabras/240 bytes | No afecta a conversación normal; inválidas rechazadas, sin truncado ni nueva inferencia |

El recibo histórico `foreign_config_drift` no se reescribe como PASS: no hay baseline global suficiente para atribuirlo. Las comprobaciones independientes de fuentes y funciones tienen su alcance propio. Un antiguo agregador que busca un `health.json` inexistente tampoco demuestra que el controlador real esté caído.

## Resultados de la copia de publicación

La tabla y los informes de la primera publicación de 26-10 son históricos; la actualización de 1-11 añade los cierres y aceptación posteriores, sin presentar el OFF/BETA antiguo como vigente. Véase [Okey Hermes](OKEY-HERMES.md) y los manifiestos por superficie.

Consultar el resumen generado `publication-verification.json` en la raíz y los SNAPSHOT/manifest de cada superficie para los comandos realmente ejecutados sobre esta copia. No sumar pruebas históricas con pruebas nuevas ni contadores de comandos con casos unitarios.

Las pruebas puras deben usar fixtures sin hardware y temporales aislados. Tests Python de integración real requieren las dependencias HA apropiadas; tests DOM Node no sustituyen una prueba Chromium ni el panel autenticado. Runners que hacían `docker exec homeassistant` o invocaban API/OTA se han excluido del flujo publicable.

## Verificación de la actualización de 1 de noviembre de 2026

- Firmware: 12 comprobaciones de integridad/contrato correctas; 43 fuentes del freeze original verificadas, tres YAML copiados idénticos y dos artefactos Okey Hermes originales añadidos. No son pruebas acústicas ni recompilación de producción.
- Home Assistant: el padre repitió **71 casos Python y 58 Node, todos correctos**, en copia y con HOME/HERMES_HOME/TMPDIR efímeros. La suite usa módulos puros y probes AST de invitaciones; no acredita clases HA completas, render de navegador ni audio real.
- Las cuatro fuentes HA incorporadas coinciden con los SHA de sus respectivos cierres instalados, no con un candidato más amplio.
- Superficie Hermes: 39 fuentes de origen contrastadas sin cambios frente al archivo previo; no se modifica runtime/companion/plugin para publicar esta actualización.
- Aceptación humana Okey Hermes: uso correcto en español e inglés confirmado por RUYMANIA; entrenamiento conservado en español. No se inventan pruebas acústicas adicionales.

## Fallo heredado reproducido

El ejecutable autónomo `firmware/tests/temporary_cards_test.cpp` aborta en la aserción de la línea 26 tanto en la fuente original de 1.3.1 como en la copia saneada. Compila con ASAN/UBSAN en ambos casos; ambos retornan `-6`. Se conserva el fallo y no se cambia producción ni el test para obtener un PASS. Es un pendiente del conjunto histórico, no una regresión introducida por sustituir la IP. El runner histórico aplicaba adaptaciones que no forman parte de este ejecutable autónomo; no se ha reejecutado ese runner ni se atribuye aquí una causa raíz más detallada.

Repetición independiente sobre la copia: **18 ejecutables C++ compilan, 17 pasan y 1 falla**. HA: **15 tests Python y 54 Node correctos**. Hermes: suites launcher 1, tarjetas 32, bridge 15, runtime 9 y timing 8 correctas; pytest plugin **95 passed, 1 skipped, 11 subtests passed**. Hay solapamiento entre la recogida pytest y bridge/runtime: no sumar esos contadores como casos únicos. El skip corresponde a una prueba de la base que busca un archivo retirado del core.

## Plan de aceptación posterior

1. Revisar físicamente acceso, orden y navegación del menú y legibilidad del QR/textos.
2. Validar por separado botones de mantenimiento y secuencia de once GIF/dos ciclos, sin activar voz/audio ajenos.
3. Confirmar entrega de tarjeta, historial silencioso, lectura completa, TTL y modo noche en recorridos específicos.
4. Probar integración de tareas reales opt-in, correlación de ejecución y no duplicación del planificador.
5. Conservar Proactivo ya aprobado/activo. Cuando se evalúe una ejecución natural, documentar su alcance sin forzar el planificador ni reabrir una activación ya aceptada. Okey Hermes y su uso ES/EN no siguen pendientes.

No ejecutar este plan por publicar documentación. Registrar fecha, versión exacta, recorrido y confirmación humana sin guardar conversaciones privadas en Git.
