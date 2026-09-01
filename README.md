# Voice Transcriber

[![Latest release](https://img.shields.io/github/v/release/OthmaneBlial/audio-capture?display_name=tag&label=release)](https://github.com/OthmaneBlial/audio-capture/releases/latest)
[![Linux](https://img.shields.io/badge/platform-Linux-315532)](docs/SUPPORT.md)
[![MIT license](https://img.shields.io/github/license/OthmaneBlial/audio-capture)](LICENSE)

**A review-first dictation desk for Linux. Speak a draft, edit the result, then
copy or export it when it is ready.**

[Download v1.0 for x86_64 Linux](https://github.com/OthmaneBlial/audio-capture/releases/download/v1.0.0/voice-transcriber-1.0.0-x86_64.flatpak)
· [Open the product tour](https://othmaneblial.github.io/audio-capture/#proof)
· [Inspect the privacy boundary](docs/PRIVACY.md)
· [Read the docs](https://othmaneblial.github.io/audio-capture/docs.html)

![Voice Transcriber guided tour: ready, listening, and transcript states](site/assets/voice-transcriber-tour.gif)

> The tour uses synthetic sample text and reproducible previews of the current
> GTK interface. The application never inserts a fake transcript.

## Why this exists

Most voice-typing tools try to put words directly into whichever app has focus.
Voice Transcriber gives the words a checkpoint first. It is deliberately built
for prompts, emails, tickets, notes, and other drafts you want to review before
they reach another application.

```text
microphone -> local speech detection -> transcription -> edit -> copy or export
```

The supported package uses Groq for transcription, so this is **privacy-explicit
cloud dictation—not an offline transcription claim**. Silence detection and the
input meter stay local; completed speech segments cross a visible provider
boundary only after you configure a key and confirm that boundary.

| Voice Transcriber is | Voice Transcriber does not pretend to be |
| --- | --- |
| A focused review-and-copy workspace | Invisible system-wide typing |
| A lightweight path with no model download | A packaged offline engine |
| Explicit about what stays local and what is sent | “100% private” cloud transcription |
| Available today as an x86_64 Flatpak bundle | A Flathub, ARM, macOS, or Windows release |

## Install v1.0

The release is a checksum-verifiable `x86_64` Flatpak bundle. Add Flathub for
the GNOME runtime, download the two release files, verify them, and install:

```bash
flatpak remote-add --user --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo
curl -fLO https://github.com/OthmaneBlial/audio-capture/releases/download/v1.0.0/voice-transcriber-1.0.0-x86_64.flatpak
curl -fLO https://github.com/OthmaneBlial/audio-capture/releases/download/v1.0.0/voice-transcriber-1.0.0-x86_64.flatpak.sha256
sha256sum --check voice-transcriber-1.0.0-x86_64.flatpak.sha256
flatpak install --user ./voice-transcriber-1.0.0-x86_64.flatpak
flatpak run io.github.othmaneblial.audio_capture
```

This standalone bundle does not add an application update remote; update it by
installing a newer verified release. See the [complete install, update, and
removal guide](docs/packaging/FLATPAK.md).

You can inspect the interface, microphone picker, signal meter, diagnostics,
and data boundary without a key. To transcribe, add a Groq API key you control
in Settings. **Start listening** remains blocked until the selected provider is
ready—there is no demo-output fallback hidden in the app.

## The 30-second workflow

1. **Pick a microphone.** Confirm the source with a local, non-recording meter.
2. **Speak naturally.** Local VAD filters silence and closes each speech segment.
3. **Review the result.** Pending, completed, and failed segments remain visible
   while the transcript stays editable.
4. **Use the words.** Copy the desk, clear it, or export plain text, Markdown,
   or a timestamped note to a destination you choose.

Keyboard controls cover start/stop, copy, undo/redo, text sizing, and focused
push-to-talk. There is no global-shortcut or active-window insertion claim yet.

## What stays local and what leaves

| Data | Current behavior |
| --- | --- |
| Microphone frames | Held in a bounded memory queue; never saved by the app |
| Voice activity detection | Runs locally; silence is not submitted |
| Completed speech segment | Encoded in memory and sent to Groq in the supported cloud path |
| Input signal meter | Calculated locally; never persisted or uploaded |
| Live transcript | Remains in the GTK desk until copy, clear, export, or exit |
| Optional history | Text only, off by default, retention-limited, and clearable |
| Settings and saved key | Owner-only local configuration where POSIX permissions apply |
| Analytics and crash reporting | None |

Provider-side processing is controlled by the provider account and its current
policies. Read the [complete data flow](docs/DATA-FLOW.md), [privacy
notice](docs/PRIVACY.md), and [threat model](docs/THREAT-MODEL.md) before using
the app with sensitive speech.

## What ships today

- Real microphone discovery and persistent device selection.
- Local `webrtcvad` speech segmentation and a bounded capture queue.
- Groq Whisper transcription with optional translation to English.
- A bounded provider worker pool with normalized network, key, rate-limit,
  malformed-audio, and full-queue failures.
- An editable transcript with undo/redo, segment states, copy, clear, and three
  explicit export formats.
- Optional text-only history with 1–365 day retention and per-entry deletion.
- A keyboard-friendly GTK desk with adjustable type, opacity, and keep-on-top.
- Stable configuration, device, readiness, and privacy-safe doctor commands.
- Release checksum, test report, CycloneDX SBOM, and Sigstore provenance.

The source tree also contains an **experimental** `whisper.cpp` adapter behind
an explicit feature flag. You must supply the binary and GGML model yourself;
it is disabled in the v1 Flatpak and is not advertised as supported offline
operation. See the [provider matrix](docs/PROVIDERS.md).

## Evidence and known limits

| Surface | Evidence-backed status |
| --- | --- |
| Package | `v1.0.0` x86_64 Flatpak built, linted, installed, smoke-tested, and mapped to its source tag |
| Automated behavior | 68 deterministic tests currently pass without a key, microphone, model, or network |
| Desktop UI | GTK 3; designed for Debian/Ubuntu-style Linux desktops |
| Audio route | PyAudio through the host PipeWire/PulseAudio compatibility path |
| Physical compatibility | Real PipeWire/PulseAudio plus Wayland/X11 reports are still being collected |
| Delivery | Clipboard and explicit local export; no simulated typing into other apps |

Automated boundary tests are not real microphone evidence. The [support
matrix](docs/SUPPORT.md) separates what has been proven from what still needs a
physical Linux session, and the open [compatibility issue
form](.github/ISSUE_TEMPLATE/compatibility.yml) collects only privacy-safe data.

## Source installation details

The Flatpak is the user path. This source setup is for development on
Debian/Ubuntu-style systems:

```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv python3-gi gir1.2-gtk-3.0 \
  portaudio19-dev python3-pyaudio libcairo2-dev libgirepository1.0-dev pkg-config
python3 -m venv venv --system-site-packages
source venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
cp .env.example .env
python main.py --check-config
python main.py --list-devices
python main.py
```

Settings resolve as:

```text
defaults < ~/.config/voice-transcriber/config.json < environment variables
```

`GROQ_API_KEY` has the highest precedence and is never logged. Run
`python main.py --doctor` for local readiness checks; only the explicit
`--doctor --probe-provider` option contacts Groq, and it sends no audio.

## Develop without a microphone or key

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
ruff check .
python -m unittest discover -s tests -v
python -m compileall -q audio transcription ui benchmarks scripts config.py main.py
```

The suite injects native and provider boundaries and exercises capture, VAD,
transcription, configuration, privacy regressions, history, export, diagnostics,
provider contracts, benchmark math, and release tooling. Start with the
[contributor map](docs/contributing/README.md) or choose a scoped
[`good first issue`](https://github.com/OthmaneBlial/audio-capture/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22).

## What comes next

The next meaningful product gates are a discoverable/updateable Linux package,
physical desktop/audio compatibility reports, a supported local provider with
model lifecycle, and portal-backed global shortcuts. They are tracked in the
[roadmap](ROADMAP.md) and will not become claims before their evidence exists.

If the review-first workflow fits your Linux setup, **star the repository and
tell us your distro, desktop session, and audio route** through the structured
[compatibility report](https://github.com/OthmaneBlial/audio-capture/issues/new?template=compatibility.yml).

Released under the [MIT License](LICENSE). Security reports belong in the
private process described by [SECURITY.md](SECURITY.md), never in a public issue.
