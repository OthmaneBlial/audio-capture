# Changelog

All notable changes to Voice Transcriber are documented here.

## [Unreleased]

## [0.4.0] - 2026-08-26

### Added

- A reproducible three-state product tour with static screenshots and a short
  animation made from synthetic sample text.
- A field-level data-flow document, supported-environment matrix, code of
  conduct, issue-routing config, label manifest, and bounded newcomer tasks.
- A privacy-safe `--doctor --json` readiness report with an explicit optional
  Groq reachability probe, stable schema, and actionable exit status.
- A keyboard-operable first-run setup that requires acknowledgement of the
  cloud boundary before transcription is enabled.
- A source-pinned Flatpak manifest, application metadata, generated Python
  dependency module, and clean-install smoke workflow.

### Changed

- Reframed the README and site around daily Linux dictation, an explicit cloud
  boundary, and the ability to inspect the app before configuring a Groq key.
- Replaced the transitive Groq SDK stack with a small, tested stdlib HTTP
  transport so the package boundary is easier to audit and reproduce.

## [0.2.0] - 2026-08-26

### Added

- Microphone picker backed by on-demand local PortAudio discovery, with a durable per-user selection.
- A rate-limited live input meter so a recording session can be verified before dictation.
- `--list-devices`, `--list-devices --json`, and `--device INDEX` for machine-friendly microphone diagnostics and one-session overrides.
- Native-boundary tests covering input filtering, selection, cleanup, and local signal-level normalization.

### Changed

- Microphone setup now explains unavailable saved devices and applies a changed source at the next session instead of silently changing an active capture.

## [0.1.0] - 2026-08-26

### Added

- Bounded transcription worker pool, actionable API errors, and configurable request timeout.
- Validated, atomically saved settings with owner-only permissions.
- A keyboard-friendly GTK recording desk with clear session state, copy, export, and always-on-top controls.
- CLI configuration check, package metadata, test suite, CI, contributor guidance, and security reporting policy.

### Changed

- Removed simulated transcription output: without a valid key the app now explains how to configure one.
- Microphone capture and shutdown now have bounded queues, cleanup, and failure recovery.
- API keys are ignored by Git and environment values explicitly override saved settings.
