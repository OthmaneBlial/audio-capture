# Contributing

Thanks for helping make Voice Transcriber easier to trust and use.

## Prerequisites

- Python 3.9+
- Debian/Ubuntu development libraries listed in [README.md](README.md#installation-details) for the full GTK/audio application
- `ruff` for the local lint check

## Setup and verification

```bash
git clone https://github.com/OthmaneBlial/audio-capture.git
cd audio-capture
./setup.sh
source venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m unittest discover -s tests -v
ruff check .
```

The core workflow is capture → VAD → bounded transcription queue → GTK. Keep native microphone work out of unit tests; inject or fake external boundaries so contributors can test without hardware or credentials.

## Pull requests

- Keep a pull request focused and explain the user-facing behavior it protects.
- Add or update tests for reliability, configuration, security, or parsing changes.
- Do not commit `.env`, API keys, recordings, exported transcripts, or generated environment folders.
- Run the checks above and note any hardware-only verification you could not perform.
- Use clear, imperative commit messages such as `fix: bound pending transcription requests`.

For vulnerabilities, use the private process in [SECURITY.md](SECURITY.md), not a pull request or public issue.
