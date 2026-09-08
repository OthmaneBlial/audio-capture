# Deterministic audio tests

Audio tests should validate conversion and framing without opening a host
microphone. The Rust unit tests in `src/audio.rs` and `src/vad.rs` use generated
sample vectors and bounded channels for this purpose.

## Good fixture properties

- Keep sample vectors short and deterministic.
- Exercise mono and multi-channel input, signed and unsigned host formats, and
  arbitrary callback sizes.
- Assert the output sample rate, channel count, frame length, clipping, and
  queue-bound behavior.
- Test device errors and queue saturation through injected results rather than
  requiring a particular OS audio backend.

## When hardware is needed

Use `cargo run -- --test-microphone --json` for a local three-second smoke test.
It reports only the selected device label, frame count, peak level, and a
normalized error; it discards all captured frames. Hardware results are
platform-specific and must not replace deterministic unit tests.
