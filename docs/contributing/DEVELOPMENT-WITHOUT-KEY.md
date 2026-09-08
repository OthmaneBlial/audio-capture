# Develop without an API key

The Rust core is designed to be testable without Groq, a microphone, or a
desktop session.

## Fast deterministic loop

```bash
cargo fmt --all -- --check
cargo test --all-targets
cargo clippy --all-targets -- -D warnings
```

These checks exercise configuration validation, bounded history and exports,
transcript ordering, VAD framing, audio conversion, provider admission, and WAV
encoding without contacting a network provider.

## Inspect local audio safely

```bash
cargo run -- --doctor --json
cargo run -- --list-devices --json
cargo run -- --test-microphone --json
```

The microphone test opens the default input for three seconds, reports frame
count and peak level, then discards the frames. It does not need a key and does
not submit anything.

## When a real provider boundary is required

Use a disposable key that you control only for the manual Groq gate. Never put
it in a command copied into an issue, test fixture, screenshot, or commit.
Enable the cloud-boundary checkbox in Settings, speak a short phrase, review
the result, and record only the status/error category and platform. Do not
attach audio, request bodies, keys, or private transcripts.

The legacy Python commands remain available while migration work is underway,
but new Rust changes must be validated with the commands above.
