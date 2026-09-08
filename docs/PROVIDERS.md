# Provider capability and boundary matrix

The current Rust desktop exposes one supported transcription provider. A
provider is considered supported only after its implementation, live request
gate, error behavior, and platform packaging have evidence in this repository.

| Contract | Groq cloud |
| --- | --- |
| Status | Implemented boundary; live key/request gate is a separate validation step |
| Audio destination | Completed segment to Groq over HTTPS |
| Credential | User-managed Groq API key |
| Model | `whisper-large-v3-turbo` transcription; `whisper-large-v3` translation |
| Language | Automatic detection or configured UI language |
| Translation | Optional English translation |
| Queue | Four in-memory jobs, one worker |
| Cancellation | Shutdown closes admission; active HTTP ends at timeout |
| Errors | Consent, key, queue, auth, rate-limit, network, malformed/oversized audio |
| Raw-audio files written by app | No |
| Automatic downloads | No |

An offline provider is not advertised by the current UI or release artifacts.
Provider tests cover malformed audio, consent/key checks, WAV headers, bounded
admission, ordering, and normalized errors without contacting a live service.
A real provider report must use a disposable user key and must never include
that key, request body, or transcript in an issue.
