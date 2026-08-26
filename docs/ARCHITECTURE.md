# Architecture

Voice Transcriber has one desktop process and four intentionally narrow responsibilities:

```text
GTK window
  ├── controller (`main.py`)
  ├── microphone capture (`audio/capture.py`)
  ├── voice activity detection (`audio/vad.py`)
  ├── Groq boundary (`transcription/groq_service.py`)
  ├── edit/request state (`transcript.py`)
  ├── structured exports (`exports.py`)
  └── opt-in local history (`history.py`)
```

## Data flow

1. `AudioCapture` uses the system default or a saved microphone index, reads 30 ms 16 kHz mono PCM frames into a fixed-size queue, and emits a rate-limited local signal level for GTK.
2. `VoiceActivityDetector` keeps a short rolling buffer and emits a completed segment after silence or the maximum segment duration.
3. `GroqTranscriptionService` converts a valid segment to an in-memory WAV file and submits it to a two-worker pool.
4. Bounded request IDs expose pending/complete/error state without storing audio or text in the tracker.
5. Results return to GTK through its idle queue and are appended to the editable transcript.

No audio recording is persisted by the application. Segments are sent to Groq only when speech has been detected. The transcript remains in the GTK buffer until the user clears, copies, exports, or closes it with explicitly enabled local text history.

## Reliability boundaries

- The microphone queue drops oldest frames if processing falls behind, preserving real-time behavior instead of growing memory indefinitely.
- Input discovery opens PortAudio only on demand and releases it immediately; a saved unavailable device remains visible so the user can correct it rather than silently falling back.
- The input meter is derived from an in-memory PCM RMS value and is never written to disk or sent to Groq.
- The API boundary rejects malformed, empty, and oversized PCM data.
- Only a small number of API requests may be pending; overflow becomes a visible, actionable message.
- The small standard-library HTTP transport has a fixed timeout and no hidden SDK retry queue, so the app's own bound remains predictable.
- Stop first signals capture, waits briefly for the processor, then flushes a final valid segment.

## Configuration boundary

Settings use the precedence `defaults < config file < environment`. The configuration file is atomically replaced and set to `0600`; its parent directory is set to `0700` where supported. `GROQ_API_KEY` overrides a stored key and is not copied into settings when the environment value is active. Microphone choice is a local saved index, with `--device INDEX` taking precedence for one launch.

History uses a separate schema-versioned owner-only file. Unknown future
schemas fail closed instead of being overwritten. Expiry is enforced on read
and write; one entry, every entry, or all sandbox data can be deleted without
touching explicit exports.
