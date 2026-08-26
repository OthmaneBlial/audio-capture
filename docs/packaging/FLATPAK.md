# Flatpak installation

Voice Transcriber `v1.0.0` publishes one `x86_64` bundle built from the matching
Git tag and a SHA-256 checksum. The application uses the GNOME 50 runtime and
has no broad home or host filesystem permission.

## Install the release

Install Flatpak through your distribution, add Flathub for the GNOME runtime,
then download and verify both release files:

```bash
flatpak remote-add --user --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo
curl -LO https://github.com/OthmaneBlial/audio-capture/releases/download/v1.0.0/voice-transcriber-1.0.0-x86_64.flatpak
curl -LO https://github.com/OthmaneBlial/audio-capture/releases/download/v1.0.0/voice-transcriber-1.0.0-x86_64.flatpak.sha256
sha256sum --check voice-transcriber-1.0.0-x86_64.flatpak.sha256
flatpak install --user ./voice-transcriber-1.0.0-x86_64.flatpak
flatpak run io.github.othmaneblial.audio_capture
```

The bundle requests only Wayland, fallback X11/IPC, PulseAudio, and network.
Network access is required for Groq transcription. The application has no
broad filesystem access; GTK's document portal grants access only to files you
explicitly choose for export.

## Diagnose

```bash
flatpak run --command=voice-transcriber io.github.othmaneblial.audio_capture --doctor
flatpak run --command=voice-transcriber io.github.othmaneblial.audio_capture --list-devices
```

Diagnostics do not contact Groq unless `--probe-provider` is explicitly added
and never print the API key. A headless machine can correctly report that no
microphone or display session is ready.

## Update or remove

A downloaded single-file bundle does not create an update remote. Download the
new version and use `flatpak install --user --or-update ./NEW-BUNDLE.flatpak`.
The versioned release notes identify every compatibility or privacy change.

```bash
flatpak uninstall --user io.github.othmaneblial.audio_capture
# Remove the sandboxed preferences as well:
flatpak uninstall --user --delete-data io.github.othmaneblial.audio_capture
```

Explicitly exported documents live outside the sandbox and therefore remain
after `--delete-data`.

## Source mapping

The `v1.0.0` tag, `main.py`, `pyproject.toml`, AppStream release entry, bundle
filename, and release title all use `1.0.0`. GitHub Actions builds the manifest
from the tag commit, installs the resulting bundle into a clean user scope,
checks CLI contracts and permissions, launches GTK under Xvfb, and removes the
app and sandbox. See the [release checklist](RELEASE-CHECKLIST.md) for the
separate real-microphone gate.
