# Frequently asked questions

## Is Voice Transcriber fully offline?

Not in the supported Flatpak. It detects speech locally, then sends completed
speech segments to Groq for transcription. A source-only whisper.cpp prototype
exists behind an explicit feature flag, but it is not yet a supported packaged
backend.

## Does the app save my recordings?

No raw-audio recording is written by the application. Frames and completed
segments are held in bounded memory while needed. Explicit text exports and
opt-in transcript history are separate, visible choices.

## Do I need a Groq key just to open it?

No. You can inspect first-run setup, Settings, privacy information, and detected
microphones without a key. The app blocks Start rather than manufacturing a
fake transcript.

## Why does the Flatpak have network and PulseAudio permissions?

PulseAudio permission exposes the desktop's PipeWire/PulseAudio-compatible
microphone route. Network permission is needed to send completed speech
segments to Groq in the supported cloud mode. The package has no broad home or
host filesystem access.

## Where is transcript history stored?

History is disabled by default. When you explicitly enable it, the Settings
screen discloses its sandboxed local location and retention period. You can
delete one entry, clear all history, or remove all sandbox data during Flatpak
uninstall. Explicitly exported files remain at the destination you chose.

## Which Linux systems are supported?

The primary artifact is an `x86_64` Flatpak using GTK 3 and the system
PipeWire/PulseAudio route, with Wayland and fallback X11 permissions. The
[support matrix](SUPPORT.md) distinguishes automated evidence from real-device
evidence. macOS, Windows, mobile, browser, Debian packages, and AppImage are not
currently supported.

## How can I report a problem without exposing private data?

Use `voice-transcriber --doctor --json`, review the output, and open the
structured bug or compatibility form. Never attach an API key, recording,
transcript, config file, home path, or full environment dump. Report suspected
security or privacy flaws privately through [`SECURITY.md`](../SECURITY.md).

## How can I help if I do not have an API key?

The deterministic suite fakes native and provider boundaries. Follow the
[contributor map](contributing/README.md) and choose a public `good first issue`
with explicit acceptance criteria.
