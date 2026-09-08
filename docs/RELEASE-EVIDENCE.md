# Release evidence register

Last reviewed: 8 September 2026

This register separates evidence for the current native Rust checkout from
gates that still require a real desktop, provider account, or downloaded
release asset. It is a record of observed results, not release approval.

## Source and local checks

| Surface | Exact evidence | Scope and limit |
| --- | --- | --- |
| Runtime language | `git ls-files` contains Rust sources under `src/`; no tracked Python source or Python build metadata remains | GitHub language statistics can lag after a rewrite |
| Deterministic suite | `cargo test --locked --all-targets` passes 23 Rust tests in the current checkout | No physical Linux/Windows desktop or live provider request |
| Static quality | `cargo fmt --all -- --check` and `cargo clippy --locked --all-targets -- -D warnings` pass locally | Does not replace platform runtime testing |
| Dependency policy | `cargo deny check advisories licenses bans sources` is part of the release gate | Advisory databases and network availability can change |
| CLI contracts | `--doctor --json`, `--list-devices --json`, and `--test-microphone --json` run locally on macOS | Hardware evidence is specific to this Mac |
| Real microphone | Three-second local smoke test received PCM frames and reported a peak level, then discarded them | Does not prove speech recognition or another OS/backend |

## Packaging and release gates

The native release workflow builds Linux x86_64, macOS arm64, and Windows
x86_64 archives, writes SHA-256 checksums, and publishes them from a version
tag. A tag or a successful build alone is not evidence that a downloaded binary
was installed and exercised.

### Observed `v1.2.0` release

| Field | Observed value |
| --- | --- |
| Tag and source commit | [`v1.2.0`](https://github.com/OthmaneBlial/audio-capture/releases/tag/v1.2.0) at `3f4cbd7e3fada3def14ea1fce23105d394d26358` |
| Release workflow | [Rust release run 34266286266](https://github.com/OthmaneBlial/audio-capture/actions/runs/34266286266) — completed successfully |
| Linux asset | `voice-transcriber-1.2.0-x86_64-unknown-linux-gnu.tar.gz` — `de3ffbd047f86af96bc310937f0ae35e50ece0fc507cb9f0fd88604b0cbc8210` |
| macOS asset | `voice-transcriber-1.2.0-aarch64-apple-darwin.app.zip` — `9ebeee1f067b5de51469326e5889bdf36f444a8cccaeb0c2239665595c0867db` |
| Windows asset | `voice-transcriber-1.2.0-x86_64-pc-windows-msvc.zip` — `7fbcbcf8089f0b44ca33637c8dff160b7748a1bbd45ec97652d6c332a9c9a1c0` |
| Downloaded macOS check | `.app` contains `NSMicrophoneUsageDescription`; arm64 binary reports `voice-transcriber 1.2.0` and `--doctor --json` returns `ok: true` with two local input devices |
| Downloaded Linux/Windows check | Archive contents and checksums inspected; binaries were not executed on this macOS host |

Before calling a release ready, record:

- the exact tag, commit, workflow URL, archive names, and checksums;
- a clean extraction and `--version`/`--doctor` check for every available host;
- the macOS microphone smoke test and a Linux/Windows hardware report when
  available;
- one tester-owned Groq transcript and translation request, including failure
  handling, without retaining the key, audio, or transcript;
- the final README links, release notes, and screenshots.

## Open acceptance gates

- A clean downloaded-asset install/update/removal check beyond the verified
  extraction and macOS diagnostic run above.
- Full manual UI review of start/stop, settings, device refresh, transcript
  ordering, copy, export, history, and error states.
- One real provider request with a disposable user-managed key.
- Linux and Windows runtime reports for their audio backends.
- A genuine product demonstration video captured after all preceding gates.

## Evidence hygiene

Record the exact commit, workflow URL, package filename/checksum, environment,
date, command or scenario, and result. Keep keys, audio, transcript content,
device serials, private paths, and full environment dumps out of this file and
public issues. “Not recorded”, “failed”, “skipped”, and “passed” are different
states.
