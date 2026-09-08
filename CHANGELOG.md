# Changelog

All notable changes to Voice Transcriber are documented here. Version `1.2.0`
is the first release of the native Rust desktop application.

## [1.2.0] - 2026-09-08

### Added

- Native Rust desktop application built with egui.
- Portable capture core with CPAL input discovery, mono downmix, sample-format
  conversion, streaming resampling to 16 kHz, and a bounded frame queue.
- Local WebRTC VAD with pre-roll, minimum speech, silence, and maximum-segment
  limits.
- Groq transcription worker with explicit consent/key admission, bounded jobs,
  in-memory WAV encoding, timeouts, request ordering, translation support, and
  normalized errors.
- Editable transcript with ordered segment states, undo/redo, clear, clipboard
  copy, text/Markdown/timestamped exports, and optional bounded text history.
- Local diagnostic commands: `--doctor`, `--list-devices`, `--check-config`,
  and a three-second `--test-microphone` smoke test with JSON output.
- Native release workflow for Linux x86_64, macOS arm64, and Windows x86_64
  archives with SHA-256 sidecars.

### Changed

- Replaced the previous desktop runtime and build system with a Rust-only
  source tree and Cargo lockfile.
- Redesigned the desktop interface around a focused dark review workspace with
  clear capture state, provider boundary, settings, transcript, and export
  actions.
- Added session generations so delayed provider results cannot repopulate a
  cleared or restarted transcript.
- Updated contributor, privacy, support, packaging, site, and issue-template
  documentation to describe the implemented Rust path only.
- Closed the old migration issue and dependency-update queue; new tasks must be
  written against the current Rust modules.

### Validation

- `cargo fmt --all -- --check` passes locally.
- `cargo test --locked --all-targets` passes 23 deterministic Rust tests locally.
- `cargo clippy --locked --all-targets -- -D warnings` passes locally.
- `cargo build --locked --release` and local CLI diagnostics pass on macOS arm64.
- A real three-second macOS microphone smoke test received PCM frames and
  discarded them; no live Groq request is implied by that check.

### Known limits

- The supported transcription path requires a user-managed Groq key and cloud
  consent; an offline provider is not included in this release.
- Linux and Windows builds are automated release targets, but their physical
  microphone and desktop runtime evidence remains target-specific.
- Release archives are unsigned/notarized and do not install package-manager
  metadata or automatic updates.
- Linux and Windows binaries have not been runtime-tested on this Mac, and a
  live Groq request remains unverified.
- The final product demonstration video is intentionally produced only after
  the remaining runtime/provider gates are validated.

## Historical releases

Pre-`1.2.0` tags belong to the retired implementation and are retained in Git
history for provenance only. They are not compatible with the current Rust
source tree and must not be used as current installation instructions.
