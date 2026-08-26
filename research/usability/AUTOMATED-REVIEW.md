# Automated heuristic review — not a usability session

The daily-dictation implementation is checked against five deterministic task
paths before recruiting participants. These are product/test scenarios, not
human evidence, and do not satisfy the roadmap's five-session gate.

| Scenario | Contract checked automatically |
| --- | --- |
| Correct a final transcript | Editable buffer model, bounded undo/redo snapshots, select-all through GTK |
| Understand request progress | Stable per-segment pending/complete/error state without transcript or audio retention |
| Keep text deliberately | Manual copy, opt-in copy-on-final, structured export content and owner-only mode |
| Discard text deliberately | Clear confirmation, history disabled by default, entry/all-history deletion |
| Use desktop conveniences honestly | Focused push-to-talk; X11-only legacy tray capability; no hidden key injection or global-shortcut claim |

The Flatpak GTK smoke test covers visible controls and accessibility structure.
Pure tests cover persistence, expiry, deletion, export formatting, permissions,
capability gating, and request-state bounds. Real participants still need to
verify comprehension, confidence, and workflow friction.
