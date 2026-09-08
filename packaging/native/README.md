# Native Rust packages

The Rust release workflow packages one archive per target:

| Target | Archive | Status |
| --- | --- | --- |
| Linux x86_64 | `voice-transcriber-<version>-x86_64-unknown-linux-gnu.tar.gz` | Built by the tag workflow |
| macOS arm64 | `voice-transcriber-<version>-aarch64-apple-darwin.app.zip` | Unsigned and not notarized |
| Windows x86_64 | `voice-transcriber-<version>-x86_64-pc-windows-msvc.zip` | Unsigned |

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
