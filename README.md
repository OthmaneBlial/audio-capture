# Voice Transcriber

[![CI](https://github.com/OthmaneBlial/audio-capture/actions/workflows/ci.yml/badge.svg)](https://github.com/OthmaneBlial/audio-capture/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/OthmaneBlial/audio-capture?display_name=tag)](https://github.com/OthmaneBlial/audio-capture/releases)
[![License](https://img.shields.io/github/license/OthmaneBlial/audio-capture)](LICENSE)

**Turn spoken notes into editable text without managing audio files.** Voice Transcriber is a focused Linux GTK desktop app: it listens to your microphone, detects speech locally, and sends only completed speech segments to Groq Whisper for fast transcription.

**[Visit the project site →](https://othmaneblial.github.io/audio-capture/)**

> Privacy boundary: microphone frames and transcript state stay in the app's memory. Completed speech segments are sent to Groq for transcription; this is not an offline transcription engine. Exported transcripts are saved locally only when you choose to export.

## Why it is useful

The fast path is deliberately short: configure one key, click **Start listening**, speak, then copy or export the result. Voice activity detection avoids uploading silence, and the app keeps a bounded work queue so a slow connection cannot spawn unlimited background requests.

- Real microphone capture: 16 kHz mono PCM, tuned for Whisper.
- Local speech detection with `webrtcvad`; silence is never sent as a transcription request.
- Groq Whisper transcription or translation to English.
- A keyboard-friendly recording desk with session status, copy, export, adjustable text, and always-on-top mode.
- Clear failure guidance for missing keys, connectivity, rate limits, microphone access, and a full request queue.
- No simulated transcripts. If configuration is incomplete, the app says so.

## Quick start

Voice Transcriber currently supports Debian/Ubuntu Linux desktops with GTK 3 and a working microphone.

```bash
git clone https://github.com/OthmaneBlial/audio-capture.git
cd audio-capture
./setup.sh
cp .env.example .env
# Edit .env and set GROQ_API_KEY to a newly created Groq API key.
source venv/bin/activate
python main.py --check-config
python main.py
```

Inside the app, use **Start listening** (or `Ctrl+Enter`), then **Copy** (`Ctrl+Shift+C`) or **Export**. The Settings menu supports language selection, translation, font size, opacity, and an API key saved in a local owner-only configuration file.

## Installation details

`setup.sh` installs required Debian/Ubuntu system libraries, creates `venv/`, and installs Python dependencies. If you prefer manual setup:

```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv python3-gi gir1.2-gtk-3.0 \
  portaudio19-dev python3-pyaudio libcairo2-dev libgirepository1.0-dev pkg-config
python3 -m venv venv --system-site-packages
source venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

To add an application-menu entry after setup:

```bash
./install.sh
```

## Configuration

Settings resolve in this order:

```text
defaults < ~/.config/voice-transcriber/config.json < environment variables
```

`GROQ_API_KEY` has the highest precedence. It is never logged. Local settings are atomically written with owner-only file permissions; `.env` is ignored by Git. `python main.py --check-config` exits with status `0` when a plausible API key is available and `2` when one is missing.

| Setting | Where | Notes |
| --- | --- | --- |
| `GROQ_API_KEY` | environment or `.env` | Required to transcribe. Create and control this key in Groq. |
| Language | Settings | Auto-detect by default; English, French, Spanish, German, Italian, Portuguese, Arabic, and Chinese are offered. |
| Translate to English | Settings | Uses Groq's translation endpoint. |
| Keep on top | Window control | Helpful while dictating into another app. |

## Architecture

```text
Microphone → bounded frame queue → local VAD → bounded API worker pool → GTK transcript
```

The UI runs on GTK's main loop. Capture and VAD run away from it, while a two-worker transcription pool accepts only a small number of pending segments. See [the architecture note](docs/ARCHITECTURE.md) for lifecycle and failure behavior.

## Troubleshooting

| What you see | What to do |
| --- | --- |
| “No Groq API key is configured” | Set `GROQ_API_KEY` in `.env` or add a key in Settings, then start again. |
| The microphone cannot open | Verify a microphone is connected and grant microphone access to your desktop session. On Linux, check PipeWire/PulseAudio settings. |
| “Could not reach Groq” | Check your network connection and Groq service access. The app leaves the session running so you can continue after recovery. |
| Rate-limit message | Wait a few seconds before speaking more; the request queue is intentionally bounded. |
| PyAudio cannot install | Ensure `portaudio19-dev` is installed, then recreate the virtual environment with `--system-site-packages`. |

## Development

```bash
python3 -m unittest discover -s tests -v
ruff check .
python3 -m compileall -q audio transcription ui config.py main.py
```

The unit suite fakes external native/API boundaries; it exercises configuration precedence and permissions, VAD segmentation, error normalization, WAV conversion, and the request bound without requiring a microphone or a Groq account. Read [CONTRIBUTING.md](CONTRIBUTING.md) before opening a pull request.

## Security and responsible disclosure

Please do not report security issues in public GitHub issues. Follow [SECURITY.md](SECURITY.md) for private reporting guidance. If a credential ever reached Git history, rotate it in the issuing service even after removing the file from the current branch.

## Roadmap

- [ ] Optional configurable input-device picker.
- [ ] Configurable local transcript retention with an explicit opt-in.
- [ ] Distribution packages for supported Linux desktop environments.

These are not implemented in `v0.1.0`.

## License

Released under the [MIT License](LICENSE).
