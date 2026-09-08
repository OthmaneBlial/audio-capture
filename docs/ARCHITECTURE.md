# Architecture

The active rewrite is one native Rust process with a UI adapter at the edge.
The core modules do not import egui, open a window, or require a real
microphone, which keeps safety and ordering tests deterministic.

```text
egui desktop adapter (`src/app.rs`)
  ├── microphone capture (`src/audio.rs`, CPAL)
  ├── voice activity detection (`src/vad.rs`, WebRTC VAD)
  ├── provider boundary (`src/provider.rs`, Groq worker)
  ├── review document (`src/transcript.rs`)
  ├── atomic exports (`src/exports.rs`)
  ├── opt-in text history (`src/history.rs`)
  └── validated settings (`src/config.rs`)
```

## Data flow

1. `AudioCapture` enumerates the current host inputs, opens the selected
   default configuration, converts its channels and sample rate to mono 16 kHz
   PCM16, and puts complete 30 ms frames into a bounded queue.
2. `VoiceActivityDetector` consumes those frames locally. It keeps a short
   rolling pre-roll, closes a segment after sustained silence, and enforces
   minimum and maximum speech durations.
3. `GroqProvider` admits only completed segments after both a plausible key and
   explicit cloud consent are present. A worker builds an in-memory WAV request,
   applies a timeout, and emits metadata-only request events.
4. The app maps events to ordered segment states. Complete text is rebuilt in
   sequence order in the editable transcript; pending and failed segments stay
   visible for review.
5. Copy, export, and optional text-only history are explicit user actions.
   Raw microphone data is never written by the Rust path.

## Reliability boundaries

- The audio queue is bounded to 64 frames. When it saturates, the oldest frame
  is discarded and a counter remains available to the UI/diagnostics.
- Provider admission is bounded to four jobs. Queue overflow is a visible,
  actionable error rather than an unbounded thread or memory backlog.
- Device identities are opaque SHA-256-derived values; a stale saved identity
  fails closed instead of silently opening a reused enumeration index.
- Provider errors contain status categories and remediation text, never a key,
  response body, or raw audio.
- Configuration, history, and exports use size limits, schema checks where
  applicable, symlink refusal, and atomic replacement.
- The diagnostic CLI is local-only. A real microphone test reports frame count
  and signal level but discards the captured frames.

## Configuration boundary

Settings follow `defaults < local config < GROQ_API_KEY environment override`.
The persisted key is owner-local configuration; the environment key takes
precedence and is not copied into the file. The cloud consent checkbox is
stored separately from key presence, so adding a key alone never silently
enables upload.

The Python/GTK implementation and its local whisper.cpp experiment remain in
the repository as migration material. They are not part of the Rust runtime
path and should not be used as evidence for Rust platform support.
