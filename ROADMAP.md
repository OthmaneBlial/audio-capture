# Roadmap — Voice Transcriber

## What this project can become

**Voice Transcriber should become the most trustworthy way for a Linux user to
turn a short spoken thought into editable text, without accumulating recordings
or making the cloud boundary invisible.**

It should serve people who dictate notes, prompts, emails, tickets, and drafts
throughout the day. It is *not* a meeting recorder, a generic AI assistant, or
a product that silently uploads a continuous microphone stream.

The existing foundation supports this promise: real microphone capture, local
voice activity detection, bounded queues, a visible input meter, a transcript
review view, and a clear Groq boundary. The next opportunity is productization:
make the first successful dictation easy to install, easy to understand, and
easy to trust.

## Audit baseline — 26 August 2026

### Already strong

- A focused, honest workflow: speech is segmented locally, completed segments
  are transcribed through Groq Whisper, and the application does not persist
  raw audio.
- Practical reliability work already exists: device selection, a bounded audio
  queue and transcription pool, actionable failures, config precedence, and
  private local settings permissions.
- The app has a clean GTK desk, keyboard shortcuts, copy/export, language and
  translation controls, a public site, MIT license, two public releases,
  contributor guidance, security reporting, Dependabot, and CI.
- The automated unit suite currently passes (`15` tests) and source compilation
  passes locally. The published site returned HTTP 200 during this audit.

### What prevents adoption today

| Gap | Why it blocks stars and users | Evidence in the current project |
| --- | --- | --- |
| The promise is useful but not yet distinctive enough | “GTK + Groq Whisper” describes implementation, not the daily job it wins. A visitor cannot immediately see why this beats a browser tab or another Whisper client. | The README leads with the stack and has no real workflow demo or outcome proof. |
| First use is developer-shaped | A new user must clone the repo, run an `apt` script, create a virtualenv, and supply a Groq key before discovering whether dictation helps them. | `setup.sh` supports Debian/Ubuntu only; the `v0.2.0` release has no installable assets. |
| The key requirement is a serious conversion barrier | Bring-your-own-key is valid, but it creates cost, account, and privacy questions before the first transcript. | Groq is the only transcription backend and a plausible key is required to start. |
| Trust is documented, not yet demonstrated | The privacy boundary is unusually clear, but users still need a permission/data-flow view, vendor-policy links, a retention choice, and reproducible release evidence. | No privacy page/threat model, SBOM, provenance, or published package checksums. |
| No proof of the experience | Audio software is judged by latency, accuracy, device handling, and ergonomics. Text alone cannot prove those. | No screenshots, GIF/video, sample corpus/benchmark, or hardware compatibility matrix is tracked. |
| Distribution is incomplete | People cannot install, update, or remove the app like a normal Linux app. | There is a source launcher script, but no Flatpak, `.deb`, AppImage, package repository, or update path. |
| Community is prepared but not activated | Good issue forms and contribution rules exist, yet there is no contribution map, discussion space, newcomer tasks, or public support contract. | GitHub’s live community profile was 85% and did not detect a code of conduct or an issue-template configuration. |
| Quality signals stop at unit tests | The native microphone, GTK UI, packaging, release artifact, security, and compatibility paths are not proven by the current CI matrix. | CI runs lint, compile, and unit tests only on Python 3.11. |

The repository had **0 stars, 0 forks, and 0 open issues** at the time of this
audit, immediately after its first public releases. That is a launch baseline,
not evidence that the product lacks value. The roadmap therefore prioritizes
repeatable first success and proof before chasing reach.

## Principles and non-negotiables

1. **Transient by default.** Do not add background recording, analytics, or
   cloud uploads without an explicit, understandable user action.
2. **State the cloud boundary precisely.** The app may say “local VAD” and
   “audio is not saved by the app”; it must never imply fully offline
   transcription while Groq is selected.
3. **Make a private workflow usable, not merely private on paper.** A user
   must be able to see the selected microphone, current provider, request
   state, storage policy, and what will leave the device.
