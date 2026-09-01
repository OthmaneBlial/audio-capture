# Privacy notice

Last reviewed: 1 September 2026

Voice Transcriber is a local desktop application. It has no operator account,
analytics, advertising, crash-report upload, transcript-sync service, or
project-controlled server. Privacy still depends on the transcription provider
you select, your operating system, and any files or programs you explicitly
choose.

## What the application processes

| Data | Purpose | Default persistence | Destination |
| --- | --- | --- | --- |
| Microphone PCM frames | Detect speech and create completed segments | Bounded memory only | Local capture/VAD |
| Completed speech segment | Transcription | No app-created audio file | Groq HTTPS in cloud mode; user-supplied local process in experimental mode |
| Transcript | Review, edit, copy, export | GTK memory | Clipboard/export only after user action |
| Optional text history | Retrieve recent transcripts | Off by default; 1–365 day retention | Owner-only local JSON |
| Groq API key | Authenticate cloud requests | Environment/`.env`, or owner-only app config when saved | Groq request header |
| Local CLI/model paths | Launch experimental local runtime | Owner-only app config when saved | Local process only |
| Preferences | Restore UI choices | Owner-only app config | Local only |

The app calculates the input meter from an in-memory RMS value. Recent request
states contain status text only, not audio or transcript text. It does not
continuously record, run in the background after exit, or silently simulate
keyboard input.

## Groq cloud mode

After local voice activity detection closes a segment, the app sends an
in-memory WAV payload, model identifier, and selected language/translation
option to Groq's audio transcription or translation endpoint. It never uploads
silence as a standalone request and does not use Groq batch, files, or
fine-tuning APIs.

Groq controls provider-side processing. Review the current official
[speech-to-text documentation](https://console.groq.com/docs/speech-to-text),
[customer-data documentation](https://console.groq.com/docs/your-data), and
[privacy policy](https://groq.com/privacy-policy) for your account and
jurisdiction. Those pages can change; this project links to them instead of
promising a vendor retention period it cannot enforce.

At this project's 1 September 2026 review, Groq's customer-data documentation
said inference input/output is not retained by default, but may be logged for
reliability or abuse investigation for up to 30 days; Zero Data Retention was
available, and retained customer data was located in US GCP. Groq's speech
documentation also stated a 10-second minimum billed length for each request.
Voice Transcriber sends every completed VAD segment as a separate request, so a
short segment can be billed above its spoken duration. The first-run dialog and
Settings show this review date, the bounded summary, and live links to both
provider documents before cloud use.

## Experimental local mode

This source-only mode requires
`VOICE_TRANSCRIBER_EXPERIMENTAL_LOCAL=1`, an executable `whisper-cli`, and a
GGML model you supply. On Linux, the app passes an in-memory WAV through a
`memfd` path and creates no raw-audio file. The selected executable runs with
your user permissions. Treat it as trusted code: a malicious or compromised
binary could read the speech it receives or use any network/filesystem access
available to that source session. The current Flatpak disables this mode.

## Text storage and deletion

- The live transcript disappears when cleared or when the app closes, unless
  opt-in history is enabled or you explicitly copy/export it.
- History is disabled by default, text-only, stored with owner-only permissions,
  pruned on read/write, deletable per entry, and clearable in one action.
- Exports require a visible destination and confirmation. The app requests
  owner read/write permissions, but copied/exported data is then governed by
  the clipboard, destination filesystem, backups, and applications you use.
- Flatpak `uninstall --delete-data` removes sandboxed settings/history. Explicit
  exports remain because they belong to the user-selected destination.

## Logs and diagnostics

Normal logs describe lifecycle and normalized failures. They are designed not
to contain API keys, audio bytes, transcript content, provider response bodies,
or local model paths. `--doctor --json` reports key presence/source and local
file readiness as booleans only. It contacts Groq only with the explicit
`--probe-provider` option and never sends audio.

## Control and reporting

You can avoid cloud transmission by not starting Groq mode. You can inspect the
UI and devices without a key, switch modes only where the experimental source
flag is available, turn history off, clear history, clear the current desk,
remove saved configuration, or uninstall with data removal.

Report suspected unintended transmission, secret exposure, or privacy bypass
privately through the repository's [security policy](../SECURITY.md). Do not
attach credentials, recordings, or private transcripts.
