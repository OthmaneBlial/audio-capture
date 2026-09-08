# Privacy notice

Last reviewed: 8 September 2026

Voice Transcriber is a local desktop application. It has no operator account,
analytics, advertising, crash-report upload, transcript-sync service, or
project-controlled server. Privacy still depends on the transcription provider,
your operating system, and files or programs you explicitly choose.

## What the application processes

| Data | Purpose | Default persistence | Destination |
| --- | --- | --- | --- |
| Microphone PCM frames | Detect speech and create segments | Bounded memory only | Local capture/VAD |
| Completed speech segment | Transcription | No app-created audio file | Groq HTTPS after consent |
| Transcript | Review, edit, copy, export | Current desk memory | Clipboard/export only after action |
| Optional text history | Retrieve recent transcripts | Off by default; 1–365 days | Local user data directory |
| Groq API key | Authenticate cloud requests | Environment or saved settings | Request header |
| Preferences | Restore UI choices | Local config | Local only |

The app calculates the input meter from an in-memory RMS value. Request states
contain status metadata only, not audio or transcript text. It does not
continuously record, run after exit, or simulate keyboard input.

## Groq cloud mode

After local VAD closes a segment, the app sends an in-memory WAV payload, model
identifier, and language/translation choice to Groq over HTTPS. It does not use
batch, file-storage, or fine-tuning APIs. Groq controls processing after receipt;
review its current [speech-to-text documentation](https://console.groq.com/docs/speech-to-text),
[customer-data documentation](https://console.groq.com/docs/your-data), and
[privacy policy](https://groq.com/privacy-policy) for your account and
jurisdiction. Those pages can change, so this project does not promise a vendor
retention period it cannot enforce.

## Text storage and deletion

- The live transcript disappears when cleared or when the app closes, unless
  opt-in history or an explicit export exists.
- History is text-only, bounded, retention-limited, and clearable in Settings.
- Exports require a visible destination and confirmation. Copies then follow the
  clipboard, filesystem, backup, and downstream application boundaries.
- The application never adds raw audio to history or exports.

## Logs and diagnostics

Normal logs and `--doctor` are designed not to contain keys, audio bytes,
transcript content, provider response bodies, or private paths. The diagnostic
CLI is local-only; a provider probe, when explicitly requested, sends no audio.

## Control and reporting

You can inspect devices without a key, decline cloud setup, avoid Start, turn
history off, clear the desk/history, remove saved configuration, and uninstall
the application. Report suspected unintended transmission or secret exposure
privately through the repository's [security policy](../SECURITY.md); never
attach credentials, recordings, or private transcripts.
