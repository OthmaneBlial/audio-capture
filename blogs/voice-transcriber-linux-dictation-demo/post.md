---
title: "Voice Transcriber: a focused Linux dictation app"
description: "See how Voice Transcriber turns a spoken note into editable text on Linux while showing what stays local and what is sent for transcription."
slug: "linux-dictation-app-demo"
status: "ready after final v1 release verification"
---

# Voice Transcriber: a focused Linux dictation app

![A calm Linux desktop dictation scene with a visible microphone signal, privacy boundary, and editable text](hero.png)

Sometimes the sentence is already clear in your head; typing is the part that
gets in the way. Voice Transcriber is a **Linux dictation app** for the short
moment between having an idea and putting it into an email, prompt, ticket, or
note.

Open it, confirm the microphone, speak, edit the result, then decide whether to
copy, export, keep, or clear it. There is no recording library to manage and no
project-owned account.

[Watch the three-state guided demo](https://othmaneblial.github.io/audio-capture/#proof).
The preview uses synthetic sample text and mirrors the current native interface;
the application itself never inserts a simulated transcript.

## A 60-second workflow

### 1. Inspect before adding a key

The app opens without provider credentials. You can see the first-run screen,
Settings, detected microphone inputs, diagnostic commands, and the active
privacy boundary. Start remains blocked until the selected transcription path
is valid, so there is no fake success state.

In the supported Flatpak, that path is Groq cloud transcription with a key you
control. Before any external transmission, onboarding explains that a completed
speech segment will leave the device and asks for explicit confirmation.

### 2. Confirm the right microphone

Choose an input and speak briefly. The local signal meter should move before
you start a session. It is calculated from in-memory microphone frames and is
not stored as a recording.

This is a small detail with a large effect: you discover a wrong input before
dictating a paragraph.

### 3. Speak and review

Start listening and dictate one useful thought. For example:

> Draft a short issue explaining that export confirmation should name the destination.

Voice activity detection runs locally. Silence does not become a standalone
transcription request. After speech ends, the completed segment is sent to the
selected provider and its state moves from pending to complete or to an
actionable error.

The transcript is ordinary editable text. Correct a word, undo or redo the
change, select everything, or clear the desk with confirmation.

### 4. Move the words intentionally

Copy places the visible text on the clipboard so you can paste it into the
destination yourself. Voice Transcriber does not pretend that automatic paste
or a global shortcut works everywhere.

Export asks you to choose a destination and can produce plain text, Markdown,
or timestamped text. Optional copy-on-final is off by default. Text history is
also disabled by default; if you enable it, the app shows its local storage
location, retention period, individual deletion, and clear-all controls.

## What stays local, and what leaves

The supported mode is privacy-explicit rather than fully offline.

| Stays in the app/device boundary | Leaves in Groq mode |
| --- | --- |
| Bounded raw microphone frames | A completed speech segment encoded in memory as WAV |
| Local voice activity detection and signal level | Selected language or translation request |
| Editable transcript until you copy, clear, export, or opt into history | Provider request metadata required for transcription |

The app does not write raw-audio recordings and contains no analytics or crash
reporter. It cannot control provider-side handling, clipboard history, exported
file backups, or operating-system capture. Read the full
[privacy notice](https://github.com/OthmaneBlial/audio-capture/blob/main/docs/PRIVACY.md)
before using it with sensitive speech.

## Install boundary

The primary package is a checksum-backed `x86_64` Flatpak. It uses GTK 3, the
system PipeWire/PulseAudio-compatible route, and Wayland with fallback X11
permissions. Source setup is available for development.

The project does not currently claim macOS, Windows, mobile, browser, AppImage,
Debian-package, universal global-shortcut, Bluetooth-microphone, or fully
offline support. The source-only whisper.cpp provider remains experimental and
is disabled in Flatpak. Automated package and Xvfb checks are published, while
representative physical-microphone reports are still being collected.

Use the [support matrix](https://github.com/OthmaneBlial/audio-capture/blob/main/docs/SUPPORT.md)
to decide whether your environment fits the current boundary, then follow the
[Flatpak instructions](https://github.com/OthmaneBlial/audio-capture/blob/main/docs/packaging/FLATPAK.md).

## Try one real note, then report one useful fact

The most valuable feedback is concrete:

- Which distribution, display session, audio route, and microphone type did
  you test?
- How long did installation to the first copied transcript take?
- Which single step was unclear: package install, key setup, microphone choice,
  boundary explanation, start/stop, correction, copy/export, or deletion?

Do not attach recordings, transcript text, credentials, config files, private
paths, or full system dumps. Use the structured issue forms so one experience
can become a compatibility entry, FAQ answer, regression test, or focused fix.

[Explore Voice Transcriber](https://othmaneblial.github.io/audio-capture/) ·
[Choose a good first issue](https://github.com/OthmaneBlial/audio-capture/labels/good%20first%20issue) ·
[Read the contributor map](https://github.com/OthmaneBlial/audio-capture/blob/main/docs/contributing/README.md)
