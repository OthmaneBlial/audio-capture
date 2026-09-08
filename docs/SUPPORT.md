# Supported environments

The support boundary distinguishes observed evidence from a build that is only
expected to work.

| Surface | Current evidence | Status |
| --- | --- | --- |
| macOS arm64 | `cargo check`, Rust tests, CLI device discovery, and a real three-second microphone stream on this Mac | Development smoke-tested |
| Linux x86_64 | Rust GitHub Actions build/test matrix is configured | Runtime and hardware report pending |
| Windows x86_64 | Rust GitHub Actions MSVC build matrix is configured | Runtime and hardware report pending |
| egui desktop UI | Native binary compiles and launches locally on macOS | Full interaction review pending |
| CPAL audio | Local macOS inputs enumerated and frames received | macOS path smoke-tested; other backends pending |
| Groq provider | Consent/key gate, WAV encoding, queue, ordering, and error tests | Contract-tested; live provider gate pending |
| Release packaging | Published [`v1.2.0`](https://github.com/OthmaneBlial/audio-capture/releases/tag/v1.2.0); all three archives and checksums verified, downloaded macOS app reports `1.2.0` and passes `--doctor --json` | Asset gate passed; Linux/Windows binaries not executed on this Mac |

“Pending” means an implementation path exists but exact-environment evidence is
missing. It must not become a support claim in release notes until the matching
build and runtime checks pass.

## Local compatibility report

```bash
voice-transcriber --doctor --json
voice-transcriber --list-devices --json
voice-transcriber --test-microphone --json
```

Include the operating system, desktop/session, audio backend, command output,
and visible error. Do not include API keys, recordings, transcripts, full
configuration files, or personal paths.

Security reports belong in [SECURITY.md](../SECURITY.md) and should remain
private until a coordinated fix is available.
