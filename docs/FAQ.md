# Frequently asked questions

## Is Voice Transcriber fully offline?

No. Capture, VAD, the input meter, and editing are local, but the implemented
transcription path sends completed speech segments to Groq after explicit
consent. An offline provider is not part of the supported current build.

## Does the app save my recordings?

No raw-audio recording is written by the application. Frames and completed
segments are held in bounded memory while needed. Explicit text exports and
opt-in transcript history are separate, visible choices.

## Do I need a Groq key just to open it?

No. You can open the desktop, inspect Settings, list microphones, and run the
local microphone test without a key. Start remains blocked until configuration
and cloud consent are valid; the app never fabricates a transcript.

## Which systems are supported?

The native Rust build targets Linux x86_64, macOS arm64, and Windows x86_64.
macOS arm64 has a local build and real microphone smoke-test evidence. Linux and
Windows have CI build paths; runtime and hardware support still require a report
for the exact OS, audio backend, and device. See [SUPPORT.md](SUPPORT.md).

## Why does the app need network access?

Only the Groq provider path uses the network, and only for a completed segment
after the key and cloud-boundary checkbox are accepted. Diagnostics and the
microphone test are local-only.

## Where is transcript history stored?

History is disabled by default. When enabled, the application stores bounded
text history in its platform-appropriate user data directory, with retention
limits and clear/delete controls. Audio is never added to history.

## How can I report a problem without exposing private data?

Run `voice-transcriber --doctor --json`, review the output, and use the
structured bug or compatibility form. Never attach an API key, recording,
transcript, config file, home path, or full environment dump. Report suspected
security or privacy flaws privately through [`SECURITY.md`](../SECURITY.md).

## How can I help without an API key or microphone?

The Rust core has deterministic tests for configuration, audio conversion,
framing, VAD, provider admission, transcript ordering, exports, and history.
Follow the [contributor map](contributing/README.md) and choose an issue with
explicit acceptance criteria.
