# UI contribution guide

The interface is a small dictation desk, not a general dashboard. A UI change
should make capture state, provider boundary, text ownership, or the next safe
action easier to understand.

## Interaction contract

- Keep the primary action unambiguous: start when ready, stop when active.
- Preserve visible ready, listening, detected-speech, pending, complete, error,
  and stopped states.
- Keep microphone, active provider, and its data-boundary label discoverable.
- Never claim a global shortcut or offline provider that the native app does not
  implement.
- Destructive text actions require confirmation; exports show the destination;
  history remains opt-in.

## Accessibility contract

- Every interactive egui widget needs a useful visible label or tooltip.
- Setup and daily actions must work by keyboard with a visible focus path.
- Do not encode state only by color, motion, or an icon.
- Respect text-size controls and narrow windows without hiding the privacy
  boundary or next action.
- Keep settings grouped in a predictable order and ensure checkbox outlines and
  selected states remain visible in the dark theme.

## Verification

Run the Rust checks for every change:

```bash
cargo fmt --all -- --check
cargo test --locked --all-targets
cargo clippy --locked --all-targets -- -D warnings
```

If the desktop interaction changes, launch the native binary on the target OS,
capture a screenshot of the changed state, exercise keyboard focus, and record
any missing OS/device evidence in the pull request. Automated unit tests do not
prove a real compositor, screen reader, microphone permission, or provider
request.
