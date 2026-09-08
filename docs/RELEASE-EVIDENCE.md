# Release evidence register

Last reviewed: 8 September 2026

This register separates evidence for the current source checkout, automated
package checks, and gates that still require a real Linux desktop or a human
tester. It is a record of observed results, not a release approval.

## Source and automated checks

| Surface | Exact evidence | Scope and limit |
| --- | --- | --- |
| Source checkout | `main` at `2d2f045` | Documentation commit on top of the code candidate below |
| Deterministic suite | `python scripts/run_checks.py` passed 109 tests and 69% combined line/branch coverage | No physical microphone, GTK desktop, provider account, or network transcription |
| Static quality | Ruff, Python compilation, `pip-audit --require-hashes --disable-pip -r packaging/requirements-audit.txt`, and Bandit passed locally | Static/dependency checks; no full operating-system audit |
| CLI contracts | `python main.py --version` returned `voice-transcriber 1.0.0`; help lists `--list-devices`, `--doctor`, `--device`, and `--probe-provider` | This macOS checkout has no usable GTK/PyAudio runtime for a desktop launch |
| Privacy boundary | The deterministic privacy suite passed; default history remains off and provider probes are opt-in | Does not prove provider retention or clipboard-manager behavior |

## Package candidate

| Surface | Exact evidence | Scope and limit |
| --- | --- | --- |
| Flatpak candidate source | Code candidate `cfcc9e6` | The later documentation commits only update this register/wording |
| Build and install | GitHub Actions Flatpak run [`34254256484`](https://github.com/OthmaneBlial/audio-capture/actions/runs/34254256484) passed | GNOME 50 container, not a physical desktop |
| Package checks | Online build, no-download rebuild, manifest/export lints, installed CLI/doctor, permissions, GTK/Xvfb smoke, and uninstall with `--delete-data` passed | A non-blocking icon-theme warning remains in the container log |
| Public stable release | Existing `v1.0.0` remains the historical public asset | It points to an older source commit and must not be described as containing the current fixes |

The candidate has not been promoted to a new public tag or release in this
register. A new release must repeat the source, package, human desktop, and
downloaded-asset gates in `docs/packaging/RELEASE-CHECKLIST.md`.

## Open acceptance gates

- A real Debian/Ubuntu Linux desktop report covering X11/Wayland, PipeWire or
  PulseAudio, launcher, permissions, default and explicit microphone capture,
  short speech, stop/flush, copy, portal export, history, and data removal.
- One tester-owned Groq transcription and translation run, including invalid
  key, offline, rate-limit, missing-device, and saturated-queue behavior.
- Five consented first-use sessions, with failures retained in the report and
  no credentials, recordings, transcript text, or private paths collected.
- A downloaded release asset installed on a clean profile, followed by the
  same desktop checks and an update/removal check.
- Real GTK screenshots and the final demonstration video. The video phase is
  intentionally last and cannot use the synthetic site tour as evidence.

## Evidence hygiene

Record the exact commit, workflow URL, package filename/checksum, environment,
date, command or scenario, and result. Keep keys, audio, transcript content,
device serials, private paths, and full environment dumps out of this file and
out of public issues. “Not recorded”, “failed”, “skipped”, and “passed” are
different states.
