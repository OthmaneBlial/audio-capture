# Daily dictation controls

Voice Transcriber keeps one editable desk in memory. Final segments arrive as
text, while a bounded strip shows each recent request as waiting, added, or
failed. The strip never stores audio or transcript content.

## Edit and control

- Type directly into the transcript, select text, or use `Ctrl+A`.
- Undo with `Ctrl+Z` and redo with `Ctrl+Shift+Z`.
- Clear always asks for confirmation and explains whether recovery is possible.
- Toggle mode starts and stops with a click or `Ctrl+Enter`.
- Focused push-to-talk starts on mouse press and stops on release. It is not a
  system-wide shortcut and cannot capture when another app owns the interaction.
- A legacy tray window toggle is exposed only on a non-sandboxed X11 session.
  Wayland and Flatpak sessions receive an explicit capability explanation.

Voice Transcriber does not simulate paste or type into another application.
Manual Copy is reliable. Optional copy-on-final is disabled by default and must
be enabled in Settings.

## Export

Choose plain text, Markdown, or timestamped text. Before writing, the app shows
the exact destination, format, and owner-only permission policy. Flatpak's file
chooser portal grants access only to the selected document; the app does not
request home or host filesystem access. SRT is intentionally absent because
segment timestamps do not yet have a published accuracy contract.

## Local history

History is disabled by default. When explicitly enabled, the current transcript
is saved as text on clean app close, repeated identical text is deduplicated,
and entries older than the chosen 1–365 day retention are deleted. The Settings
and History views disclose the exact storage path.

History can be copied back to the clipboard, opened on the desk, deleted one
entry at a time, or cleared permanently. Raw audio is never added. Explicit
exports are separate user-owned documents and remain after history deletion or
Flatpak `--delete-data` if they were saved outside the sandbox.
