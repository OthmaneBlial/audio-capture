# Packaging decision: native Rust archives

## Decision

The supported packaging path is the native Rust release workflow. It publishes
one archive for Linux x86_64, macOS arm64, and Windows x86_64 from the exact
version tag. The project does not currently publish a sandboxed Linux package,
installer, package-manager formula, or automatic updater.

## Why native archives first

- The application already builds as one self-contained Rust desktop binary.
- The same archive contract can be inspected on all three release targets.
- A checksum-backed archive is easier to reproduce and validate while the
  project collects real microphone and desktop evidence.
- Platform-specific signing, notarization, installers, and package-manager
  publication can be added after the binary behavior is stable.

## Artifact contract

| Target | Archive |
| --- | --- |
| Linux x86_64 | `voice-transcriber-<version>-x86_64-unknown-linux-gnu.tar.gz` |
| macOS arm64 | `voice-transcriber-<version>-aarch64-apple-darwin.app.zip` |
| Windows x86_64 | `voice-transcriber-<version>-x86_64-pc-windows-msvc.zip` |

Every archive contains the native binary, `README.md`, and `LICENSE`; every
archive has a SHA-256 sidecar. The macOS archive includes a minimal `.app` with
`NSMicrophoneUsageDescription`.

## Required gates

1. Run format, locked tests, clippy, and dependency policy checks.
2. Build each target on its native GitHub Actions runner.
3. Verify archive names, checksums, version metadata, and release notes.
4. Extract the downloaded asset on a clean profile and run the diagnostics.
5. Collect target-specific microphone/UI/provider evidence before expanding
   the support claim.

Signing, notarization, installers, and distribution services are future phases,
not implied by a green archive build.