4. **One excellent desktop workflow first.** Do not dilute the project with a
   web app, mobile app, meeting bot, or a broad AI-agent layer.
5. **Proof beats feature count.** Every capability needs a testable contract,
   a visible demo or documentation path, and an honest support boundary.

## North-star and guardrail measures

No behavioral telemetry should be introduced to obtain these numbers. Use
release downloads, GitHub traffic, opt-in feedback, reproducible benchmark
runs, and support issues instead.

| Measure | First credible target | Why it matters |
| --- | --- | --- |
| Time from install to first copied transcript | Under 5 minutes on a supported fresh Linux machine | This is the real onboarding funnel. |
| Supported-install pass rate | 10 documented clean-machine runs across the declared targets | Replaces “works on my machine” with evidence. |
| Dictation latency | Publish p50/p95 from a licensed sample corpus for each provider/model | Gives users a reason to trust the experience. |
| Privacy regression checks | 100% of releases pass data-flow, secret, and retention checks | Protects the project’s differentiator. |
| Community response | Every reproducible bug gets an acknowledgement within 7 days | Makes a small project safe to try and contribute to. |
| Adoption signals | Sustained release downloads, returning contributors, issue resolution, and qualified star growth | Stars are an outcome of usefulness and trust, not the sole KPI. |

## Dependency-ordered roadmap

### P0 — Establish the promise and the public proof

**Outcome:** a visitor understands the product, its limits, and a successful
workflow in less than a minute.

- [x] Rewrite the README opening around a concrete job: “Dictate a thought,
  review it, and paste it anywhere on Linux.” Keep the current technical
  explanation lower in the page.
- [x] Add three truthful screenshots and one short silent GIF/video: choosing a
  microphone, the live meter and transcription state, then copy/export. Use
  synthetic or consented sample text; do not publish customer audio.
- [x] Add a compact comparison table: **current behaviour**, **what stays
  local**, **what is sent to Groq**, **where text can be stored**, and **what
  it does not do**.
- [x] Publish a supported-environments table with tested desktop/session,
  architecture, audio stack, package format, and known limitations. Debian and
  Ubuntu are the only supported targets until evidence expands that table.
- [x] Add an explicit “Try before configuring” path: launch the UI, inspect
  devices and privacy information, then explain exactly why a key is required
  before Start becomes available. Do not fake a transcript.
- [x] Add `CODE_OF_CONDUCT.md`, an issue-template `config.yml`, labels,
  `good first issue` candidates, and a small maintainer response policy. Check
  GitHub’s community profile again after publishing.
- [x] Fix discoverability without a speculative repository rename: align the
  GitHub description, topics, README title, release names, and site metadata
  on “Linux dictation / speech-to-text / privacy-aware”. Reconsider the generic
  `audio-capture` repository name only after search and referral data justify
  the disruption.

**Acceptance gate:** a clean browser visit shows the outcome, data boundary,
support matrix, install route, demo, license, latest release, and a newcomer
contribution route. All claims can be traced to code or a documented test.

**Completed evidence:** local desktop/mobile browser QA passed with no console
errors or horizontal overflow; the deployed Pages build `6fc2361` completed;
all three screenshots, the animated tour, docs, CSS, and JavaScript returned
HTTP 200; and GitHub's community profile reached 100% after publication.

### P1 — Make first success a normal Linux installation

**Outcome:** supported users install a release, run a diagnostic, and transcribe
one sentence without cloning source code or troubleshooting native Python.

- [ ] Choose one primary distribution format after a short packaging spike.
  **Flatpak is the preferred primary candidate** because it can declare
  permissions and works across more distributions; only ship it once microphone
  portal and outbound-network behaviour have been manually tested. `.deb` can
  be a secondary Ubuntu/Debian path. Do not publish an untested AppImage simply
  to claim portability.
- [x] Package the app, desktop entry, icon, Python dependencies, and runtime
  libraries into release artifacts. Provide checksums, install/update/uninstall
  instructions, and exact source-to-artifact version mapping.
