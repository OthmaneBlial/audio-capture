# Data flow and privacy boundary

Voice Transcriber is privacy-explicit, not fully offline. Voice activity
detection happens locally; completed speech segments are sent to the active
Groq transcription endpoint.

| Data | Where it exists | When it leaves the device | Persistence controlled by Voice Transcriber |
| --- | --- | --- | --- |
| Raw 30 ms microphone frames | Bounded in-memory capture queue | Never directly | Not persisted |
| Detected speech segment | In memory as PCM, then WAV | Sent to Groq after the segment closes | Not persisted |
| Silence | Local VAD only | Never sent as a transcription request | Not persisted |
| Transcript text | GTK memory buffer | Not sent elsewhere by the app | Saved only on explicit export |
| Groq API key | Environment, `.env`, or owner-only config | Used for authenticated Groq requests | Saved only when the user chooses Settings |
| Preferences | Owner-only local config | Never | Persisted locally |
| Input signal meter | In-memory RMS value | Never | Not persisted |

The current application has no analytics, crash reporter, background upload,
audio library, cloud transcript history, or automatic sync.

## Session path

```text
microphone
  -> bounded local frame queue
  -> local voice activity detector
  -> completed in-memory speech segment
  -> in-memory WAV encoding
  -> Groq Whisper request
  -> transcript in the GTK buffer
  -> explicit copy, clear, or local export
```

Provider-side processing and retention are governed by the provider account and
its current policies. Users should review Groq's documentation for their own
account and jurisdiction; this project does not make a vendor-retention promise
it cannot enforce.
