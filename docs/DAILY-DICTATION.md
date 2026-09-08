# Daily dictation controls

Voice Transcriber keeps one editable desk in memory. Final segments arrive as
text, while a bounded strip shows each recent request as waiting, added, or
failed. The strip never stores audio or transcript content.

## Edit and control

- Type directly into the transcript, select text, or use `Ctrl+A`.
- Incoming segments follow the bottom only while you are already reading there;
  scrolling up for review is preserved while new text arrives.
- Undo with `Ctrl+Z` and redo with `Ctrl+Shift+Z`.
- Undo/Redo keeps a bounded in-memory snapshot budget; very large drafts may
  have fewer recoverable edit points than short drafts.
- Clear always asks for confirmation and explains whether recovery is possible.
- Use **Test microphone** in Settings to verify the selected local input. It only
  drives the signal meter, keeps no audio queue, and never calls a provider.
- An explicitly selected input is saved with a best-effort opaque identity as
  well as its PortAudio index. If a replugged device reuses that index, startup
  refuses the mismatch and asks you to refresh the picker instead of recording
  from an unexpected microphone. PortAudio does not provide one portable
  persistent identifier, so this guard is not a hardware guarantee.
- If the status says **Audio buffer full**, the computer could not process the
  microphone quickly enough. The app drops the oldest in-memory frame to stay
  bounded; repeat the phrase after the warning instead of assuming that segment
  is complete. No dropped frame is written to disk.
- Toggle mode starts and stops with a click or `Ctrl+Enter`.
- After Stop, the desk can briefly show **Processing remaining…** while an
  already admitted segment finishes; the transcript becomes ready to review
  when that result arrives.
- Focused push-to-talk starts on mouse press and stops on release. It is not a
  system-wide shortcut; losing window focus also stops it, and it cannot capture
  when another app owns the interaction. `Ctrl+Enter` remains the explicit
  start/stop toggle.
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
and entries older than the chosen 1–365 day retention are deleted. The store is
bounded to 500 entries and a 500,000-character aggregate budget; malformed or
future-schema data is preserved and reported instead of overwritten. The Settings
and History views disclose the exact storage path.

History can be copied back to the clipboard, opened on the desk, deleted one
entry at a time, or cleared permanently. Raw audio is never added. Explicit
exports are separate user-owned documents and remain after history deletion or
Flatpak `--delete-data` if they were saved outside the sandbox.
