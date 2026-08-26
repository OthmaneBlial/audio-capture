# Changelog

All notable changes to Voice Transcriber are documented here.

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
