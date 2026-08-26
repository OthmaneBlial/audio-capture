# Supported environments

Voice Transcriber publishes a narrow support boundary so that “supported”
means tested, not merely expected to work.

## Current support contract

| Surface | Supported in v0.6.0 | Evidence | Status |
| --- | --- | --- | --- |
| Operating system | Debian/Ubuntu Linux desktops | `setup.sh` uses `apt`; CI runs Ubuntu | Supported source install |
| Desktop toolkit | GTK 3 | Application imports GTK 3 explicitly | Supported |
| Audio API | PortAudio through PyAudio | Unit-tested discovery, selection, level calculation, and cleanup | Supported API; real hardware verification required |
| Audio servers | PipeWire/PulseAudio through the system PortAudio route | Documented setup path | Expected; compatibility reports welcome |
| Display session | X11 and Wayland GTK sessions | Flatpak declares Wayland and fallback X11 sockets | Package smoke-tested; real desktop reports welcome |
| CPU architecture | `x86_64` | GitHub-hosted Linux builds and installs the public bundle shape | CI-tested package path |
| Python | 3.9 or newer | Package metadata declares `>=3.9`; CI currently exercises 3.11 | 3.11 CI-proven; broader matrix planned |
| Transcription | Groq `whisper-large-v3-turbo` | Fake-client contract tests; user-managed key | Supported cloud path |
| Installation | Versioned Flatpak release asset; source setup remains available | Clean user-scope install/CLI/metadata/uninstall workflow | Primary package path |
| Packaged app | Flatpak | Source-pinned manifest, minimal permissions, checksum, and release bundle | Supported on the declared boundary after real-device gate |
| Other package formats | Debian package, AppImage | No release artifact exists | Not supported |
| Other platforms | macOS, Windows, mobile, browser | No native implementation or verification | Not supported |

“Expected” is deliberately weaker than “supported”: it means the underlying
stack should work, but this project has not yet published repeatable evidence
for the exact combination.

## Hardware verification report

When reporting a microphone issue, include only:

- distribution and version;
- desktop environment and X11/Wayland session;
- PipeWire or PulseAudio version, if known;
- microphone connection type (built-in, USB, Bluetooth);
- sanitized output from `python main.py --list-devices --json`;
- the visible error and reproduction steps.

Never include an API key, recording, transcript, full environment dump, or
configuration file.

## Maintainer response target

Reproducible bug reports should receive an acknowledgement within seven days.
Security reports follow [SECURITY.md](../SECURITY.md) and remain private until
a coordinated fix is available.
