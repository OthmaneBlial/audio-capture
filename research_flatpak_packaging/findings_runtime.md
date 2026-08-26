# Flatpak packaging findings for the Python/GTK 3 app

Research date: 2026-08-26. Sources are limited to the official Flatpak documentation, the official Flatpak Builder Tools repository, and Flathub's runtime listing.

## Decision: target GNOME Platform 50

Use this manifest baseline:

```yaml
id: io.github.othmaneblial.audio_capture
runtime: org.gnome.Platform
runtime-version: '50'
sdk: org.gnome.Sdk
command: voice-transcriber
```

Flathub currently exposes **GNOME Application Platform version 50** for both `x86_64` and `aarch64`. Flatpak's runtime documentation says the GNOME runtime is the appropriate runtime for GNOME/GTK applications, is based on Freedesktop, and adds GNOME platform libraries. It also says GNOME runtime releases track GNOME releases and a branch is usually supported for about a year, so `runtime-version` must be reviewed at every GNOME release rather than left indefinitely.

For this GTK 3 application, first inspect what the SDK already contains and do not bundle duplicate runtime libraries. Useful checks are:

```sh
flatpak run --command=pkg-config org.gnome.Sdk//50 --list-all
flatpak run --command=python3 org.gnome.Sdk//50 -c 'import gi; print(gi.__version__)'
flatpak run --command=pkg-config org.gnome.Sdk//50 --modversion gtk+-3.0
```

In particular, exclude `PyGObject` from generated pip modules when the runtime supplies it. If PortAudio is absent, package it as a separate source-built Flatpak module before the Python dependencies; do not assume a host distribution package will be visible inside the sandbox.

Sources:

- https://flathub.org/en/apps/org.gnome.Platform
- https://docs.flatpak.org/en/latest/available-runtimes.html

## Manifest conventions

- Name the manifest after the application ID, for example `io.github.othmaneblial.audio_capture.yml`.
- Use current `id`, not deprecated `app-id`.
- Declare `id`, `runtime`, `runtime-version`, `sdk`, and `command` at top level.
- Put reusable/native dependency modules first, generated Python dependency modules next, and the frequently changing application module last. Flatpak Builder builds in declaration order and can reuse the preceding module cache.
- Prefer the real project build system when possible. This setuptools project can also use `buildsystem: simple` with an explicit offline install into `/app`.
- Pin every remote archive with `sha256`, every Git source to an immutable commit, and keep the generated dependency manifest in Git. The source-fetch phase may use the network; the module build must not resolve or download dependencies.
- Keep permissions narrow. The expected runtime permissions for this app are Wayland plus fallback X11, PulseAudio for microphone capture, and network access for the Groq API:

```yaml
finish-args:
  - --share=ipc
  - --socket=wayland
  - --socket=fallback-x11
  - --socket=pulseaudio
  - --share=network
```

Do not add a broad home-directory permission merely for export. A GTK file chooser should be tested through the desktop portal first.

Official manifest documentation:

- https://docs.flatpak.org/en/latest/manifests.html
- https://docs.flatpak.org/en/latest/flatpak-builder-command-reference.html

## Python dependencies: generate vendored, hashed sources

Flatpak Builder performs a source-download stage before building modules. The official Builder Tools project exists specifically to generate manifest sources/modules so builds can run without network access. For Python, use its maintained `flatpak-pip-generator` against the same SDK branch as the app.

Recommended flow:

1. Make a packaging requirements file with exact versions. Do not feed the current broad ranges directly into a release build.
2. Omit packages supplied by the runtime, notably `PyGObject` after verifying `import gi` in `org.gnome.Sdk//50`.
3. Generate and commit the dependency module, for example:

   ```sh
   flatpak-pip-generator \
     --runtime='org.gnome.Sdk//50' \
     --requirements-file=packaging/requirements-flatpak.txt \
     --output=python3-dependencies \
     --checker-data
   ```

