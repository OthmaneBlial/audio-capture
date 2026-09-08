# Native Rust packages

The Rust release workflow packages one archive per target:

| Target | Archive | Current status |
| --- | --- | --- |
| Linux x86_64 | `voice-transcriber-<version>-x86_64-unknown-linux-gnu.tar.gz` | Workflow definition only; no Rust release published |
| macOS arm64 | `voice-transcriber-<version>-aarch64-apple-darwin.app.zip` | Workflow definition only; unsigned and not notarized |
| Windows x86_64 | `voice-transcriber-<version>-x86_64-pc-windows-msvc.zip` | Workflow definition only; unsigned |

Each archive contains the binary, `README.md`, `LICENSE`, and a SHA-256 file.
The macOS archive also contains a minimal `.app` bundle with the microphone
usage description. The workflow does not claim code signing, notarization,
installer registration, auto-update, or package-manager publication.

## Local smoke checks

After extracting a matching target archive:

```text
voice-transcriber --doctor --json
voice-transcriber --list-devices --json
voice-transcriber --test-microphone --json
```

The first run may require the platform's microphone permission. Keep API keys,
raw recordings, and private transcripts out of release artifacts and support
reports.

The remaining packaging gates are tracked in [`ROADMAP.md`](../../ROADMAP.md):
real Linux/Windows sessions, macOS GUI interaction, signing/notarization,
installer UX, release checksums and provenance, and a final video captured from
the finished product.
