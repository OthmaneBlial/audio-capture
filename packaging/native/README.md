# Native Rust packages

The Rust release workflow packages one archive per target:

| Target | Archive | Status |
| --- | --- | --- |
| Linux x86_64 | `voice-transcriber-<version>-x86_64-unknown-linux-gnu.tar.gz` | Published in [`v1.2.0`](https://github.com/OthmaneBlial/audio-capture/releases/tag/v1.2.0); archive/checksum verified |
| macOS arm64 | `voice-transcriber-<version>-aarch64-apple-darwin.app.zip` | Published and locally exercised from the downloaded archive; unsigned/not notarized |
| Windows x86_64 | `voice-transcriber-<version>-x86_64-pc-windows-msvc.zip` | Published and checksum verified; unsigned and not runtime-tested on this Mac |

Each archive contains the native binary, `README.md`, `LICENSE`, and a
SHA-256 sidecar. The macOS archive also contains a minimal `.app` bundle with
the microphone usage description. The workflow does not claim signing,
notarization, installer registration, auto-update, or package-manager
publication.

## Local smoke checks

After extracting a matching target archive:

```text
voice-transcriber --version
voice-transcriber --doctor --json
voice-transcriber --list-devices --json
voice-transcriber --test-microphone --json
```

The first run may require the platform's microphone permission. Keep API keys,
raw recordings, and private transcripts out of release artifacts and support
reports. See [`docs/packaging/RELEASE-CHECKLIST.md`](../../docs/packaging/RELEASE-CHECKLIST.md)
for the complete release gate.
