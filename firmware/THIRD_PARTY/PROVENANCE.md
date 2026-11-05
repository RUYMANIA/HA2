# Procedencia y alcance de terceros

RealDeco/xiaozhi-esphome, commit `12599ede7b79101157ac55bb31f4c28356ccbb69`.
Licencia recuperada íntegra desde `https://raw.githubusercontent.com/RealDeco/xiaozhi-esphome/12599ede7b79101157ac55bb31f4c28356ccbb69/LICENSE`; MIT, copyright 2025 RealDeco. Véase `RealDeco-LICENSE`.

Los cinco YAML de `vendor/` proceden de `devices/Under_Development/Modular/` en ese commit: `Ball_v2.yaml`, `core.yaml`, `display_pages.yaml`, `clocks-standard.yaml` y `HW/ball_v2_hw.yaml`. Los cambios de saneado, si existen, constan en SNAPSHOT.md y el manifiesto; no se presentan copias modificadas como byte-idénticas. `config/` y la entrada son adaptaciones locales, no copias literales del upstream. Aportaciones originales de RUYMANIA bajo [MIT](../../LICENSE), preservando los avisos anteriores.

El paquete `models/hey-hermes/` declara miketomkins/hey-hermes-wakeword-model y conserva LICENSE MIT (copyright 2026 Mike Tomkins), MODEL_CARD.md y SHA256SUMS originales. No se ha fijado aquí un commit upstream adicional; identidad por hashes.

**`models/okey-hermes/okey_hermes.tflite` queda expresamente fuera de MIT** y no se atribuye MIT al manifiesto exportado. Se publica como referencia sin conceder una licencia abierta alternativa ni permiso comercial; véase [su aviso específico](../models/okey-hermes/LICENSE.md), con procedencia e incertidumbres del entrenamiento. Su manifiesto conserva autor Tater Totterson y website por ser valores del exportador, no prueba de autoría del entrenamiento local. No se atribuye la licencia de Hey Hermes al detector Okey Hermes.

La base de los once GIF coincide con el logo de NousResearch/hermes-agent, revisión `bd312c903ea42763a535a5ac034ef132fad1a5d2`; conservar `NousResearch-hermes-agent-LICENSE`. Las animaciones y modificaciones originales de RUYMANIA se incluyen en MIT, sin conceder derechos de marca ni atribuir el personaje original a HA². QR, música procedural, voz Cori/Bryce Beattie y fotografías tienen procedencia diferenciada en [THIRD_PARTY.md](../../THIRD_PARTY.md); la voz no se relicencia por usar Piper.

Dependencias no incorporadas completas: ESPHome (entorno histórico 2026.9.1), ESP-IDF/toolchain, fuentes Figtree y Syne Mono, sonidos FLAC upstream y modelos stock okay_nabu/hey_jarvis/alexa. Sus versiones, licencias y descargas requieren revisión separada; no hay build offline ni redistribución binaria acreditados.
