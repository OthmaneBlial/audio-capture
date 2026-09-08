# Good first issue candidates

The previous issue queue was closed during the Rust rewrite because its
acceptance criteria described the removed runtime. New public tasks should be
opened only after a maintainer checks them against the current source and
release goals.

## Bounded Rust tasks

### Add a deterministic provider fixture

Exercise a normalized Groq response and malformed-response branch through an
injected transport without contacting the network.

**Acceptance:** the test fails on the old behavior, passes with the change, and
never stores a key, audio payload, or transcript in output.

### Improve a microphone error

Choose one normalized CPAL failure and make the next user action explicit.

**Acceptance:** a focused unit test covers the failure and the UI/CLI message is
actionable without exposing device internals or private paths.

### Review keyboard focus and contrast

Run the native desktop through ready, settings, recording, complete, and error
states on one available OS.

**Acceptance:** every interactive control has a visible name, focus is obvious,
checkboxes remain visible in the dark theme, and the evidence names any missing
screen-reader or hardware gate.

### Add a target-specific release smoke check

Extract one native archive on a clean profile and run the diagnostic commands.

**Acceptance:** the exact tag, asset, checksum, OS, architecture, and output are
recorded without credentials or private transcript data.

Use the [contributor map](contributing/README.md) and the [issue-to-PR path](contributing/ISSUE-TO-PR.md)
before publishing a new task.
