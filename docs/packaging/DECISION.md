# Packaging decision: Flatpak first

## Decision

Voice Transcriber will use **Flatpak as its primary Linux package**. A Debian
package may follow only when its dependency/update contract can be tested with
the same rigor. AppImage is not planned while native GTK, PortAudio, and portal
behaviour remain harder to make auditable there.

The stable application ID is:

```text
io.github.othmaneblial.audio_capture
```

The initial manifest targets `org.gnome.Platform//50` and its matching SDK,
which are current for this packaging decision. Runtime branches are reviewed at
each GNOME release rather than treated as permanent.

## Why Flatpak

- It gives the app an explicit, inspectable runtime permission contract.
- It packages the GTK/Python/native stack without relying on an unknown host
  Python environment.
- GTK file choosers can use portals for an explicitly selected export instead
  of granting broad home-directory access.
- The generated Python and native source modules can be pinned and rebuilt
  without network access during the build phase.

## Permission contract

| Permission | Reason |
| --- | --- |
| Wayland socket | Native GTK display |
| Fallback X11 socket and IPC | Desktop compatibility when Wayland is unavailable |
| PulseAudio socket | Microphone capture through PortAudio/PyAudio; this permission covers more than input and is disclosed as such |
| Network share | Groq HTTPS requests; Flatpak cannot narrow this to one hostname |

The package deliberately does **not** request `home`, `host`, `device=all`, or
portal D-Bus names. Export must remain an explicit GTK file-chooser operation.

## Reproducible dependency contract

- PortAudio `v19.7.0` is source-pinned by SHA-256 in the main manifest.
- PyAudio, WebRTC VAD, and python-dotenv are exact-version, hashed sources in
  `packaging/python3-dependencies.json`.
- PyGObject comes from the GNOME runtime and is not duplicated through pip.
- The Groq SDK was removed in favour of the small tested stdlib HTTP boundary,
  eliminating a large transitive HTTP/Pydantic/Rust dependency tree.
- The application module installs with `--no-deps --no-build-isolation`.

Regenerate the Python module with the official `flatpak-pip-generator` whenever
`packaging/requirements-flatpak.txt` changes. Review all new URLs, versions, and
hashes before committing.

## Required gates

1. Validate the desktop file and MetaInfo without the network.
2. Run Flatpak manifest, AppStream, and exported-repository lint with zero
   errors.
3. Fetch declared sources, then rebuild with `flatpak-builder --disable-download`.
4. Install the produced bundle on a clean user installation, run `--version`,
   `--help`, and `--doctor --json`, inspect permissions/metadata, then uninstall.
5. On real Linux hardware, verify launcher/icon, X11 and Wayland GTK launch,
   microphone enumeration and capture, one real Groq transcription, file chooser
   export, and data removal.
6. Treat a Flathub PR test build and an official Flathub publication as separate
   future gates. A local or CI bundle is not a Flathub release.

## Primary references

- [Flatpak manifests](https://docs.flatpak.org/en/latest/manifests.html)
- [Flatpak sandbox permissions](https://docs.flatpak.org/en/latest/sandbox-permissions.html)
- [Python dependencies in Flatpak](https://docs.flatpak.org/en/latest/python.html)
- [Flathub application requirements](https://docs.flathub.org/docs/for-app-authors/requirements)
- [Flathub linter](https://docs.flathub.org/docs/for-app-authors/linter)

