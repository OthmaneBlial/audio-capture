# UI contribution guide

The interface is a small dictation desk, not a general dashboard. A UI change
should make capture state, provider boundary, text ownership, or the next safe
action easier to understand.

## Interaction contract

- Keep the primary action unambiguous: start when ready, stop when active.
- Preserve visible ready, listening, detected-speech, pending, complete, error,
  and stopped states.
- Keep microphone, active provider, and its data-boundary label discoverable.
- Never claim a global shortcut, tray behavior, or local provider on a desktop
  where capability detection says it is unavailable.
- Destructive text actions require confirmation; exports show the destination;
  history remains opt-in.

## Accessibility contract

- Every interactive widget needs a useful accessible name.
- All setup and daily actions must work by keyboard with a visible focus path.
- Do not encode state only by color, motion, or an icon.
- Respect text-size controls and reduced visual space without truncating the
  privacy boundary or next action.
- Preserve a logical mapped-widget focus order under the GTK smoke harness.

## Verification

Run unit tests and Ruff for every change. If widget structure, labels, first
run, or the recording desk changes, also run:

```bash
xvfb-run -a python3 tests/gtk_accessibility_smoke.py
```

The smoke check proves mapped GTK structure under Xvfb, not real Wayland/X11
input, a screen-reader session, or a microphone. State those manual gaps in the
pull request. If the public guided tour changes, edit `site/product-tour.html`,
run `scripts/render_demo_assets.sh`, inspect every generated frame, and keep the
synthetic-data disclosure next to the images.
