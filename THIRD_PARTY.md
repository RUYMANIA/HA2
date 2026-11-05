# Procedencia y componentes de terceros

**Licencias separadas:** [MIT](LICENSE) para el código y las aportaciones originales de RUYMANIA que no estén expresamente excluidas; cada tercero conserva sus condiciones. **Okey Hermes está incluido, pero fuera de MIT y sin licencia abierta alternativa concedida para sus pesos**: [aviso específico](firmware/models/okey-hermes/LICENSE.md). No se presenta todo el contenido del repositorio como una única distribución MIT.

| Componente | Procedencia | Identidad documentada | Tratamiento |
|---|---|---|---|
| Base ESPHome Ball V2 | RealDeco/xiaozhi-esphome | `12599ede7b79101157ac55bb31f4c28356ccbb69` | MIT, copyright 2025 RealDeco; aviso íntegro en firmware/THIRD_PARTY/RealDeco-LICENSE; distinguir YAML derivados |
| Companion y adaptador HA Hermes | Codename-11/hermes-homeassistant | Procedencia histórica `7dc174cedf2cf47b16083979ff9b5b4bfc8fa8a9` | MIT, copyright 2026 Bailey Dixon; avisos íntegros en sus superficies; modificaciones locales posteriores diferenciadas |
| Plugin Home Assistant para Hermes | NousResearch/hermes-homeassistant | Base observada `ba30cb0cf86c52bdb5cde98974bc062e97966529` | MIT Nous Research; wiring y puente HA² locales; aviso íntegro preservado |
| Modelo Okey Hermes | Entrenamiento local exportado con microWakeWord Trainer Apple Silicon | SHA pesos `c3a747d398c526c0d1f092ae315a9aa10d3df8e3051379c2227dd14aec56b974` | **Excluido de MIT; no se concede licencia abierta alternativa ni permiso comercial**. Procedencia NC e incertidumbres descritas en su aviso específico |
| Modelo Hey Hermes | miketomkins/hey-hermes-wakeword-model | SHA pesos `2073e984de30b7cd004428930e6363fe58b9158823f888cc269168b62597f995` | MIT Mike Tomkins; LICENSE y MODEL_CARD preservados; no confundir con Okey Hermes |
| Logo base de los GIF | NousResearch/hermes-agent | Logo idéntico al de `bd312c903ea42763a535a5ac034ef132fad1a5d2`, SHA `b76ed32dd5ffdf842db696dc6dc0992529acfe12903ec1b2128251a41dfd31d2` | MIT del repositorio, copyright Nous Research; aviso íntegro en firmware/THIRD_PARTY/NousResearch-hermes-agent-LICENSE; no se conceden derechos de marca ni se afirma afiliación oficial |
| Hermes Agent core | NousResearch/hermes-agent | Entorno histórico `bf0203a794a07aac3ff764972ab9087baa4e4f4e` | Dependencia externa; no se copia su runtime como parte de este archivo |
| ESPHome y dependencias | ESPHome y proveedores respectivos | Entorno firmware documentado ESPHome 2026.9.1 | Dependencias externas; no atribuir una licencia única al firmware compuesto |

Las licencias upstream se recuperan en las revisiones indicadas, no por asociación con nombres parecidos. Los manifiestos describen hashes de las fuentes seleccionadas y de las copias saneadas; no afirman que el upstream histórico sea idéntico al código actual. Las modificaciones originales de RUYMANIA quedan bajo MIT, sin borrar atribuciones anteriores.

## Recursos visuales

- **Once GIF**: animaciones locales derivadas del logo aportado, identificado por sus bytes con el [logo oficial de NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent/blob/bd312c903ea42763a535a5ac034ef132fad1a5d2/website/static/img/logo-dark.png). Conservar tanto el aviso MIT de Nous Research para la base como la atribución de las animaciones/modificaciones de RUYMANIA. No se atribuye el personaje original íntegramente al proyecto HA².
- **QR**: generado para enlazar a RUYMANIA. Su generación y las aportaciones originales se incluyen en MIT; no es una licencia de ninguna marca que pudiera aparecer en el destino.
- **Fotografías ES/EN**: aportadas por RUYMANIA para documentar el menú; originales del usuario en el alcance de su autorización. Copias saneadas sin metadata doméstica y con las redacciones del manifiesto. La fotografía no cede derechos sobre marcas visibles ni demuestra la ejecución de los controles.
- **Iconos del adaptador HA**: procedencia upstream, sin concesión adicional de derechos de marca.

## Audio

- **`startup-cori-v2.mp3`**: saludo con voz **en_GB-cori-high** y mezcla procedural original del proyecto. No es una grabación de conversaciones ni una canción descargada. Las aportaciones originales de texto, composición y mezcla se incluyen en MIT, sin atribuir a RUYMANIA la voz base.
- **Cori high**: el creador **Bryce Beattie** identifica el modelo como **public domain** en [su página de voces](https://brycebeattie.com/files/tts); la [modelcard oficial](https://huggingface.co/rhasspy/piper-voices/blob/main/en/en_GB/cori/high/MODEL_CARD) documenta LibriVox. [LibriVox advierte](https://librivox.org/pages/public-domain/) de diferencias territoriales en dominio público. No se distribuye aquí el modelo Cori ni el motor Piper; no se infiere una licencia del audio a partir de la licencia del programa.
- **`notification.wav` / `proactive-three-notes.wav`**: tres notas extraídas de la composición procedural local previa, sin voz, no un recurso musical externo. Aportación original bajo MIT; no se regeneran ni se altera el volumen por esta publicación.

## Dependencias y material no distribuido

Google Fonts **Figtree** y **Syne Mono**, sonidos FLAC remotos y modelos stock referenciados por ESPHome no se han vendorizado como una distribución completa. Revisar sus licencias/versiones si se añaden al archivo. El entrenador, corpus, grabaciones, checkpoints y generadores TTS de Okey Hermes **no se distribuyen**; su código o sus pesos no quedan licenciados por este repositorio.

La apertura pública y la exclusión de Okey Hermes de MIT fueron autorizadas expresamente por RUYMANIA el **5 de noviembre de 2026**. La autorización propia no elimina derechos de terceros ni certifica que una reutilización concreta sea legal. Véanse [LICENSE.md](LICENSE.md), [seguridad](SECURITY.md) y los límites técnicos documentados.
