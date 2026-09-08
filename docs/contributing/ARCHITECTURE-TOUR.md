# Rust architecture tour

The binary starts in `src/main.rs`. It parses the diagnostic flags first; a
normal launch creates the native egui application in `src/app.rs`.

## Core path

1. `src/config.rs` validates settings and persists them atomically in the
   platform user directory.
2. `src/audio.rs` discovers CPAL inputs, converts arbitrary host sample formats
   to mono PCM16, resamples to 16 kHz, and keeps a bounded frame queue.
3. `src/vad.rs` applies local WebRTC VAD, pre-roll, silence, and maximum-segment
   limits.
4. `src/provider.rs` admits completed segments only after key and consent
   checks, then sends in-memory WAV data to Groq from a bounded worker.
5. `src/transcript.rs` orders request results and owns the editable undo/redo
   document.
6. `src/exports.rs` writes confirmed text/Markdown destinations atomically;
   `src/history.rs` stores optional bounded text history.

The UI polls typed events and renders state; it does not own audio conversion,
HTTP parsing, persistence, or credential formatting. External work remains off
the egui frame loop.

## Review checklist

When changing a boundary, ask:

- Is the queue or response size bounded?
- Can a stale session update the current transcript?
- Does an error reveal credentials, response bodies, audio, or private paths?
- Is the behavior deterministic without a microphone, provider, or window?
- Does the documentation describe the current Rust implementation exactly?
