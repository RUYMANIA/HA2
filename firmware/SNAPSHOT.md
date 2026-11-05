# Registro del snapshot firmware

Origen vigente: firmware **1.3.2**, cierre `ha2-okey-hermes-20261029`. Actualización de archivo del 1 de noviembre de 2026: tres YAML actualizados contra sus bytes congelados y dos artefactos Okey Hermes añadidos; demás fuentes/recursos y pruebas conservados. No se incluyen rutas privadas originales. El manifiesto registra la procedencia por archivo.

**Aceptación:** RUYMANIA confirma uso físico correcto de Okey Hermes tanto hablando en español como en inglés; el manifiesto sigue declarando entrenamiento `es`. No se ha ejecutado ninguna acción de hardware durante esta actualización.

## Conteos históricos de la primera copia (1.3.1)

```json
{
  "copied_files": 68,
  "headers": 11,
  "gif": 11,
  "cpp_sources": 18,
  "python_sources": 4,
  "redacted_files": 6,
  "cpp_compile_pass": 18,
  "cpp_run_pass": 17,
  "cpp_run_fail": 1
}
```

## Sustituciones por archivo

Solo saneado textual; sin cambios de lógica, entidades ni expectativas. Un recuento representa apariciones sustituidas; no identidades distintas. Sin valores privados originales.

| Archivo | IPv4 LAN → 192.0.2.10 | Ruta usuario → /path/to/user | MAC → 00:00:00:00:00:00 |
|---|---:|---:|---:|
| `release-tools/night_audio_test.cpp` | 1 | 0 | 0 |
| `release-tools/night_pending_test.cpp` | 1 | 0 | 0 |
| `release-tools/test_actual_lambdas.py` | 1 | 2 | 0 |
| `release-tools/test_demo_lambdas.py` | 0 | 1 | 0 |
| `temporary_cards.h` | 1 | 0 | 0 |
| `tests/temporary_cards_test.cpp` | 5 | 0 | 0 |

Los demás archivos copiados son byte-idénticos según el manifiesto. El saneado puede romper expectativas históricas negativas que comparaban IP distintas: no se modifica esa lógica para ocultarlo.

## Ejecución histórica de la primera copia (26-10-2026)

Comandos por archivo, salida y códigos reales en TEST-RESULTS.json. Directorio de trabajo del compilador: raíz de este snapshot; ejecutables temporales exclusivamente en scratch y eliminados después. No se ejecutan runners originales ni Python, ESPHome, red HA, OTA o reinicios. No se infieren pruebas físicas ni una suite portable.

## Exclusiones y derechos

Allowlist cerrada; no se copian secrets.yaml, logs/reportes originales, backups, cachés, ELF/OTA/factory, scripts de operación, baseline ni fuentes de otros proyectos. El TFLite sí es el recurso de modelo solicitado, no firmware OTA. QR nearest es la comparación histórica y opaque-rgb es el incorporado. Ese fue el estado del archivo inicial privado. Actualización de licencia del 5 de noviembre de 2026: RUYMANIA autoriza MIT para su código/aportaciones originales no excluidas y la apertura pública; **Okey Hermes permanece incluido pero fuera de MIT, sin licencia abierta alternativa ni permiso comercial concedidos**, según `models/okey-hermes/LICENSE.md`. Se conservan avisos de terceros y se detallan recursos/procedencia en `../THIRD_PARTY.md`. La publicación no cambia ni reentrena el modelo y no reescribe el historial.