4. Include `python3-dependencies.json` before the application module in the YAML manifest. The generator records PyPI artifact URLs and hashes. It prefers universal wheels, then source distributions; platform wheels must be enabled explicitly and should cover both `x86_64` and `aarch64` when Flathub support is intended.
5. The application module should install only from its checked-out source and must not ask pip to resolve dependencies. A suitable pattern is:

   ```yaml
   - name: audio-capture
     buildsystem: simple
     build-commands:
       - pip3 install --verbose --prefix=/app --no-deps --no-build-isolation .
     sources:
       - type: dir
         path: ..
   ```

For a Flathub submission, replace a development-only parent-directory source with an immutable archive or Git commit source. Verify offline reproducibility by downloading sources once and rebuilding with `flatpak-builder --disable-download`; the official command reference says that option guarantees no network I/O and fails if any source is missing.

Sources:

- https://docs.flatpak.org/en/latest/python.html
- https://github.com/flatpak/flatpak-builder-tools
- https://github.com/flatpak/flatpak-builder-tools/tree/master/pip
- https://docs.flatpak.org/en/latest/flatpak-builder-command-reference.html

## Desktop file, MetaInfo, and icon installation

Use the **same application ID everywhere**. Renaming during the build is supported, but the Flatpak documentation says naming correctly in the source tree is more reliable.

Install these artifacts under `/app`:

```text
/app/share/applications/io.github.othmaneblial.audio_capture.desktop
/app/share/metainfo/io.github.othmaneblial.audio_capture.metainfo.xml
/app/share/icons/hicolor/scalable/apps/io.github.othmaneblial.audio_capture.svg
```

Example application-module commands:

```yaml
build-commands:
  - pip3 install --verbose --prefix=/app --no-deps --no-build-isolation .
  - install -Dm644 packaging/io.github.othmaneblial.audio_capture.desktop /app/share/applications/io.github.othmaneblial.audio_capture.desktop
  - install -Dm644 packaging/io.github.othmaneblial.audio_capture.metainfo.xml /app/share/metainfo/io.github.othmaneblial.audio_capture.metainfo.xml
  - install -Dm644 resources/icon.svg /app/share/icons/hicolor/scalable/apps/io.github.othmaneblial.audio_capture.svg
```

The desktop entry should at minimum contain `Name`, `Exec=voice-transcriber`, `Type=Application`, `Icon=io.github.othmaneblial.audio_capture`, and suitable categories such as `AudioVideo;Audio;Utility;`. The MetaInfo file must use the application ID as its `<id>` and refer to `io.github.othmaneblial.audio_capture.desktop` in its desktop launchable. The SVG icon is installed in the `scalable/apps` directory and must be square.

Validate before accepting the package:

```sh
desktop-file-validate packaging/io.github.othmaneblial.audio_capture.desktop
appstreamcli validate --no-net --explain packaging/io.github.othmaneblial.audio_capture.metainfo.xml
flatpak-builder --show-manifest io.github.othmaneblial.audio_capture.yml >/dev/null
```

Sources:

- https://docs.flatpak.org/en/latest/conventions.html
- https://docs.flatpak.org/en/latest/manifests.html

## Implementation cautions specific to this project

- The package is currently named `voice-transcriber`, while the repository is `audio-capture`. Choose one stable public Flatpak ID now; changing it later creates a different installed application.
- The runtime dependency list includes compiled/native packages (`PyAudio`, `webrtcvad`) and a runtime-provided binding candidate (`PyGObject`). A successful host `pip install` is not evidence of a reproducible Flatpak build; build both supported architectures.
- Audio capture needs a real sandbox smoke test with `--socket=pulseaudio`. Network access for Groq is a runtime permission and is distinct from the forbidden dependency downloads during the build.
- The package should be considered complete only after the desktop entry launches the installed command, the icon appears in the host launcher, MetaInfo validates without network access, microphone recording works in the sandbox, and the generated dependency manifest rebuilds with downloads disabled.
