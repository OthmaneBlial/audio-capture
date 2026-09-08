# Data flow and privacy boundary

The Rust application keeps speech local until local VAD closes a completed
segment. The user must configure a provider key and confirm the cloud boundary
before that segment can leave the process.

| Data | Local Rust process | Groq cloud | App persistence |
| --- | --- | --- | --- |
| Raw microphone frames | Bounded queue only | Never sent directly | None |
| Completed speech segment | PCM16/WAV in memory | Sent over HTTPS after consent | None |
| Silence and input level | Local VAD/RMS calculation | Not submitted | None |
| Transcript and request state | Editable ordered document | Not sent elsewhere by the app | Explicit export; optional text history |
| API key | Environment or saved settings | Authentication header | Saved only when the user chooses |
| Device identity | Opaque local fingerprint | Never sent as metadata | Saved with settings |

```text
microphone -> bounded frames -> local VAD -> completed segment
  -> in-memory WAV/HTTPS request -> Groq -> ordered editable transcript
```

Provider processing and retention follow the user's account and the provider's
current policy. The project does not make a retention promise it cannot enforce.
The request worker applies a timeout, rejects oversized responses, and
normalizes authentication, rate-limit, network, and malformed-response errors
without returning provider bodies or credentials to the UI.

`--test-microphone`, the input meter, VAD, configuration validation, and export
building do not contact Groq. The test command discards all captured frames
after reporting a count and peak level. Optional history stores transcript text
only, is disabled by default, retention-limited, and clearable.
