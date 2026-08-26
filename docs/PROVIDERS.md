# Provider capability and boundary matrix

| Contract | Groq cloud | Local whisper.cpp prototype |
| --- | --- | --- |
| Status | Supported cloud path; current Flatpak | Experimental source install only; disabled in Flatpak |
| Audio destination | Completed segment to Groq over HTTPS | Linux memory-backed descriptor to user-supplied local process |
| Credential | User-managed Groq API key | None |
| Model | `whisper-large-v3-turbo` | User-supplied GGML model; exact capabilities vary |
| App language choices | Auto, EN, FR, ES, DE, IT, PT, AR, ZH | Same UI choices, constrained by the selected model |
| Translate to English | Available | CLI capability exposed; model/build dependent |
| Queue | Bounded, up to four pending requests | Bounded, up to two with one worker |
| Cancellation | Queued work cancels; active HTTP ends at timeout | Queued work cancels; active process is terminated on close/reconfigure |
| Normalized errors | Auth, rate limit, network, queue, malformed/oversized audio | Setup, timeout, process/model mismatch, queue, malformed/oversized audio |
| Raw-audio files written by app | No | No |
| Automatic downloads | No | No |

The UI reads this same distinction as a visible data-boundary label. Provider
selection is offered only when the experimental source-session flag is present;
otherwise users see the supported Groq path without a non-functional promise.

The benchmark contract lives in [`benchmarks/README.md`](../benchmarks/README.md).
A provider result is meaningful only with corpus checksum/composition, exact
model/build, hardware, WER numerator/denominator, latency percentiles, and failed
samples. The local prototype remains unsupported until that evidence and the
same Flatpak/real-device first-success gate as Groq both pass.
