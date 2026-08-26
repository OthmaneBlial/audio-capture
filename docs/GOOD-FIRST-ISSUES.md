# Good first issue candidates

These candidates are intentionally bounded. Before publishing one as an issue,
a maintainer should confirm it still matches the current code and promise to
review the resulting pull request.

## Verify one environment in the support matrix

Run the documented source install on one currently “expected” Linux
environment and report the exact OS, desktop session, audio stack, install
commands, diagnostics, and result without including private device names or
credentials.

**Acceptance:** one row in `docs/SUPPORT.md` gains reproducible evidence and an
honest supported/expected/unsupported status.

## Add an architecture diagram alt description

Turn the text data flow in `docs/DATA-FLOW.md` into an accessible SVG diagram
and preserve the complete text equivalent.

**Acceptance:** the diagram renders in GitHub light/dark themes, has a concise
alt description, and introduces no new privacy claim.

## Test the product-tour renderer on Linux

Run `scripts/render_demo_assets.sh` with Chrome/Chromium and ffmpeg on Linux,
then document any required package names or font differences.

**Acceptance:** regenerated images have the documented dimensions, contain all
three states, and pass a visual comparison review.

## Improve a microphone error

Choose one normalized capture failure, add a failing unit test for an unclear
message, then make the next action explicit without exposing environment data.

**Acceptance:** the new test fails before and passes after the change; the
message names a safe user action.

## Review keyboard names and focus order

Use GTK's accessibility inspection tools on the ready, Settings, recording,
and completed states. Record only widget names and focus order.

**Acceptance:** every interactive control has a useful accessible name, the
focus path is documented, and any fix includes a manual verification note.

