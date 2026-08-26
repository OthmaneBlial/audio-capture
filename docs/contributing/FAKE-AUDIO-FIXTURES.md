# Fake audio and provider fixtures

Tests use small synthetic values and injected boundaries. A fixture should
prove one contract without resembling a real recording or containing spoken
content.

## PCM fixtures

Voice Transcriber expects signed 16-bit, mono PCM at 16 kHz. Construct only the
frames a test needs:

```python
import struct

silence = b"\x00\x00" * 480              # one 30 ms frame
tone_like_level = struct.pack("<480h", *([1200] * 480))
```

Constant samples are useful for queue, RMS, size, and lifecycle tests. They are
not realistic speech and must never be described as an accuracy fixture.

## Native boundaries

Follow `tests/test_audio_capture.py`: inject a small PyAudio-compatible factory
with deterministic device metadata, a stream that records close/stop calls,
and no access to the host audio service. VAD behavior belongs in
`tests/test_vad.py`; keep timing and frame counts explicit.

## Provider boundaries

Follow `tests/test_transcription.py` and `tests/test_provider.py`: inject an HTTP
opener or process factory, inspect the outbound contract, and return a
synthetic phrase such as `test transcript`. Cover normalized success, timeout,
authentication, rate-limit, invalid-body, cancellation, and bounded-queue
states without opening a socket.

## Fixture rules

- Generate bytes in the test unless a reviewed binary fixture is materially
  clearer.
- Never commit captured human audio, a provider response dump, an API key, a
  home path, or a real transcript.
- Assert both the result and cleanup: streams, responses, descriptors, pools,
  and subprocesses must close.
- A benchmark corpus is a different artifact. It must have a compatible
  license, pinned checksum, documented sample selection, and an unedited
  receipt as specified in [`benchmarks/README.md`](../../benchmarks/README.md).
