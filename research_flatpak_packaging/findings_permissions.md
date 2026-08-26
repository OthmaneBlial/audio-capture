# Flatpak permissions and Flathub validation research

Research date: 2026-08-26

Scope: a Python/GTK 3 desktop application that captures microphone input through PyAudio/PortAudio and sends audio to a remote HTTPS transcription API. Only current official Flatpak and Flathub documentation was used.

## Recommended minimum runtime permissions

For this application as it exists today, the defensible baseline is:

```yaml
finish-args:
  # GTK windowing on native Wayland, with X11 only as a fallback.
  - --socket=wayland
  - --socket=fallback-x11
  # Needed by the X11 fallback for shared-memory drawing.
  - --share=ipc
  # Microphone capture through PulseAudio/PipeWire compatibility/PortAudio.
  - --socket=pulseaudio
  # Outbound connection to the transcription API.
  - --share=network
```

Why this is the minimum:

- Flatpak applications have no network, device, PulseAudio, X11, or other host-service access by default. `finish-args` is where the runtime sandbox is opened deliberately.
- `--socket=pulseaudio` is Flatpak's documented audio permission. It explicitly covers sound input (microphone), playback, MIDI, and ALSA devices under `/dev/snd`. It is therefore sufficient for the app's audio use case and makes broad permissions such as `--device=all` unnecessary.
- `--share=network` is required for the app's outbound HTTPS request. It permits general network access; Flatpak does not express an HTTPS-only or host-only allowlist through this flag. Endpoint restriction remains an application-level responsibility.
- For an application with native Wayland support, Flatpak recommends `--socket=wayland` plus `--socket=fallback-x11`, not simultaneous unconditional `x11` and `wayland` sockets. `--share=ipc` accompanies the X11 fallback. If the application is later verified to be Wayland-only, both `fallback-x11` and `ipc` can be reconsidered, but Flathub normally expects the fallback for desktop compatibility.
- Do not add `--filesystem=home`, `--filesystem=host`, `--device=all`, full session/system D-Bus access, or explicit portal D-Bus names. None is needed for this app's core flow and these would weaken its Flathub permission story.
- `--device=dri` is not part of the core functional minimum identified here. Add it only if real Flatpak runtime testing shows that this GTK build needs hardware-accelerated rendering; it is a standard permission, but microphone capture and HTTPS do not require it.

