# Contributing

Thanks for helping make Voice Transcriber easier to trust and use.

Start with the public [contributor map](docs/contributing/README.md). It links
the architecture tour, credential-free development loop, deterministic audio
test guidance, UI and packaging guides, and the complete issue-to-PR path.

## Prerequisites

- Rust 1.95 or newer (`rustup` recommended)
- On macOS, Xcode Command Line Tools
- On Linux, the ALSA and windowing development headers required by CPAL and
  egui on your distribution
- On Windows, the MSVC Rust toolchain and Visual Studio build tools

## Setup and verification

```bash
git clone https://github.com/OthmaneBlial/audio-capture.git
cd audio-capture
cargo fmt --all -- --check
cargo test --locked --all-targets
cargo clippy --locked --all-targets -- -D warnings
cargo deny check advisories licenses bans sources
```

The core workflow is capture → VAD → bounded transcription queue → provider →
editable egui desk. Keep native microphone and network work out of deterministic
unit tests; use the existing bounded contracts so contributors can test
without hardware or credentials.

For the shortest no-key loop, follow
[Development without a key](docs/contributing/DEVELOPMENT-WITHOUT-KEY.md).

## Pull requests

- Keep a pull request focused and explain the user-facing behavior it protects.
- Add or update tests for reliability, configuration, security, or parsing changes.
- Do not commit `.env`, API keys, recordings, exported transcripts, or generated environment folders.
- Run the Rust checks above and note any hardware-only verification you could
  not perform.
- Use clear, imperative commit messages such as `fix: bound pending transcription requests`.

For vulnerabilities, use the private process in [SECURITY.md](SECURITY.md), not a pull request or public issue.
