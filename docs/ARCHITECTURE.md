# Architecture

Voice Transcriber has one desktop process and four intentionally narrow responsibilities:

```text
GTK window
  ├── controller (`main.py`)
  ├── microphone capture (`audio/capture.py`)
  ├── voice activity detection (`audio/vad.py`)
  ├── provider contract (`transcription/provider.py`)
  │   ├── Groq cloud (`transcription/groq_service.py`)
  │   └── experimental local (`transcription/local_whisper.py`)
  ├── edit/request state (`transcript.py`)
  ├── structured exports (`exports.py`)
  └── opt-in local history (`history.py`)
```

## Data flow

1. `AudioCapture` uses the system default or a saved microphone index, reads 30 ms 16 kHz mono PCM frames into a fixed-size queue, and emits a rate-limited local signal level for GTK.
2. `VoiceActivityDetector` keeps a short rolling buffer and emits a completed segment after silence or the maximum segment duration.
3. The selected provider receives a valid segment through its explicit
   capability and data-boundary contract. Groq converts it to an in-memory WAV
   request in a two-worker pool. Experimental local mode wraps it as WAV and
   passes a Linux memory-backed descriptor to one user-supplied whisper.cpp
   process at a time.
4. Bounded request IDs expose pending/complete/error state without storing audio or text in the tracker.
5. Results return to GTK through its idle queue and are appended to the editable transcript.

No audio recording is persisted by the application. In Groq mode, segments are
sent only after speech has been detected. In experimental local mode, the app
creates no raw-audio path and terminates active CLI work during shutdown. The
transcript remains in GTK until clear/copy/export or explicitly enabled local
text history.

## Reliability boundaries

- The microphone queue drops oldest frames if processing falls behind, preserving real-time behavior instead of growing memory indefinitely.
- Input discovery opens PortAudio only on demand and releases it immediately; a saved unavailable device remains visible so the user can correct it rather than silently falling back.
- The input meter is derived from an in-memory PCM RMS value and is never written to disk or sent to Groq.
- The API boundary rejects malformed, empty, and oversized PCM data.
- Each provider has a small bounded queue; overflow becomes a visible,
  normalized, actionable message.
- The small standard-library HTTP transport has a fixed timeout and no hidden SDK retry queue, so the app's own bound remains predictable.
- Stop first signals capture, waits briefly for the processor, then flushes a final valid segment.

## Configuration boundary

Settings use the precedence `defaults < config file < environment`. The
configuration file is atomically replaced and set to `0600`; its parent
directory is set to `0700` where supported. `GROQ_API_KEY` overrides a stored
key and is not copied into settings when the environment value is active. The
local executable/model paths are activated only by the explicit source-session
feature flag and never exposed by diagnostics. Microphone choice is a local
saved index, with `--device INDEX` taking precedence for one launch.

History uses a separate schema-versioned owner-only file. Unknown future
schemas fail closed instead of being overwritten. Expiry is enforced on read
and write; one entry, every entry, or all sandbox data can be deleted without
touching explicit exports.
