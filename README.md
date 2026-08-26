# Voice Transcriber

[![CI](https://github.com/OthmaneBlial/audio-capture/actions/workflows/ci.yml/badge.svg)](https://github.com/OthmaneBlial/audio-capture/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/OthmaneBlial/audio-capture?display_name=tag)](https://github.com/OthmaneBlial/audio-capture/releases)
[![License](https://img.shields.io/github/license/OthmaneBlial/audio-capture)](LICENSE)

**Dictate a thought, review it, and paste it anywhere on Linux.** Voice
Transcriber is a focused GTK desktop desk for notes, prompts, emails, tickets,
and drafts. It detects speech locally, sends only completed speech segments to
Groq Whisper, and leaves the resulting text ready to copy or explicitly export.

**[Visit the project site](https://othmaneblial.github.io/audio-capture/)** ·
**[Read the data flow](docs/DATA-FLOW.md)** ·
**[Check supported environments](docs/SUPPORT.md)**

![Guided Voice Transcriber product preview showing ready, listening, and completed transcript states](site/assets/voice-transcriber-tour.gif)

> This is a guided preview made from the current native interface design with
> synthetic sample text. Voice Transcriber does not generate a simulated
> transcript inside the application.

## The short path

1. Choose a detected microphone and confirm it with the local input meter.
2. Start listening and speak naturally.
3. Review the transcript as completed segments return.
4. Copy the text into your work, clear it, or export it deliberately.

There is no audio library to organise and no continuous background upload. A
bounded capture queue and bounded API worker pool keep failure and memory use
predictable when a device or connection is slow.

## What stays local and what leaves

Voice Transcriber is privacy-explicit, not an offline transcription engine.

| Surface | Current behaviour |
| --- | --- |
| Microphone frames | Held in a bounded in-memory queue; not saved by the app |
| Voice activity detection | Runs locally; silence is not submitted for transcription |
| Completed speech segment | Encoded in memory and sent to Groq Whisper |
| Input signal meter | Calculated locally and never persisted |
| Transcript | Remains in the GTK buffer until you copy, clear, or export it |
| Export | Writes a local UTF-8 text file only after you choose a destination |
| Settings and API key | Saved only when you choose to save them, in an owner-only local config where supported |
| Analytics and crash reporting | None |

Read [the complete data-flow table](docs/DATA-FLOW.md) before using the app with
sensitive speech. Provider-side handling is controlled by the provider account
and its current policies, not by this application.

## See the interface before configuring a key

You can open the application, inspect Settings, discover microphone inputs, and
read the privacy boundary without configuring Groq. **Start listening** remains
blocked until a plausible API key is available; the app never substitutes a
fake transcription.

```bash
git clone https://github.com/OthmaneBlial/audio-capture.git
cd audio-capture
./setup.sh
source venv/bin/activate
python main.py --list-devices
python main.py
```

The current supported source-install path is Debian/Ubuntu Linux with GTK 3 and
a working microphone. See [the evidence-based support matrix](docs/SUPPORT.md)
for the distinction between supported, expected, and unsupported environments.

## Configure a real transcription session

Create a Groq API key that you control, then use either the environment or the
owner-only Settings screen:

```bash
cp .env.example .env
# Edit .env and set GROQ_API_KEY to your newly created key.
source venv/bin/activate
python main.py --check-config
python main.py --list-devices
python main.py
```

Inside the app, choose a microphone from **Settings** if needed, then select
**Start listening** or press `Ctrl+Enter`. The input meter confirms that the
selected source is receiving audio without saving a recording. Use **Copy**
(`Ctrl+Shift+C`) or **Export** when the transcript is ready.

## Current capabilities

- Real microphone discovery and selection, including a machine-readable
  `--list-devices --json` command.
- A live, rate-limited local signal meter that does not record audio.
- Local speech detection with `webrtcvad`; silence is not sent as a
  transcription request.
- Groq Whisper transcription and optional translation into English.
- A keyboard-friendly recording desk with session state, copy, export,
  adjustable text, opacity, and always-on-top mode.
- Clear failures for missing keys, connectivity, rate limits, microphone
  access, malformed audio, and a full request queue.
- Atomic settings writes and owner-only configuration permissions where the
  operating system supports them.

## Installation details

`setup.sh` installs required Debian/Ubuntu system libraries, creates `venv/`,
and installs Python dependencies. For a manual setup:

```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv python3-gi gir1.2-gtk-3.0 \
  portaudio19-dev python3-pyaudio libcairo2-dev libgirepository1.0-dev pkg-config
python3 -m venv venv --system-site-packages
source venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Add an application-menu entry after the environment is ready:

```bash
./install.sh
```

This release does not yet provide a Flatpak, Debian package, AppImage, or
automatic updater. Source archives on the release page are not installable app
packages. Packaging work and its acceptance gates are tracked in
[ROADMAP.md](ROADMAP.md).

## Configuration

Settings resolve in this order:

```text
defaults < ~/.config/voice-transcriber/config.json < environment variables
```

`GROQ_API_KEY` has the highest precedence and is never logged. Local settings
are atomically written with owner-only file permissions; `.env` is ignored by
Git. `python main.py --check-config` exits with status `0` when a plausible key
is available and `2` when one is missing.

| Setting | Where | Notes |
| --- | --- | --- |
| `GROQ_API_KEY` | Environment or `.env` | Required to transcribe; use a key you control |
| Language | Settings | Auto-detect, English, French, Spanish, German, Italian, Portuguese, Arabic, and Chinese |
| Translate to English | Settings | Uses the provider translation endpoint |
| Microphone input | Settings or `--device INDEX` | Saved selection is reused; CLI option overrides it for one launch |
| Keep on top | Main window | Keeps the desk visible beside other work |

## Stable diagnostic commands

```bash
python main.py --check-config
python main.py --list-devices
python main.py --list-devices --json
python main.py --device 2
python main.py --version
python main.py --help
```

`--check-config` never prints the key. `--list-devices --json` prints device
metadata only and does not contact Groq.

## Architecture

```text
Microphone -> bounded frame queue -> local VAD -> bounded API worker pool -> GTK transcript
```

The UI runs on GTK's main loop. Capture and VAD run away from it, while a
two-worker transcription pool accepts only a small number of pending segments.
See [the architecture note](docs/ARCHITECTURE.md) for lifecycle and failure
behaviour.

## Troubleshooting

| What you see | What to do |
| --- | --- |
| “No Groq API key is configured” | Set `GROQ_API_KEY` in `.env` or add a key in Settings, then start again |
| The microphone cannot open | Verify a microphone is connected and allowed in the desktop session; check PipeWire/PulseAudio settings |
| The wrong microphone is active | Run `python main.py --list-devices`, choose it in Settings, and start a new session |
| “Could not reach Groq” | Check the network, key, and provider access; the session remains recoverable |
| Rate-limit message | Wait before speaking more; the request queue is deliberately bounded |
| PyAudio cannot install | Install `portaudio19-dev`, then recreate the venv with `--system-site-packages` |

When opening a device issue, follow [the minimal safe report](docs/SUPPORT.md#hardware-verification-report).

## Development

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m unittest discover -s tests -v
ruff check .
python -m compileall -q audio transcription ui config.py main.py
```

The unit suite fakes external native/API boundaries. It exercises configuration
precedence and permissions, microphone discovery and selection, local meter
normalisation, VAD segmentation, error normalisation, WAV conversion, and the
request bound without requiring a microphone or a Groq account.

Read [CONTRIBUTING.md](CONTRIBUTING.md) and the
[Code of Conduct](CODE_OF_CONDUCT.md) before opening a pull request.

## Security and responsible disclosure

Do not report credentials, recordings, transcripts, or suspected privacy flaws
in a public issue. Follow [SECURITY.md](SECURITY.md) for private reporting. If a
credential ever reached Git history, rotate it in the issuing service even
after removing the current file.

## Roadmap

The dependency-ordered [product roadmap](ROADMAP.md) prioritises public proof,
normal Linux packaging, daily dictation, provider choice, verifiable privacy,
and a sustainable contribution loop.

## License

Released under the [MIT License](LICENSE).