- [x] Add a non-destructive `voice-transcriber --doctor --json` command. It
  should report OS/session support, GTK availability, microphone discovery,
  selected input availability, config-key presence (never value), provider
  reachability when explicitly requested, and next actions.
- [x] Keep `--check-config` and `--list-devices`; document their stable output
  contracts and exit codes so support scripts can use them.
- [x] Add a first-run screen that asks for microphone choice, language, and
  provider/key with an explicit explanation before external transmission. It
  must be fully keyboard navigable.
- [x] Add clean-machine smoke tests for the selected packaging format and a
  release checklist covering installation, microphone permission, start/stop,
  copy/export, and removal.

**Acceptance gate:** a new supported-machine tester can install the latest
release, pass `--doctor`, record a real short segment, copy its result, and
uninstall cleanly using only the public instructions.

**Implementation evidence:** `v0.4.0` publishes a source-mapped x86_64 Flatpak
and SHA-256; Actions run `33013357498` built it from a clean checkout, installed
it, verified exact version/help/doctor contracts, exercised first-run GTK and
accessibility under Xvfb, asserted minimal permissions and packaged metadata,
then removed the app and sandbox. The two public assets were downloaded again
and matched SHA-256 `cd1e448065e13f9c639567d722439be3651a3c8d67b5047dfd343e1346903215`.
The first checkbox and acceptance gate remain open because a physical Linux
microphone plus a tester-owned Groq key have not been exercised; automated
headless audio/package proof is not relabelled as that manual evidence.

### P2 — Turn a transcription desk into daily dictation

**Outcome:** the app earns a place in someone’s daily workflow rather than being
a one-time demo.

- [ ] Run five structured usability sessions with the P0 demo build. Observe
  device selection, start/stop confidence, correction, copying, and privacy
  comprehension. Publish anonymised findings and change the roadmap from
  evidence, not intuition.
- [x] Add transcript editing, undo/redo, select-all, clear confirmation, and
  a visible pending/error state per segment. Preserve the existing explicit
  bounded-queue behaviour.
- [x] Add a push-to-talk workflow and a tray/window toggle where the declared
  desktop session permits it. Global shortcut support must be capability-gated:
  Wayland and sandbox restrictions should produce a useful explanation, never a
  silent failure.
- [x] Add optional “copy on final transcript” and an intentional paste/insert
  workflow only where platform APIs make it reliable. Never simulate hidden
  keyboard input or claim universal paste support.
- [x] Add structured exports (`.txt`, Markdown, and timestamped text) with a
  preview of destination and owner-only permissions where feasible. Add SRT
  only after timestamps have a tested accuracy contract.
- [x] Add an explicit opt-in local history: disabled by default, configurable
  retention period, clear-all action, storage location disclosure, and safe
  migration/deletion tests. Raw audio remains non-persistent.

**Acceptance gate:** a user can dictate, correct, copy, retrieve or permanently
discard text according to a plainly visible retention choice, all without
opening a terminal.

**Implementation evidence:** `v0.5.0` adds editable transcript state with
bounded undo/redo, per-segment request state, focused push-to-talk, an X11-only
legacy tray toggle, optional copy-on-final, three destination-confirmed export
formats, and schema-versioned opt-in text history with retention and deletion.
Forty unit tests passed in CI and Flatpak run `33013850025` built, installed,
exercised the GTK accessibility and daily-workflow smoke contract, and removed
the exact bundle. The five real-participant sessions remain open and are
separately specified in `research/usability/PROTOCOL.md`; automated review is
not presented as human evidence.

### P3 — Remove the “bring a cloud key” ceiling without weakening privacy

**Outcome:** users can choose an understandable transcription mode rather than
being forced into one vendor/account path.

- [x] Extract a small provider interface from `GroqTranscriptionService`:
  capabilities, supported languages, translation availability, cancellation,
  limits, error normalization, and a provider-specific data-boundary label.
