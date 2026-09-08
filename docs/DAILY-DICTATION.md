# Daily dictation controls

Voice Transcriber keeps one editable desk in memory. Final segments arrive as
text, while a bounded strip shows recent requests as waiting, added, or failed.
The strip never stores audio or transcript content.

## Edit and control

- Type directly into the transcript and use the normal text-selection keys.
- Incoming segments preserve their sequence order; pending and failed states
  remain visible so a review does not silently lose a request.
- Undo/redo uses a bounded in-memory snapshot budget.
- Clear asks for confirmation before removing the current draft.
- **Test microphone** verifies the selected local input, drives the level meter,
  and discards frames without contacting Groq.
- An explicitly selected input is saved with a best-effort opaque identity. If a
  replugged device reuses an old index with a different identity, startup fails
  closed and asks you to refresh the picker.
- When the bounded audio queue is full, the oldest in-memory frame is dropped
  and the UI reports the condition. Repeat the phrase rather than assuming the
  segment is complete.
- Toggle mode starts/stops from the primary button or `Ctrl+Enter`.
- After Stop, the desk may briefly show **Processing remaining…** while an
  already admitted segment finishes.
- Focused push-to-talk starts while the window is pressed and stops on release;
  it is not a system-wide shortcut.

Voice Transcriber does not simulate paste or type into another application.
Copy and export are explicit actions.

## Export

Choose plain text, Markdown, or timestamped text. The app writes only after you
confirm a destination and refuses unsafe replacement paths. SRT is absent until
the project has a published timestamp accuracy contract.

## Local history

History is disabled by default. If enabled, the current transcript is saved as
text on clean close, identical text is deduplicated, and entries older than the
chosen 1–365 day retention are pruned. The store is bounded to 500 entries and
500,000 aggregate characters. Entries can be copied back, reopened, deleted
individually, or cleared permanently.
