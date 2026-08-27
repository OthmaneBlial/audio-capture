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

## Fake provider contract fixture

`tests/fake_provider_fixture.py` exposes `FakeTranscriptionProvider`, a
test-only double of the shared `TranscriptionProvider` contract. Import it from
unit tests; do not ship it in the runtime application package.

```python
from fake_provider_fixture import FakeProviderConfig, FakeTranscriptionProvider

states = []
provider = FakeTranscriptionProvider(
    FakeProviderConfig(default_text="test transcript", max_pending_requests=2),
    on_request_state=lambda request_id, state, detail: states.append(state),
)
try:
    future = provider.transcribe_async(b"\x00\x00" * 80)
    assert future is not None
    assert future.result(timeout=2) == "test transcript"
finally:
    provider.close(wait=True)
```

The fixture covers:

- declared capabilities (languages, translation, cancellation, limits)
- a human-readable `ProviderBoundary` (destination, credential, storage)
- deterministic `pending` / `complete` / `error` / `cancelled` request states
- bounded-queue rejection with a normalized `queue_full` error
- normalized authentication, rate-limit, and network error codes
- request-state tracking that stores byte lengths and lifecycle labels only -- never PCM frames or transcript text

Drive scripted failures with the `outcomes=` sequence, and block workers with
`hold_event=` when a test needs an in-flight request. See
`tests/test_fake_provider_fixture.py` for the focused contract tests. The
fixture must not open a socket, enumerate a microphone, read an API key, or
launch a local model process.
