# Supported environments

Voice Transcriber publishes a narrow support boundary so that “supported”
means tested, not merely expected to work.

## Current support contract

| Surface | Supported in v1.0.0 | Evidence | Status |
| --- | --- | --- | --- |
| Operating system | Debian/Ubuntu Linux desktops | `setup.sh` uses `apt`; v1 verification ran on Ubuntu | Supported source install |
| Desktop toolkit | GTK 3 | Application imports GTK 3 explicitly | Supported |
| Audio API | PortAudio through PyAudio | Unit-tested discovery, selection, level calculation, and cleanup | Supported API; real hardware verification required |
| Audio servers | PipeWire/PulseAudio through the system PortAudio route | Documented setup path | Expected; compatibility reports welcome |
| Display session | X11 and Wayland GTK sessions | Flatpak declares Wayland and fallback X11 sockets | Package smoke-tested; real desktop reports welcome |
| CPU architecture | `x86_64` | The v1 Flatpak workflow built, installed, and removed the public bundle shape | Automated package path proven for v1 |
| Python | 3.9 or newer | Package metadata declares `>=3.9`; v1 CI exercised 3.9, 3.11, and 3.14 | Declared range with release-specific boundary evidence |
| Transcription | Groq `whisper-large-v3-turbo` | Fake-client contract tests; user-managed key | Supported cloud path |
| Installation | Versioned Flatpak release asset; source setup remains available | Clean user-scope install/CLI/metadata/uninstall workflow | Primary package path |
| Packaged app | Flatpak | Source-pinned manifest, minimal permissions, checksum, and release bundle | Supported on the declared boundary after real-device gate |
| Other package formats | Debian package, AppImage | No release artifact exists | Not supported |
| Other platforms | macOS, Windows, mobile, browser | No native implementation or verification | Not supported |

“Expected” is deliberately weaker than “supported”: it means the underlying
stack should work, but this project has not yet published repeatable evidence
for the exact combination.

The repository's general `CI` workflow is manually paused as of 1 September
2026. CI statements above are release-specific historical evidence, not a claim
that the general workflow currently runs on every push. Flatpak packaging and
CodeQL are separate workflows.

See [Linux compatibility evidence](COMPATIBILITY.md) for the explicit
X11/Wayland and PipeWire/PulseAudio evidence levels and the bounded reproduction
protocol. Use the structured compatibility issue form instead of a full system
dump.

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
