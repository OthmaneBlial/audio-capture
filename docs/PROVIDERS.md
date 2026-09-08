# Provider capability and boundary matrix

The Rust rewrite currently exposes one provider. A provider is considered
supported only after its implementation, live request gate, error behavior, and
platform packaging have evidence in this repository.

| Contract | Groq cloud (Rust) | whisper.cpp (legacy Python) |
| --- | --- | --- |
| Status | Implemented boundary; live key/request gate pending | Experimental migration material only |
| Audio destination | Completed segment to Groq over HTTPS | User-supplied local process on Linux |
| Credential | User-managed Groq API key | None |
| Model | `whisper-large-v3-turbo` transcription; `whisper-large-v3` translation | User-supplied model/build |
| Language | Automatic detection or configured UI language | Depends on selected model |
| Translation | Optional English translation | Legacy adapter behavior |
| Queue | Four in-memory jobs, one worker | Legacy Python limits |
| Cancellation | Shutdown closes admission; active HTTP ends at timeout | Legacy process lifecycle |
| Errors | Consent, key, queue, auth, rate-limit, network, malformed/oversized audio | Legacy setup/process errors |
| Raw-audio files written by app | No | No claim for the legacy adapter |
| Automatic downloads | No | No |

The Rust UI does not advertise offline transcription. A future local Rust
provider must reuse the same explicit capability and data-boundary contract,
then pass a separate packaging and first-success gate before appearing here as
supported.

Provider tests use malformed audio, key/consent checks, WAV headers, and
bounded admission without contacting a live service. A real provider report
must use a disposable user key and must never include that key, request body, or
transcript in an issue.
