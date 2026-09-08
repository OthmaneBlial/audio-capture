# Architecture

Voice Transcriber is one native Rust desktop process. The egui adapter is at
the edge; capture, segmentation, provider admission, persistence, and export
are kept in separate modules so their contracts can be tested without a window,
microphone, or API key.

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

1. `AudioCapture` enumerates host inputs, opens the selected default
   configuration, converts samples to mono 16 kHz PCM16, and publishes complete
   30 ms frames through a bounded queue.
2. `VoiceActivityDetector` consumes those frames locally. It keeps a short
   pre-roll, closes a segment after sustained silence, and enforces minimum and
   maximum speech durations.
3. `GroqProvider` admits only completed segments after a plausible key and
   explicit cloud consent are present. A worker builds an in-memory WAV request,
   applies a timeout, and emits metadata-only events.
4. The app maps events to ordered segment states. Completed text is rebuilt in
   sequence order in the editable transcript; pending and failed segments stay
   visible for review.
5. Copy, export, and optional text-only history are explicit user actions. Raw
   microphone data is never written by the Rust application.

## Reliability boundaries

- The audio queue is bounded to 64 frames. When it saturates, the oldest frame
  is discarded and the drop count remains visible to diagnostics/UI.
- Provider admission is bounded to four jobs. Overflow is a visible error,
  rather than an unbounded thread or memory backlog.
- Device identities are opaque SHA-256-derived values. A stale saved identity
  fails closed instead of silently opening a different enumeration index.
- Provider errors contain a category and remediation text, never a key,
  response body, or raw audio.
- Configuration, history, and exports enforce size limits, refuse symlinks where
  appropriate, and use atomic replacement.
- The diagnostic CLI is local-only. A real microphone test reports frame count
  and signal level, then discards the captured frames.

## Configuration boundary

Settings resolve as `defaults < local config < GROQ_API_KEY` environment
override. The persisted key is owner-local configuration; an environment key
takes precedence and is not copied into the file. Cloud consent is stored
separately and adding a key alone never enables upload.

The supported runtime path is Groq cloud transcription. The configuration enum
keeps room for a future local provider, but the current desktop flow does not
advertise or execute an offline provider. Documentation and release claims
must follow the implemented path.
