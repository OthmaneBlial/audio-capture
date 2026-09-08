# Supported environments

The support boundary distinguishes observed evidence from a build that is only
expected to work. The table below describes the active Rust rewrite; the old
Python/GTK v1.0 package has a separate historical boundary in its release
documentation.

## Rust rewrite status

| Surface | Current evidence | Status |
| --- | --- | --- |
| macOS arm64 | Local `cargo check`, tests, CLI device discovery, and a real three-second microphone stream on this Mac | Development smoke-tested |
| Linux x86_64 | GitHub Actions build/test matrix configured; physical desktop/audio session not yet reported | Pending first green run and hardware report |
| Windows x86_64 | GitHub Actions MSVC build matrix configured; no local Windows session | Pending first green run and hardware report |
| egui desktop UI | Native binary compiles locally | Manual interaction and screenshots still required |
| CPAL audio | Three macOS input devices enumerated; 94 frames received from the default Jabra stream | macOS path smoke-tested; other backends pending |
| Groq provider | Consent/key gate, WAV contract, queue and error tests; no user-key request in this checkout | Contract-tested; live provider gate pending |
| Packaging | No Rust release asset or installer | Not published |

“Pending” means the project has an implementation path but lacks reproducible
evidence for the exact environment. It must not be presented as a support claim
in release notes until the corresponding build and runtime checks pass.

## Local compatibility report

For a privacy-safe report, run:

```bash
voice-transcriber --doctor --json
voice-transcriber --list-devices --json
voice-transcriber --test-microphone --json
```

Include the operating system, desktop session, audio backend, command output,
and visible error. Do not include API keys, recordings, transcripts, full
configuration files, or personal paths.

## Historical Python package

The existing v1.0.0 x86_64 Flatpak is a Python/GTK Linux artifact. Its support
claims, checksum, and smoke-test evidence remain in
[`docs/RELEASE-EVIDENCE.md`](RELEASE-EVIDENCE.md) and
[`docs/packaging/FLATPAK.md`](packaging/FLATPAK.md). Those documents do not
transfer support to the Rust rewrite.

Security reports belong in [SECURITY.md](../SECURITY.md) and should remain
private until a coordinated fix is available.