Primary source: [Flatpak sandbox permissions](https://docs.flatpak.org/en/latest/sandbox-permissions.html)

## Portals versus microphone access

- Flathub requires static permissions to be kept to an absolute minimum and requires a suitable, ecosystem-supported XDG portal to be used when one covers the use case.
- GTK transparently uses portals for supported operations such as native file selection, opening URIs, printing, notifications, and session inhibition. Using `GtkFileChooserNative` for transcript import/export avoids a blanket filesystem permission. Files selected through the portal are granted individually.
- Portal APIs are already allowed by Flatpak. The manifest must not add `--talk-name=org.freedesktop.portal.*`; Flathub's linter treats that as invalid/unnecessary.
- The official GTK portal list does not provide transparent microphone capture for a PyAudio/PortAudio stream, while the official sandbox permission guide explicitly assigns microphone capture to `--socket=pulseaudio`. Therefore, for this app, `--socket=pulseaudio` is the current justified static permission. This is an inference from the two official guides, not a claim that no future audio portal can ever exist.
- This permission is not microphone-only: it also exposes playback, MIDI, and ALSA sound devices. The privacy description and store metadata should be candid about the microphone need, and the implementation should open input streams only.

Primary sources:

- [Flathub requirements: permissions](https://docs.flathub.org/docs/for-app-authors/requirements#permissions)
- [Portal support in GTK](https://docs.flatpak.org/en/latest/portals.html)
- [Flatpak sandbox permissions](https://docs.flatpak.org/en/latest/sandbox-permissions.html)
- [Flathub linter policy](https://docs.flathub.org/docs/for-app-authors/linter)

## Build and offline dependency expectations

Runtime network access and build-time network access are separate. `--share=network` in `finish-args` enables the installed app; it does not authorize downloads during the build.

Flathub's build policy requires:

- no network during the build phase;
- every build and runtime dependency declared as a manifest source with a publicly accessible URL, or as an allowed local source;
- source builds for the application and source-available dependencies;
- no source tree or precompiled/binary build artifacts copied directly into the Flathub submission repository;
- the top-level manifest named exactly after the application ID and using the latest suitable runtime version hosted on Flathub at submission time;
- a dependency submanifest for generated dependency sources when needed.

For Python, generate a pinned source submanifest with `flatpak-pip-generator` from the release's locked requirements. The generator records source archives and hashes. Install Python packages into `/app`, normally with `pip3 install --prefix=/app --no-deps ...`; `--no-deps` is safe only when every dependency is already represented by its generated module/source entries. PyAudio and PortAudio must be built or provided through the runtime/manifest; a host `apt` package or an undeclared wheel is not available to the Flathub builder.

Useful proof of a truly offline-capable manifest:

```sh
# Fetch all declared sources first.
flatpak-builder --download-only builddir <APP_ID>.yml

# Then force a clean build while forbidding any further source download.
flatpak-builder --force-clean --disable-download --repo=repo builddir <APP_ID>.yml
```

`--disable-download` is explicitly documented as guaranteeing no network I/O from source downloads and fails if any source is missing. Flathub's recommended end-to-end local build uses its Builder image:

```sh
flatpak install -y flathub org.flatpak.Builder
flatpak run --command=flathub-build org.flatpak.Builder --install <APP_ID>.yml
```

Primary sources:

- [Flathub requirements: no network and dependency manifests](https://docs.flathub.org/docs/for-app-authors/requirements#no-network-access-during-build)
- [Flatpak Python guide](https://docs.flatpak.org/en/latest/python.html)
- [Flatpak Builder command reference](https://docs.flatpak.org/en/latest/flatpak-builder-command-reference.html)
- [Flathub submission build procedure](https://docs.flathub.org/docs/for-app-authors/submission#build-and-install)

## Validation gates before submission

Run all three official checks; a manifest-only lint is not enough evidence that the exported app is valid:

```sh
# YAML/JSON schema, manifest policy, permissions, source policy, etc.
flatpak run --command=flatpak-builder-lint org.flatpak.Builder manifest <APP_ID>.yml

# Exported OSTree repository checks; requires a build created with --repo=repo.
flatpak run --command=flatpak-builder-lint org.flatpak.Builder repo repo

# Direct AppStream/Flathub metadata validation.
flatpak run --command=flatpak-builder-lint org.flatpak.Builder appstream <APP_ID>.metainfo.xml
```

Acceptance should require zero errors. In particular:

- invalid YAML/JSON, unknown manifest properties, malformed schema, missing `finish-args`, and top-level build network access are non-waivable linter failures;
- do not design around linter exceptions: Flathub describes them as case-by-case and temporary, and many relevant checks never receive exceptions;
- AppStream warnings as well as errors are fatal in Flathub validation;
- the manifest ID, desktop file, icon, launchable entry, and installed MetaInfo filename/ID must match exactly;
- graphical apps need a desktop file, a correctly installed icon, at least one MetaInfo screenshot, and a MetaInfo file that passes validation;
- screenshots must use direct image URLs and, when hosted in Git, URLs pinned to a tag or commit rather than a mutable branch;
- MetaInfo needs a `releases` entry whose version is properly ordered, date is not in the future, and release notes accurately describe the shipped version.

Primary sources:

- [Flatpak builder lint](https://docs.flathub.org/docs/for-app-authors/linter)
- [Flathub MetaInfo validation](https://docs.flathub.org/docs/for-app-authors/metainfo-guidelines#validation)
- [Flathub required files and metadata](https://docs.flathub.org/docs/for-app-authors/requirements#required-files)
- [Flathub MetaInfo screenshots and releases](https://docs.flathub.org/docs/for-app-authors/metainfo-guidelines#screenshots)

## Release evidence ladder

Treat these as separate gates, with saved logs or URLs for each:

1. **Manifest evidence:** manifest lint passes with no exceptions.
2. **Build evidence:** the Flathub Builder command succeeds from a clean checkout, including the no-download/offline rebuild.
3. **Repository evidence:** repo lint passes on the exported `repo`.
4. **Runtime evidence:** install and run the built Flatpak, then verify GTK launch, microphone enumeration, an actual microphone capture, an actual HTTPS transcription, error states, and transcript export through the portal. A successful build alone does not prove launch or microphone/API behavior.
5. **Architecture evidence:** Flathub builds `x86_64` and `aarch64` by default. Either produce compatible source-based builds on both or justify a top-level `flathub.json` architecture restriction.
6. **Submission evidence:** the new-app PR targets Flathub's `new-pr` branch, passes review, and its requested test build succeeds. Install the PR test build and repeat the runtime smoke test.
7. **Publication evidence:** after approval/merge, confirm the official build succeeded and the app is actually published/listed on Flathub. A PR test build is not public-release proof; Flathub says screenshots are unavailable in test builds and appear after the official build is published.

For later updates, Flathub's official workflow is: update PR -> successful test build -> maintainer installs/tests the test build -> merge -> official build -> publication. Flathub explicitly warns that a successful automated build does not guarantee that the application launches correctly.

Primary sources:

- [Flathub submission and review](https://docs.flathub.org/docs/for-app-authors/submission)
- [Flathub maintenance and update workflow](https://docs.flathub.org/docs/for-app-authors/maintenance)
- [Flathub requirements: architectures and metadata](https://docs.flathub.org/docs/for-app-authors/requirements)
- [Flathub MetaInfo guidelines](https://docs.flathub.org/docs/for-app-authors/metainfo-guidelines)

## Practical conclusion for this repository

The expected permission story is small and reviewable: Wayland plus fallback X11/IPC, PulseAudio for microphone capture, and network for the remote transcription API. File access should be portal-mediated and app state should remain in the Flatpak-owned XDG directories. The highest packaging risk is not the runtime permission set; it is making PyAudio/PortAudio and the Python HTTP stack fully source-pinned and buildable without network access, then proving the installed sandbox can both enumerate a microphone and reach the transcription endpoint.
