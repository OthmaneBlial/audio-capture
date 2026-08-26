# Develop without an API key

Most work is deliberately possible without Groq, a microphone, GTK, or a local
Whisper model. Tests inject native and provider boundaries rather than reaching
real services.

## Fast deterministic loop

On a machine with Python 3.9 or newer:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install ruff
python -m unittest discover -s tests -v
ruff check .
python -m compileall -q audio transcription ui config.py diagnostics.py \
  exports.py history.py main.py onboarding.py platform_capabilities.py transcript.py
```

The standard-library tests provide fake PyAudio streams, HTTP responses,
subprocesses, clipboard operations, history clocks, and GTK boundaries. They
must not contact Groq or enumerate the contributor's real microphone.

## Inspect the app without accepting a provider boundary

The full native application needs the packages documented in the root README.
After installing them, launch without `GROQ_API_KEY`. You can inspect first-run
setup, Settings, device discovery, the input meter, privacy copy, and provider
choices. **Start listening** remains unavailable until the selected provider is
valid; there is no fake-transcript runtime mode.

```bash
python main.py --check-config
python main.py --doctor --json
python main.py
```

An incomplete config exits with the documented non-zero status. That is an
expected contract, not a failed development environment.

## When a real boundary is required

Use your own disposable provider key only for the manual cloud gate. Never put
it in a command, issue, test, screenshot, or committed file. Physical
microphone, Wayland/X11, and PipeWire/PulseAudio results belong in the
[structured compatibility form](https://github.com/OthmaneBlial/audio-capture/issues/new?template=compatibility.yml), after reviewing the privacy warning.
