# From issue to merged pull request

## 1. Choose a bounded issue

Start with a task carrying `good first issue` or `help wanted`. Read its exact
acceptance criteria and check that nobody is already assigned. Comment with the
environment you can test and the part you plan to handle; a maintainer will
confirm scope or clarify a stale issue.

Security and privacy vulnerabilities never start in a public issue. Use
[`SECURITY.md`](../../SECURITY.md).

## 2. Reproduce before changing code

Run the smallest relevant test and record the current outcome. For a bug, add a
failing deterministic test when possible. For hardware or packaging work,
separate local automated evidence from real-machine evidence.

## 3. Make one reviewable change

Keep the provider, privacy, persistence, and queue invariants described in the
[architecture tour](ARCHITECTURE-TOUR.md). Do not refactor unrelated code or
add telemetry, stored audio, broad Flatpak permissions, or a new product scope
to complete a narrow issue.

## 4. Verify and open the PR

Run the commands in [development without a key](DEVELOPMENT-WITHOUT-KEY.md).
Open a pull request that links the issue and includes:

- the user-visible behavior before and after;
- tests and documentation changed;
- exact automated commands and results;
- any provider, microphone, display-session, screen-reader, or packaging gate
  not run;
- confirmation that no credentials, recordings, transcripts, or private paths
  are included.

Use an imperative title such as `fix: explain unavailable saved microphone`.
The maintainer target is an initial response within seven days. Review may ask
for a smaller scope or stronger evidence; that protects the public contract,
not just code style.
