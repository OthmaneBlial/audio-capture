# Architecture tour for contributors

Voice Transcriber is one GTK process with deliberately narrow boundaries. The
shortest mental model is:

```text
microphone -> bounded frames -> local VAD -> selected provider -> editable GTK text
```

## Follow one spoken segment

1. `audio/capture.py` discovers an input and reads 30 ms, 16 kHz mono PCM
   frames. Its queue is bounded and may drop old frames to preserve real-time
   behavior.
2. `audio/vad.py` decides locally whether frames contain speech. It emits one
   completed segment after silence or the maximum duration.
3. `transcription/provider.py` defines capabilities, limits, cancellation,
   normalized failures, and the data-boundary wording shared by providers.
4. `transcription/groq_service.py` sends the completed segment through a small
   bounded cloud worker pool. `transcription/local_whisper.py` is an explicit,
   source-only experimental implementation that passes WAV through a Linux
   memory descriptor to a user-supplied executable.
5. `main.py` returns results to GTK's main loop. `transcript.py` owns editable
   text and request states; `exports.py` and `history.py` own explicit text
   persistence.

## Where a change belongs

- Capture, device selection, and local signal level belong under `audio/`.
- Provider-specific HTTP or process details stay behind the provider contract.
- UI widgets and layouts belong under `ui/`; orchestration belongs in
  `main.py`, not in a widget.
- Exported files and opt-in history are separate persistence contracts. Do not
  create a new audio-persistence path.
- Configuration uses `defaults < config file < environment`; diagnostics must
  disclose readiness, never a secret or a private local path.

## Reliability and privacy invariants

- Keep capture and provider queues bounded.
- Do not block GTK's main loop with microphone, network, or local-model work.
- Do not log response bodies, credentials, transcript text, audio, or local
  model paths.
- Do not imply that Groq mode is offline or that the application controls
  provider-side retention.
- Keep history disabled by default and exports deliberate.

Read the deeper [architecture note](../ARCHITECTURE.md), [data-flow contract](../DATA-FLOW.md), [provider matrix](../PROVIDERS.md), and [threat model](../THREAT-MODEL.md) before changing a boundary.
