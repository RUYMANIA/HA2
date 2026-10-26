# Estado y pruebas

## Qué se acredita

La publicación parte de fuentes y cierres **locales archivados**. No incluye nueva lectura de la Ball/HA vivo ni nuevas pruebas auditivas/táctiles. Los hash manifiestan identidad de archivos, no ausencia de fallos ni equivalencia de un firmware compilado con configuración diferente.

| Elemento | Evidencia histórica | Pendiente/límite |
|---|---|---|
| Firmware 1.3.1 | Cierre de instalación del 25-10-2026, build 21:47:53 UTC, identidad/uptime coherentes | Aceptación física nuevo menú, reinicio y test animaciones |
| Fuentes firmware | Inventario verificó 41/41 hashes y procedencia de cinco YAML | Copia saneada tiene hashes propios; no mismo artefacto instalado |
| Recursos | Preservación histórica de 25 arrays compilados | No nueva compilación ni medición de heap/audio runtime durante archivo |
| Host firmware | Registro histórico 67 comandos correctos y sanitizers | No 67 pruebas reejecutadas por esta publicación |
| HA/panel | Backend 0.3.0, JS servido con hash acreditado por cierre local | No demuestra navegador actual recargado |
| QA coordinado | Último informe histórico 237 pruebas correctas | No reejecutadas íntegramente, no hardware |
| Proactivo manual | Secuencia nativa, contexto y aceptación auditiva de invitación/respuesta documentados | No valida activación y primera oportunidad automática |
| Proactivo automático | OFF en último cierre local | Activación, guardas y primera oportunidad real pendientes |

El recibo histórico `foreign_config_drift` no se reescribe como PASS: no hay baseline global suficiente para atribuirlo. Las comprobaciones independientes de fuentes y funciones tienen su alcance propio. Un antiguo agregador que busca un `health.json` inexistente tampoco demuestra que el controlador real esté caído.

## Resultados de la copia de publicación

Consultar el resumen generado `publication-verification.json` en la raíz y los SNAPSHOT/manifest de cada superficie para los comandos realmente ejecutados sobre esta copia. No sumar pruebas históricas con pruebas nuevas ni contadores de comandos con casos unitarios.

Las pruebas puras deben usar fixtures sin hardware y temporales aislados. Tests Python de integración real requieren las dependencias HA apropiadas; tests DOM Node no sustituyen una prueba Chromium ni el panel autenticado. Runners que hacían `docker exec homeassistant` o invocaban API/OTA se han excluido del flujo publicable.

## Fallo heredado reproducido

El ejecutable autónomo `firmware/tests/temporary_cards_test.cpp` aborta en la aserción de la línea 26 tanto en la fuente original de 1.3.1 como en la copia saneada. Compila con ASAN/UBSAN en ambos casos; ambos retornan `-6`. Se conserva el fallo y no se cambia producción ni el test para obtener un PASS. Es un pendiente del conjunto histórico, no una regresión introducida por sustituir la IP. El runner histórico aplicaba adaptaciones que no forman parte de este ejecutable autónomo; no se ha reejecutado ese runner ni se atribuye aquí una causa raíz más detallada.

Repetición independiente sobre la copia: **18 ejecutables C++ compilan, 17 pasan y 1 falla**. HA: **15 tests Python y 54 Node correctos**. Hermes: suites launcher 1, tarjetas 32, bridge 15, runtime 9 y timing 8 correctas; pytest plugin **95 passed, 1 skipped, 11 subtests passed**. Hay solapamiento entre la recogida pytest y bridge/runtime: no sumar esos contadores como casos únicos. El skip corresponde a una prueba de la base que busca un archivo retirado del core.

## Plan de aceptación posterior

1. Revisar físicamente acceso, orden y navegación del menú y legibilidad del QR/textos.
2. Validar por separado botones de mantenimiento y secuencia de once GIF/dos ciclos, sin activar voz/audio ajenos.
3. Confirmar entrega de tarjeta, historial silencioso, lectura completa, TTL y modo noche en recorridos específicos.
4. Probar integración de tareas reales opt-in, correlación de ejecución y no duplicación del planificador.
5. Autorizar/activar Proactivo sólo con capacidades disponibles y validar primera oportunidad automática, noche/ocupación y contexto de respuesta.

No ejecutar este plan por publicar documentación. Registrar fecha, versión exacta, recorrido y confirmación humana sin guardar conversaciones privadas en Git.
