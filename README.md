# Voice Transcriber

[![Rust CI](https://github.com/OthmaneBlial/audio-capture/actions/workflows/rust.yml/badge.svg)](https://github.com/OthmaneBlial/audio-capture/actions/workflows/rust.yml)
[![Legacy Python CI](https://github.com/OthmaneBlial/audio-capture/actions/workflows/ci.yml/badge.svg)](https://github.com/OthmaneBlial/audio-capture/actions/workflows/ci.yml)
[![MIT license](https://img.shields.io/github/license/OthmaneBlial/audio-capture)](LICENSE)

**A review-first dictation desk for Linux, macOS, and Windows.** Speak a draft,
inspect the ordered transcript, edit it, then decide what to copy or export.

The repository is in the middle of a native Rust rewrite. The current `main`
branch contains the portable core, the CPAL microphone adapter, the explicit
Groq provider boundary, a native egui desktop interface, and diagnostic
commands. There is **no Rust v1.1 release or downloadable Rust binary yet**;
the release page still contains the older Python/GTK v1.0 Linux package.

## Why this exists

Most voice-typing tools inject words into whichever application currently has
focus. Voice Transcriber gives the words a checkpoint first, which fits prompts,
emails, tickets, notes, and other drafts that need review before they are shared.

```text
microphone -> local PCM conversion -> local VAD -> explicit provider -> edit -> copy/export
```

The default provider path uses Groq Whisper. Silence detection, resampling,
the input meter, ordering, and the review document stay local. Completed speech
segments cross the cloud boundary only after a key is configured and the user
confirms that boundary in Settings.

## Current Rust surface

- Native egui desktop window with a dark, keyboard-friendly review workspace.
- CPAL input discovery on the host backend, opaque device identities, bounded
  frame queue, level meter, mono downmix, and resampling to 16 kHz PCM16.
- Local WebRTC VAD with minimum speech, silence, and maximum segment limits.
- Groq worker with a bounded request queue, WAV encoding, translation support,
  ordered request events, and credential-safe error messages.
- Editable transcript with segment states, undo/redo, clear, clipboard copy,
  text/Markdown export, and opt-in bounded text-only history.
- Non-network diagnostics that can be scripted in CI or support reports:
  `--doctor`, `--list-devices`, `--check-config`, and a three-second real
  `--test-microphone` smoke test.

The Rust GUI has been compiled locally on macOS arm64. The real microphone
smoke test has opened the default Jabra input and received PCM frames on this
Mac. Linux and Windows builds are covered by the Rust GitHub Actions matrix;
their first green run is still the evidence gate for those targets. Manual GUI
interaction, provider requests with a user key, and packaged Rust releases are
deliberately not described as complete until they are tested.

## Run from source

Install Rust 1.95 or newer. On macOS, install Xcode Command Line Tools. On
Windows, install the MSVC Rust toolchain and its Visual Studio build tools. On
Linux, install the development headers for the audio backend and the windowing
stack used by your distribution (usually ALSA/PipeWire plus X11 or Wayland).

```bash
git clone https://github.com/OthmaneBlial/audio-capture.git
cd audio-capture
cargo run -- --doctor
cargo run -- --list-devices
cargo run
```

The first GUI launch may require the operating system's microphone permission.
Use the **Test microphone** button before enabling cloud transcription.

Useful scripted checks:

```bash
cargo test --all-targets
cargo clippy --all-targets -- -D warnings
cargo run -- --check-config --json
cargo run -- --test-microphone --json
```

The diagnostic commands never send audio to Groq. `--doctor` checks local
configuration and input-device availability; it does not perform a provider
probe.

## Configure transcription

The effective key comes from `GROQ_API_KEY` when present, otherwise from the
local Settings field. The key is never printed by the application or included
in provider events.

```bash
export GROQ_API_KEY="your-key"
cargo run
```

In Settings, select a language or automatic detection, optionally enable
English translation, and explicitly confirm that completed speech is sent to
Groq over HTTPS. Without both consent and a plausible key, **Start listening**
stays blocked; **Test microphone** remains local.

## Data boundary

| Data | Rust behavior |
| --- | --- |
| Microphone frames | Bounded in memory; never written as audio files |
| VAD and input level | Computed locally |
| Completed speech segment | Encoded in memory and sent to Groq only after consent |
| Transcript | Editable in the current desk; copy/export is explicit |
| Optional history | Text only, off by default, bounded and retention-limited |
| API key | Environment or local configuration; excluded from logs/events |
| Analytics | None implemented |

Provider-side processing follows the provider account and current policy. See
[`docs/PRIVACY.md`](docs/PRIVACY.md), [`docs/DATA-FLOW.md`](docs/DATA-FLOW.md),
and [`docs/THREAT-MODEL.md`](docs/THREAT-MODEL.md) before using sensitive audio.

## Architecture

```text
src/config.rs       validated settings and atomic persistence
src/audio.rs        CPAL devices, conversion, bounded PCM frame queue
src/vad.rs          local WebRTC VAD segmentation
src/provider.rs     consent gate, bounded Groq worker, safe events
src/transcript.rs   ordered review document and undo/redo
src/exports.rs      atomic text/Markdown exports
src/history.rs      opt-in bounded text history
src/app.rs          egui desktop adapter
src/main.rs         GUI entry point and diagnostic CLI
```

The core modules are intentionally independent of egui and microphone access,
so storage, ordering, safety limits, and provider contracts can be tested on a
machine without a key or an audio device.

## Releases and packaging

Rust binaries are not published yet. The repository still contains the
transitional Python/GTK implementation and its historical x86_64 Flatpak
workflow; that package is labeled as the old v1.0 product and is not evidence
that the Rust rewrite has been released. The migration roadmap covers parity,
native packaging, signed release assets, installation documentation, and the
real product demo video that must be recorded only after those gates pass.

See [`ROADMAP.md`](ROADMAP.md) for the implementation order and acceptance
criteria. Do not use an old release asset as a Rust build artifact.

## Contributing

Start with `cargo test --all-targets`, `cargo fmt --all -- --check`, and
`cargo clippy --all-targets -- -D warnings`. Changes that touch audio or the
provider boundary should include deterministic tests and a note about the
platform evidence they require. Never commit API keys, raw recordings,
personal configuration files, or screenshots containing sensitive text.

Bug reports and compatibility reports should include the output of
`voice-transcriber --doctor --json` and the host OS/audio backend, without
including credentials or recordings. Security reports belong in
[`SECURITY.md`](SECURITY.md), not in a public issue.

Released under the [MIT License](LICENSE).