- [x] Preserve Groq as the well-tested fast cloud path; add a provider selection
  UI only when a second backend has equal error, privacy, and test contracts.
- [x] Prototype one genuinely local backend behind an explicit feature flag
  (for example a packaged Whisper-compatible local runtime). Measure model
  download size, CPU/RAM, latency, language quality, and supported hardware
  before promising “offline”.
- [x] Offer a clear choice at setup: **Groq cloud** (completed speech segment
  leaves the device, user-managed key) or **Local model** (model/download and
  hardware cost explained). The UI must show the active mode during a session.
- [x] Publish a reproducible, licensed benchmark corpus and harness for
  accuracy/latency comparisons. Report limitations and sample composition;
  do not manufacture an aggregate “accuracy” number without context.

**Acceptance gate:** each supported backend has a documented data flow,
capability matrix, deterministic tests, and reproducible performance evidence.
Local mode is not announced as supported until it passes the same packaging and
first-success gate as cloud mode.

**Implementation evidence:** the typed provider contract drives Groq and the
explicitly flagged source-only whisper.cpp prototype, with deterministic
capability, cancellation, error, configuration, diagnostics, and data-boundary
tests. The current Flatpak deliberately contains only the supported Groq path.
Benchmark run `33015305254` verified the official LibriSpeech `test-clean`
archive checksum, selected 25 speakers deterministically, built pinned
whisper.cpp/tiny.en, and published the committed receipt: 37 / 627 word errors
(5.90% WER), 1,043.810 ms p50 and 1,508.576 ms p95 on the named GitHub runner.
Exact commit CI run `33015936280` passed 50 tests, Ruff, and compilation;
Flatpak run `33015936279` built/installed `0.6.0` and passed the CLI, doctor,
provider-boundary, mapped GTK accessibility, and uninstall smoke contracts;
CodeQL run `33015923746` passed all three detected languages with no open
alerts. The measured local prototype remains labelled experimental—not
supported or universally offline—until the separate Flatpak and physical
first-success gates pass.

### P4 — Make trust and releases independently verifiable

**Outcome:** an open-source user can verify what the app does and reproduce a
safe release decision.

- [x] Add a privacy page and a concise threat model covering microphone access,
  VAD, memory, provider request, API-key storage, exports, history, logs, and
  crash reports. Link the current Groq policy/documentation rather than making
  unverifiable vendor-retention claims.
- [x] Add a privacy regression checklist/test suite: no raw-audio files,
  secrets redacted from logs/errors, no key in diagnostics, retention disabled
  by default, and explicit export/history permissions.
- [x] Expand CI to the declared supported Python range, package builds, test
  coverage reporting, dependency vulnerability checks, and static security
  analysis. Native hardware checks remain separately labelled manual evidence.
- [ ] Add reproducible release automation: version consistency checks,
  changelog validation, artifact checksums, SBOM, signed tags or attestations,
  and a downloadable provenance record.
- [ ] Test against representative PipeWire/PulseAudio and X11/Wayland paths;
  publish a compatibility issue template that captures only the data needed to
  reproduce an audio failure.
- [x] Define a supported-version and deprecation policy. Keep security fixes,
  packaging fixes, and model/provider changes easy to audit in release notes.

**Acceptance gate:** every release has a test report, provenance/checksum,
known limitations, compatibility status, and a privacy-change section. A
security reviewer can follow the documented data flow from microphone to export.

**Implementation evidence:** the published privacy notice and threat model map
microphone, VAD, bounded memory, provider requests, credentials, text storage,
exports, logs, local executables, and release supply chain. Four privacy tests
join the 58-test suite. Exact-commit CI run `33018105244` passed Python 3.9,
3.11, and 3.14 with branch coverage above 70%, wheel/sdist builds, a hashed
dependency audit, Bandit, Ruff, and compilation. Flatpak run `33018105481`
passed the documented App-ID-only linter exception, mirrored AppStream/repo
lints, a clean `--disable-download` rebuild, install/GTK/CLI smoke, and removal.
CodeQL run `33018105062` passed all detected languages with no open alerts.
Release automation now validates version/changelog surfaces and creates a
checksum, CycloneDX SBOM, test report, provenance and SBOM attestations, and
release notes. Its checkbox remains open until the `v1.0.0` tag proves the
complete publish job. The compatibility checkbox also remains open because
Xvfb and capability unit tests are not relabelled as real Wayland/X11 plus
PipeWire/PulseAudio microphone sessions; the new structured issue form records
that missing evidence without collecting sensitive system dumps.

