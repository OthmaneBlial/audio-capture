# Changelog

All notable changes to Voice Transcriber are documented here.

## [Unreleased]

## [1.0.0] - 2026-08-27

### Added

- A public privacy notice and threat model spanning microphone capture, local
  VAD, bounded memory, provider requests, credentials, exports, opt-in text
  history, logs, local executables, and release supply chain.
- Privacy regression tests for raw-audio non-persistence, secret and provider
  detail redaction, history-off defaults, explicit text storage permissions,
  and deletion.
- Tag-driven release automation that produces a checksum, CycloneDX SBOM,
  deterministic test report, GitHub provenance and SBOM attestations, and
  downloadable Sigstore bundles.
- A contributor map with architecture, no-key development, fake-fixture, UI,
  packaging, and issue-to-PR guides; plus eight maintained public tasks.
- An FAQ, explicit public-feedback loop, and technical/user launch stories
  with original cover art.

### Changed

- Expanded CI to Python 3.9, 3.11, and 3.14 with branch coverage, wheel/sdist
  builds, hash-pinned dependency audit, Bandit, Ruff, and compilation.
- Hardened Flatpak verification with documented linter exceptions, mirrored
  AppStream media, an offline no-download rebuild, installed-bundle smoke, and
  compatibility-safe reporting.
- Release notes now lead from a visual demo to verified installation, support,
  privacy delta, benchmark receipt, and bounded help-wanted tasks.

### Privacy

- The runtime data path is unchanged: local VAD precedes Groq transmission,
  raw audio is not persisted by the app, transcript history stays disabled by
  default, and exports remain explicit.
- Release and diagnostic evidence adds no analytics, crash upload, transcript
  collection, recording collection, or project server.
- The experimental local provider remains source-only, explicitly flagged,
  user-supplied, and disabled in Flatpak; v1 does not relabel it as supported.

### Verification

- Fifty-nine deterministic unit tests, Ruff, source compilation, release
  version checks, and release-note surface tests pass locally before the tag.
- Exact-commit CI, Flatpak, CodeQL, public release asset, checksum, SBOM,
  provenance, and attestation evidence is recorded in `ROADMAP.md` after each
  remote gate completes; physical microphone/desktop combinations remain a
  separately labelled community gate.

## [0.6.0] - 2026-08-26

### Added

- A typed transcription-provider contract with capability, language,
  cancellation, limit, normalized-error, and data-boundary metadata.
- A provider-aware first run, Settings selector, active-boundary desk label,
  config check, and privacy-safe diagnostics.
- A source-only, explicit-feature-flag whisper.cpp prototype using a
  memory-backed Linux file descriptor instead of a raw-audio file.
- A checksum-pinned LibriSpeech preparation tool, WER/latency receipt harness,
  deterministic unit tests, and a manually triggered pinned local benchmark.

### Changed

- Groq remains the supported packaged path but now implements the same bounded
  provider contract and cancellation/error behavior as future backends.

### Privacy

- Groq transmission remains limited to completed speech segments after local
  VAD. Experimental local mode is source-only, explicit, disabled in Flatpak,
  and passes WAV through Linux memory rather than an app-created audio file.
- Provider errors and local process failures are normalized without logging
  response bodies, credentials, transcript content, or local paths.

### Verification

- Fifty deterministic unit tests, Ruff, and source compilation passed in exact
  commit CI run `33015936280`.
- Benchmark run `33015305254` passed on 25 deterministic LibriSpeech
  `test-clean` speakers with whisper.cpp tiny.en: 37 errors / 627 reference
  words (5.90% WER), 1,043.810 ms p50 and 1,508.576 ms p95 wall-clock latency
  on its named GitHub runner. The complete unedited receipt is committed.
- Flatpak run `33015936279` built and installed `0.6.0`, passed CLI/doctor,
  provider-boundary and mapped GTK accessibility smoke tests, then uninstalled.
- CodeQL run `33015923746` passed for Python, Actions, and JavaScript with no
  open code-scanning alerts.

## [0.5.0] - 2026-08-26

### Added

- An editable transcript desk with bounded undo/redo, select-all, clear
  confirmation, and recent per-segment pending/complete/error states.
- Focused push-to-talk, capability-gated X11 tray window toggle, and an honest
  explanation where global shortcuts or tray integration are unavailable.
- Optional copy-on-final and destination-confirmed plain text, Markdown, and
  timestamped exports written with owner-only permissions.
- Explicit opt-in local text history with configurable expiry, storage-path
  disclosure, retrieval, per-entry deletion, and clear-all controls.
- A real-participant usability protocol that does not confuse automated
  heuristic review with five observed sessions.

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
