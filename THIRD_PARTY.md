# Procedencia y componentes de terceros

| Componente | Procedencia | Identidad documentada | Tratamiento |
|---|---|---|---|
| Base ESPHome Ball V2 | RealDeco/xiaozhi-esphome | `12599ede7b79101157ac55bb31f4c28356ccbb69` | MIT, copyright 2025 RealDeco; conservar licencia y distinguir YAML derivados |
| Companion y adaptador HA Hermes | Codename-11/hermes-homeassistant | Procedencia histórica `7dc174cedf2cf47b16083979ff9b5b4bfc8fa8a9` | MIT, copyright 2026 Bailey Dixon; hay modificaciones posteriores locales |
| Plugin Home Assistant para Hermes | NousResearch/hermes-homeassistant | Base observada `ba30cb0cf86c52bdb5cde98974bc062e97966529` | MIT Nous Research; wiring y puente HA² locales |
| Modelo Okey Hermes | Entrenamiento local exportado con microWakeWord Trainer Apple Silicon | SHA pesos `c3a747d398c526c0d1f092ae315a9aa10d3df8e3051379c2227dd14aec56b974` | Archivo privado; manifiesto original conserva autoría/website del exportador; licencia abierta propia no elegida |
| Modelo Hey Hermes | miketomkins/hey-hermes-wakeword-model | SHA pesos `2073e984de30b7cd004428930e6363fe58b9158823f888cc269168b62597f995` | MIT Mike Tomkins; LICENSE y MODEL_CARD preservados; no benchmark español |
| Hermes Agent core | NousResearch/hermes-agent | Entorno histórico `bf0203a794a07aac3ff764972ab9087baa4e4f4e` | Dependencia externa, no copia del runtime |
| ESPHome y dependencias | ESPHome y proveedores respectivos | Entorno firmware documentado ESPHome 2026.9.1 | Dependencias externas, no atribuir una licencia única al firmware compuesto |

Las licencias de RealDeco y Codename-11 se recuperaron de la API oficial de GitHub en las revisiones indicadas, no por inferencia a partir de proyectos con nombres parecidos. Los manifiestos de snapshot describen hashes de las fuentes seleccionadas y de las copias saneadas: no afirman que el upstream histórico sea idéntico al código actual.

## Recursos y descargas externas

- Once GIF de la Ball: derivados de la identidad gráfica aportada al proyecto, con variantes de etiquetas internacionales. Derechos de marca/arte pendientes de consolidar antes de publicación pública.
- Saludo `startup-cori-v2.mp3`: preview aprobado con voz `en_GB-cori-high` y mezcla local. Tres notas `notification.wav`/`proactive-three-notes.wav`: recurso de aviso derivado del preview anterior. No son grabaciones de conversaciones. Procedencia de voz/música y condiciones de redistribución pendientes de cierre documental.
- QR: recurso de marca generado; verificar el destino y la titularidad de la identidad antes de distribuir.
- Iconos del adaptador HA: procedencia upstream, no concede derechos adicionales de marca.
- Google Fonts **Figtree** y **Syne Mono**, sonidos FLAC remotos y modelos stock referenciados por ESPHome no se han vendorizado como una distribución completa. Revisar sus licencias/versiones si se añaden pesos, fuentes o binarios al archivo.

No se ha elegido MIT para todo HA² por asociación con sus dependencias. Mantener privado hasta resolver licencia propia, recursos y requisitos de distribución.
