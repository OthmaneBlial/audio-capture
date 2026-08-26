# Data flow and privacy boundary

Voice Transcriber makes the active transcription boundary visible on first run,
in Settings, and on the main desk. Local voice activity detection always happens
before a provider receives a completed segment.

| Data | Where it exists | Groq cloud | Experimental local | App persistence |
| --- | --- | --- | --- | --- |
| Raw 30 ms microphone frames | Bounded memory queue | Never sent directly | Never sent to a network provider | None |
| Completed speech segment | PCM/WAV in memory | Sent over HTTPS after silence closes it | Passed to user-supplied `whisper-cli` through Linux `memfd` | None |
| Silence | Local VAD only | Not submitted | Not submitted | None |
| Transcript | Editable GTK buffer | Not sent elsewhere by the app | Not sent elsewhere by the app | Explicit export; opt-in text history |
| Request state | Bounded status tracker | Local metadata | Local metadata | None; no audio/text |
| API key | Environment, `.env`, or owner-only config | Used for authenticated requests | Not used | Only when user saves it |
| CLI/model paths | Owner-only config | Not used | Used to launch the selected local files | Saved when user chooses local setup |
| Preferences/history | Owner-only local files | Never | Never | Explicit settings; history off by default |

## Groq cloud path

```text
microphone -> bounded frames -> local VAD -> completed segment
  -> in-memory WAV/HTTPS request -> Groq -> editable transcript
```

Provider processing and retention follow the user's account and the provider's
current policies. This project makes no retention promise it cannot enforce.

## Experimental local path

```text
microphone -> bounded frames -> local VAD -> completed segment
  -> in-memory WAV -> /proc/self/fd/<memfd> -> user-supplied whisper-cli/model
  -> editable transcript
```

This path is disabled inside the current Flatpak and without
`VOICE_TRANSCRIBER_EXPERIMENTAL_LOCAL=1`. It downloads nothing, writes no raw
audio file, and is not labelled supported/offline until its model, hardware,
packaging, and first-success evidence are published.

Both paths end in explicit edit/copy/clear/export actions. Optional transcript
history is text-only, disabled by default, retention-limited, and clearable.
The app has no analytics, crash reporter, background upload, cloud transcript
history, or automatic sync.
