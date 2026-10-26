# Registro del snapshot firmware

Origen lógico: `ha2-menu-1.3.1`; no se incluyen rutas privadas originales.

## Conteos calculados

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

## Ejecución nueva

Comandos por archivo, salida y códigos reales en TEST-RESULTS.json. Directorio de trabajo del compilador: raíz de este snapshot; ejecutables temporales exclusivamente en scratch y eliminados después. No se ejecutan runners originales ni Python, ESPHome, red HA, OTA o reinicios. No se infieren pruebas físicas ni una suite portable.

## Exclusiones y derechos

Allowlist cerrada; no se copian secrets.yaml, logs/reportes originales, backups, cachés, ELF/OTA/factory, scripts de operación, baseline ni fuentes de otros proyectos. El TFLite sí es el recurso de modelo solicitado, no firmware OTA. QR nearest es la comparación histórica y opaque-rgb es el incorporado. No se elige licencia propia. Artwork/audio/voz/música: derechos de redistribución pública sin validar; archivo privado autorizado.
