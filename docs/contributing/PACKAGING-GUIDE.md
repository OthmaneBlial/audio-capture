# Packaging and release guide

The supported binary path is one `x86_64` Flatpak release asset. Source install
remains available for development. Do not add another package format without a
maintainer-approved support and clean-removal plan.

## Important files

| File | Purpose |
| --- | --- |
| `io.github.othmaneblial.audio_capture.yml` | Runtime, sources, build, and sandbox permissions |
| `packaging/python3-dependencies.json` | Hash-pinned Python source modules |
| `packaging/*.desktop`, `*.metainfo.xml`, icons | Desktop integration and AppStream metadata |
| `packaging/smoke_test_flatpak.sh` | Installed-bundle CLI, permissions, GTK, and removal proof |
| `.github/workflows/flatpak.yml` | Pull/branch package validation and offline rebuild |
| `.github/workflows/release.yml` | Tag-only build, tests, checksum, SBOM, attestations, and release |

## Invariants

- Keep permissions limited to Wayland, fallback X11/IPC, PulseAudio, and the
  network needed by the supported Groq path. Do not add broad filesystem or
  device access.
- Every source used by the build is pinned. The clean second build must succeed
  with `--disable-download`.
- Manifest, AppStream, exported repository, desktop file, and installed bundle
  checks are separate gates.
- Version surfaces must agree across Python metadata, CLI, AppStream,
  changelog, filename, tag, and release title.
- A headless Xvfb pass is not physical microphone or desktop-session evidence.

## Before proposing a packaging change

Run the release checker and deterministic suite locally, then push a branch so
the containerized Flatpak workflow can run:

```bash
python3 scripts/check_release.py 1.0.0
python3 -m unittest discover -s tests -v
ruff check .
```

Use the current project version in place of `1.0.0`. Read the full
[Flatpak instructions](../packaging/FLATPAK.md), [linter policy](../packaging/FLATPAK-LINT.md), [release checklist](../packaging/RELEASE-CHECKLIST.md), and [version policy](../VERSION-POLICY.md). Only a maintainer creates release tags.