### P5 — Build an open-source distribution and contribution loop

**Outcome:** each useful release gives users something concrete to share and
contributors a bounded way to help.

- [ ] Publish a release page that includes the demo, a one-sentence outcome,
  package instructions, support matrix, privacy delta, benchmark delta, and
  a short “help wanted” list.
- [ ] Create a public `docs/contributing/` map: architecture tour, local
  development without a real API key, fake audio fixtures, UI contribution
  guide, packaging guide, and an issue-to-PR path.
- [ ] Curate 5–10 narrowly scoped issues after P1/P2 evidence exists: package
  smoke test, documentation translation, accessibility review, device matrix,
  provider contract fixture, and release QA. Each issue needs acceptance
  criteria and a maintainer.
- [ ] Enable GitHub Discussions only if it will receive regular responses;
  otherwise direct users to issues with the two existing structured forms.
- [ ] Write one technical launch post and one user-focused demo post around the
  verified differentiator: ephemeral voice-to-text with an explicit cloud
  boundary. Share only after a packaged release and demo exist; collect feedback
  questions rather than asking generically for stars.
- [ ] Turn useful external feedback into public artifacts: compatibility
  entries, FAQs, reproducible bug fixes, and credited contributors. Never add
  usage tracking merely to produce growth charts.

**Acceptance gate:** the project has an installable release, a visual proof,
an honest support boundary, a contributor’s first task, and a repeatable
release/feedback cycle.

## Recommended release sequence

| Release | User-visible promise | Scope that must land together |
| --- | --- | --- |
| `v0.3` — Proof | “See exactly what Voice Transcriber does and where data goes.” | P0 documentation/demo/community foundation and compatibility statement. |
| `v0.4` — Install | “Install and diagnose it like a Linux app.” | One verified package format, `--doctor`, first-run flow, clean-machine evidence. |
| `v0.5` — Daily dictation | “Dictate, correct, and intentionally keep or discard text.” | P2 workflow and opt-in retention; the real-participant study remains a separate evidence gate. |
| `v0.6` — Choice | “Choose a clear cloud or local transcription boundary.” | Provider contract plus one proven second backend; do not label experimental local mode as production. |
| `v1.0` — Trusted public tool | “A repeatable, auditable Linux dictation tool.” | P4 release/trust gates and P5 contribution loop proven over several releases. |

## Things deliberately not to do yet

- Do not add a broad chatbot, summaries, meeting recording, speaker
  diarisation, or automatic cloud sync. They obscure the sharp dictation job
  and increase the privacy surface.
- Do not claim macOS, Windows, all Linux distributions, offline operation, or
  global shortcuts until release artifacts and real compatibility evidence
  support each claim.
- Do not collect transcript/audio analytics to chase product metrics.
- Do not start several package formats or providers at once. One trustworthy
  end-to-end path is much more valuable than four untested badges.

## First implementation backlog

The highest-leverage next pull requests are, in order:

1. P0 README/site proof bundle: screenshots/demo, workflow-led copy, data-flow
   table, supported-environment matrix, and code of conduct/community config.
2. A packaging spike with a written decision record and clean-machine test plan
   for Flatpak versus a Debian package.
3. `--doctor --json` plus tests for every diagnostic outcome.
4. First-run privacy/provider setup and its keyboard-accessibility tests.
5. Transcript editing/retention design based on five observed user sessions.

This order is intentional: it gives the project a compelling, verifiable
public face, then removes the installation wall, before expanding the product
surface or making claims a release cannot yet support.
