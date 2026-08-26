# Flatpak release checklist

This checklist distinguishes an automated package build from a supported public
release. Record the commit, bundle checksum, tester environment, and evidence
URL for every completed run.

## Automated package gate

- [x] Unit tests, Ruff, and Python compilation pass.
- [x] Desktop file and AppStream metadata validate with no errors.
- [x] Flatpak manifest builds from a clean checkout.
- [ ] All declared sources are fetched, then an offline `--disable-download`
  rebuild passes.
- [ ] Manifest, exported repository, and AppStream lints report zero errors.
- [x] Bundle installs into a clean user Flatpak installation.
- [x] Installed `--version`, `--help`, and `--doctor --json` contracts pass.
- [x] Installed permissions contain only Wayland, fallback X11/IPC,
  PulseAudio, and network.
- [x] Desktop file, MetaInfo, icon, and executable exist inside `/app`.
- [x] GTK window and first-run dialog remain open under Xvfb.
- [x] Uninstall with data removal succeeds.

## Real Linux desktop gate

- [ ] Test exact distribution, version, architecture, desktop, X11/Wayland,
  and PipeWire/PulseAudio route is recorded.
- [ ] App appears in the launcher with the correct icon and name.
- [ ] First-run controls are reachable in order from the keyboard; accessible
  names and boundary copy are understandable.
- [ ] Microphone permission is visible and can be revoked.
- [ ] Default and one explicitly selected microphone show a live local meter.
- [ ] Start, speech detection, stop, and final segment flush work.
- [ ] One real Groq transcription succeeds with a tester-owned key.
- [ ] Invalid key, offline network, rate limit, missing device, and full queue
  states remain actionable and contain no secret/transcript content.
- [ ] Copy produces the visible transcript.
- [ ] Export uses an explicit chooser, writes only the chosen file, and does not
  require broad home access.
- [ ] Closing and reopening does not retain raw audio or transcript text.
- [ ] Uninstall and “delete data” remove the app sandbox; an external explicit
  export remains because it belongs to the user.

## Public artifact gate

- [x] Bundle filename includes the exact application version and architecture.
- [x] SHA-256 checksum file is generated from the uploaded bundle.
- [x] Release notes name the supported environments and permission boundary.
- [x] Source tag, changelog, package version, MetaInfo release, and bundle output
  all match.
- [ ] A clean machine installs the *downloaded release asset*, not a local build,
  and repeats the real desktop gate.
