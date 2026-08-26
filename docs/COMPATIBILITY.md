# Linux compatibility evidence

Last reviewed: 26 August 2026

“Declared”, “automated”, “expected”, and “real-device verified” are separate
states. This table is intentionally narrower than the combinations the GTK,
Flatpak, and PortAudio stacks may happen to support.

| Path | Evidence | Status |
| --- | --- | --- |
| x86_64 Flatpak build/install/remove | Clean GNOME 50 container workflow | Automated every relevant change |
| GTK 3 on X11 | Xvfb first-run, desk, accessibility, and settings smoke | Automated virtual display; no physical desktop claim |
| GTK 3 on Wayland | Manifest declares Wayland and fallback X11; unit diagnostics classify Wayland | Declared/logic-tested; real compositor report open |
| PulseAudio socket in Flatpak | Minimal `--socket=pulseaudio` permission asserted | Declared; real microphone report open |
| PipeWire through PulseAudio compatibility | Intended desktop route documented by PortAudio stack | Expected; real microphone report open |
| Source install on Debian/Ubuntu | `setup.sh`, diagnostics, CI unit contracts | Source contract; native library/hardware report open |
| Direct ALSA/JACK | JACK disabled in bundled PortAudio; no declared direct ALSA support | Not supported |
| Bluetooth microphones | No repeatable codec/device evidence | Not supported yet |
| aarch64 or other architectures | No published package build | Not supported |

## Reproduction protocol

1. Record app version, distribution, desktop, X11/Wayland, PipeWire/PulseAudio,
   installation path, architecture, and microphone connection type.
2. Run `voice-transcriber --doctor --json` and review the output locally.
3. Open the app, refresh inputs, select the default and one explicit device,
   observe the local meter, then start/stop one short segment.
4. For a tester-owned provider configuration, verify one final transcript,
   copy, explicit export, history-off restart, and uninstall/data removal.
5. Publish only the compatibility outcome and sanitized diagnostics. Never
   publish keys, audio, transcript content, config files, device serials, or
   unrelated environment variables.

Use the repository's **Linux audio compatibility report** issue form. A report
does not enter the supported table until the exact path is reproducible and the
privacy/cleanup steps pass.
