# Procedencia y alcance de terceros

RealDeco/xiaozhi-esphome, commit `12599ede7b79101157ac55bb31f4c28356ccbb69`.
Licencia recuperada íntegra desde `https://raw.githubusercontent.com/RealDeco/xiaozhi-esphome/12599ede7b79101157ac55bb31f4c28356ccbb69/LICENSE`; MIT, copyright 2025 RealDeco. Véase `RealDeco-LICENSE`.

Los cinco YAML de `vendor/` proceden de `devices/Under_Development/Modular/` en ese commit: `Ball_v2.yaml`, `core.yaml`, `display_pages.yaml`, `clocks-standard.yaml` y `HW/ball_v2_hw.yaml`. Los cambios de saneado, si existen, constan en SNAPSHOT.md y el manifiesto; no se presentan copias modificadas como byte-idénticas. `config/` y la entrada son adaptaciones locales, no copias literales del upstream.

El paquete `models/hey-hermes/` declara miketomkins/hey-hermes-wakeword-model y conserva LICENSE MIT (copyright 2026 Mike Tomkins), MODEL_CARD.md y SHA256SUMS originales. No se ha fijado aquí un commit upstream adicional; identidad por hashes.

El modelo local `models/okey-hermes/` se exportó con microWakeWord Trainer Apple Silicon. Su manifiesto original conserva autor Tater Totterson y website del entrenador; no se altera para aparentar otra procedencia. Pesos originales del entrenamiento del proyecto, identidad por SHA-256; no se les asigna la MIT del modelo Hey Hermes. Licencia abierta propia y derechos de distribución pública pendientes; archivo privado autorizado.

No se elige licencia para las aportaciones propias ni para el conjunto. La MIT upstream y la del modelo no licencian automáticamente GIF, logo, QR, voz ni música. Estos recursos creativos se incluyen únicamente para archivo privado autorizado; derechos y procedencia completa pendientes de validar antes de abrir el repositorio o redistribuirlos públicamente.

Dependencias no incorporadas completas: ESPHome (entorno histórico 2026.9.1), ESP-IDF/toolchain, fuentes Figtree y Syne Mono, sonidos FLAC upstream y modelos stock okay_nabu/hey_jarvis/alexa. Sus versiones, licencias y descargas requieren revisión separada; no hay build offline ni redistribución binaria acreditados.
