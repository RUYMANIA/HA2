# Hey Hermes model card

## Summary

Hey Hermes is an English-language ESPHome microWakeWord model intended to add **“Hey Hermes”** as a selectable wake word on the Home Assistant Voice Preview Edition (Voice PE, 8 MB).

**Status:** experimental. The integration has been tested on Voice PE, but formal far-field and false-alarm performance results have not yet been published.

## Bundle identity

| Item | Value |
| --- | --- |
| Model file | `hey-hermes.tflite` |
| Model SHA-256 | `2073e984de30b7cd004428930e6363fe58b9158823f888cc269168b62597f995` |
| Manifest schema | microWakeWord v2 |
| Declared language | English (`en`) |
| Intended hardware | Home Assistant Voice Preview Edition (Voice PE, 8 MB) |
| Minimum ESPHome version | `2026.8.0` |

## Intended use

Use this model only as the wake-word component of a custom ESPHome firmware build for Voice PE. It runs on-device and is intended to begin a Home Assistant Assist interaction after the phrase “Hey Hermes.”

It is not a ready-to-flash firmware image, a speech-to-text model, a general speech-recognition model, or a security/authentication mechanism.

## Deployment configuration

The published manifest supplies these initial parameters:

| Setting | Value |
| --- | ---: |
| Probability cutoff | `0.32` |
| Sliding-window size | `5` |
| Feature step size | `10` ms |
| Tensor arena size | `65,536` bytes |

The cutoff is preliminary. It was selected during an initial ROC review, but the ROC curve, operating-point rationale, evaluation corpus description, and false-accept rate have not yet been published. A user should not infer a specific false-alarm rate from the value alone.

## Training information

The following facts are currently published:

- The model was trained for the English phrase “Hey Hermes.”
- The deployment manifest uses the parameters shown above.

The following details have **not** been publicly documented for this release and should not be inferred:

- Number of positive and negative samples, speakers, recording environments, or data splits.
- Source, consent, license, retention, or release status of any training recordings.
- Training-tool version, model architecture, optimizer, epochs, random seed, augmentation, and preprocessing beyond the manifest's feature-step setting.
- Held-out recall, missed-detection rate, false accepts per hour, ROC values, distance tests, and noise-condition results.

No raw training recordings are included in this repository.

## Evaluation status

Observed integration checks on Voice PE:

- The custom configuration compiled successfully with the model manifest and TFLite file.
- The firmware flashed, reconnected to Home Assistant, and exposed **Hey Hermes** in the Wake word selector.
- An initial end-to-end voice command successfully controlled Home Assistant lights.

These checks verify installation and one positive use case only. They are not a benchmark and do not establish performance at room distance or in everyday background audio.

## Known limitations

- The Home Assistant Voice PE is the only integration-tested target.
- Accents, languages other than English, microphone placement, room size, background conversation, television audio, music, and competing speech have not been formally evaluated.
- False accepts per hour and missed detections are unknown.
- The Voice PE **Wake word sensitivity** selector does not currently adjust the Hey Hermes cutoff in the tested source configuration; it changes only the bundled stock wake-word models.
- The model must not be used for identity verification, safety-critical activation, or any application where an unmeasured false activation is unacceptable.

## Planned validation

Before describing this model as broadly validated, collect and publish a controlled validation summary that includes:

1. At least 14 consecutive days of ordinary in-home listener time, with total listener-hours and every unintended activation recorded.
2. Intentional wake-word trials by multiple speakers at documented distances and room-noise conditions, including the total trials and misses.
3. Separate tests with background conversation, television, and music where practical.
4. A held-out evaluation set and ROC/operating-point summary, including the basis for the selected cutoff.
5. A versioned manifest/model pair for every changed cutoff, with the corresponding test results.

Report results as counts and rates, including false activations per listener-hour and misses per intentional trial. Do not generalize a result beyond the tested Voice PE environment.

## License

Unless otherwise noted, the model weights, manifest, and documentation are licensed under the [MIT License](LICENSE).
