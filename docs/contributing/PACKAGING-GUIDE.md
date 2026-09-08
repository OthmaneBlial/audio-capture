# Native packaging guide

The supported release path is the Rust workflow in
[`.github/workflows/rust-release.yml`](../../.github/workflows/rust-release.yml).
It builds one archive per target and emits a SHA-256 checksum beside each
archive.

| Target | Artifact | Packaging details |
| --- | --- | --- |
| Linux x86_64 | `voice-transcriber-<version>-x86_64-unknown-linux-gnu.tar.gz` | Binary, README, and MIT license |
| macOS arm64 | `voice-transcriber-<version>-aarch64-apple-darwin.app.zip` | Minimal `.app`, microphone usage description, README, and license |
| Windows x86_64 | `voice-transcriber-<version>-x86_64-pc-windows-msvc.zip` | Binary, README, and MIT license |

## Invariants

- The Cargo package version, tag, changelog, AppStream metadata, archive name,
  and release title must agree.
- Archives contain only the native Rust binary and reviewed documentation.
- Checksums are generated from the exact uploaded bytes.
- The workflow does not claim signing, notarization, installer registration,
  auto-update, package-manager publication, or hardware support.
- A CI build is separate from a clean extraction and runtime check.

## Before a packaging change

```bash
cargo fmt --all -- --check
cargo test --locked --all-targets
cargo clippy --locked --all-targets -- -D warnings
cargo build --locked --release
```

For a downloaded archive, extract it into a clean directory and run
`--version`, `--doctor --json`, `--list-devices --json`, and
`--test-microphone --json` where a microphone is available. Do not include keys,
recordings, transcripts, private paths, or full environment dumps in release
evidence.
