# From issue to pull request

## 1. Choose a bounded Rust task

Describe the user-visible problem, affected module, acceptance criteria, and
the platform evidence required. Closed migration issues are historical and
should not be reopened without rewriting their scope for the native code.

Security and privacy vulnerabilities never start in a public issue. Use
[`SECURITY.md`](../../SECURITY.md).

## 2. Reproduce before changing code

Run the smallest relevant Cargo test and record the current outcome. For a bug,
add a failing deterministic test when possible. For hardware or packaging,
separate local automated evidence from real-machine evidence.

## 3. Make one reviewable change

Keep the provider, privacy, persistence, and queue invariants in the
[architecture tour](ARCHITECTURE-TOUR.md). Do not add telemetry, stored audio,
or an unverified support claim to complete a narrow task.

## 4. Verify and open the PR

Run the commands in [development without a key](DEVELOPMENT-WITHOUT-KEY.md).
Open a pull request that includes:

- the user-visible behavior before and after;
- tests and documentation changed;
- exact commands and results;
- any provider, microphone, display, screen-reader, or packaging gate not run;
- confirmation that no credentials, recordings, transcripts, or private paths
  are included.

Use an imperative title such as `fix: explain unavailable saved microphone`.
