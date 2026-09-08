# Cross-platform compatibility evidence

Last reviewed: 8 September 2026

“Declared”, “automated”, “smoke-tested”, and “real-device verified” are separate
states. This table records only evidence observed for the native Rust build.

| Path | Evidence | Status |
| --- | --- | --- |
| macOS arm64 | Local release build, CLI diagnostics, device discovery, and a real three-second microphone stream | Development smoke-tested |
| Linux x86_64 | Native build/test job in `.github/workflows/rust.yml` | CI path; physical desktop/audio report pending |
| Windows x86_64 | Native MSVC build/test job in `.github/workflows/rust.yml` | CI path; physical desktop/audio report pending |
| Groq cloud provider | Consent gate, bounded worker, WAV contract, and normalized-error tests | Contract-tested; user-key request pending |
| Other architectures | No configured release artifact | Not supported by the current release workflow |

## Reproduction protocol

1. Record app version, OS, desktop/session, architecture, audio backend,
   installation path, and microphone connection type.
2. Run `voice-transcriber --doctor --json` and review it locally.
3. Run `--list-devices --json`, select an input, and run
   `--test-microphone --json`.
4. For a tester-owned Groq key, verify one short transcript, stop/flush,
   copy, explicit export, history-off restart, and failure behavior.
5. Publish only sanitized diagnostics. Never publish keys, audio, transcript
   content, serials, private paths, or unrelated environment variables.

Use the repository's compatibility issue form. A report enters the supported
table only when the exact path is reproducible and the cleanup/privacy steps
pass.
