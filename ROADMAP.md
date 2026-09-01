# Voice Transcriber roadmap

Last revised: 1 September 2026

## Direction

Voice Transcriber is a **review-first Linux dictation desk**. It should be the
small, dependable place where someone speaks a prompt, email, ticket, note, or
draft; corrects the result; and deliberately copies or exports the final text.

That is narrower than system-wide voice typing, and intentionally so. The
product can win on a coherent combination:

- a visible review step before text reaches another application;
- local speech detection with an inspectable cloud boundary;
- no app-created audio library, analytics, or automatic transcript sync;
- bounded capture/provider work with visible failures;
- a lightweight cloud path that does not require a local model download.

The project will not market “private/offline Linux voice typing” as a unique
claim. Mature competitors already ship packaged local inference, global
shortcuts, cursor insertion, model managers, GPU options, and broader distro
support. Voice Transcriber should either prove those capabilities properly or
remain honest about not having them.

## Shipped baseline

Version `v1.0.0` currently provides:

- an installable, source-mapped `x86_64` Flatpak release asset;
- a GTK review desk with microphone selection, local meter, editing,
  undo/redo, segment states, copy, clear, and explicit exports;
- local WebRTC VAD plus a bounded Groq transcription path;
- optional text-only local history, off by default and retention-limited;
- privacy-safe diagnostics and a user-managed provider key;
- checksum, test report, CycloneDX SBOM, and Sigstore provenance;
- a reproducible guided product tour, public site, privacy notice, support
  matrix, contribution map, and structured issue forms;
- 69 deterministic tests that require no microphone, key, model, or network.

Automated package and boundary tests are not physical microphone evidence. The
current Flatpak is a manually downloaded bundle, not a Flathub release; the
local `whisper.cpp` adapter remains an experimental source-only path.

## Now — prove first success and normal distribution

### 1. Publish through a real update channel

- [ ] Submit the Flatpak to Flathub and complete the App ID affiliation review.
- [ ] Prove search, install, launch, update, and uninstall from a clean supported
  desktop without cloning the repository.
- [ ] Make the Flathub listing the primary download only after the public app
  page, screenshots, permissions, privacy boundary, and support links are live.
- [ ] Keep the checksum-verifiable GitHub bundle as an advanced fallback.

**Gate:** a new user can install and later update Voice Transcriber through a
configured remote. A standalone `.flatpak` file does not satisfy this gate.

### 2. Replace expected compatibility with physical evidence

- [ ] Verify Ubuntu GNOME on Wayland with PipeWire and a real microphone.
- [ ] Verify Debian on X11 with PulseAudio and a real microphone.
- [ ] For each combination, test device discovery, the input meter, one real
  Groq transcript, edit/copy/export, reconnect behavior, and data removal.
- [ ] Publish only sanitized environment facts; never collect keys, recordings,
  transcripts, configuration files, or full system dumps.

**Gate:** the [compatibility matrix](docs/COMPATIBILITY.md) links repeatable
reports for both declared paths. Xvfb and injected audio remain labelled as
automated boundary evidence.

### 3. Prove install-to-first-copy onboarding

- [x] Make first run scrollable, keyboard-operable, and explicit about what is
  local and what is sent.
- [x] Show dated Groq retention, location, Zero Data Retention, and 10-second
  per-request billing facts with live provider-document links.
- [ ] Run ten privacy-safe clean-machine sessions through install, microphone
  choice, one real test phrase, review, and copy.
- [ ] Classify failures by step and publish an anonymized findings summary.
- [ ] Keep **Explore first** available without a key or provider probe.

**Gate:** at least eight of ten supported-machine sessions reach a first copied
transcript in under five minutes; every failure produces a concrete product or
documentation action. No analytics are added to measure this.

## Next — make review-first dictation easier to summon

### 4. Add portal-backed activation

- [ ] Detect the XDG `GlobalShortcuts` portal and expose global toggle plus
  hold-to-talk actions where the desktop grants them.
- [ ] Show the actual binding returned by the portal and a useful unsupported
  fallback; never silently grab keys.
- [ ] Add stable single-instance actions for show, start, stop, cancel, and
  stop-and-copy so desktop integrations do not scrape the UI.
- [ ] Verify supported GNOME/KDE Wayland and X11 paths while another app has
  focus.

Clipboard delivery remains the safe default. Active-window insertion may be
explored only as an opt-in, desktop-specific integration with a separate threat
model and real evidence; `ydotool` or simulated typing will not become a hidden
mandatory dependency.

### 5. Turn experimental local inference into a supported product—or remove it

- [ ] Decide one packaged local runtime and a small recommended CPU model.
- [ ] Build an in-app model flow that shows source, license, checksum, download
  size, expected RAM, language scope, acceleration status, and deletion before
  download.
- [ ] Prove clean install to first local transcript without a key, compiler, or
  terminal, then repeat with the network disabled after model download.
- [ ] Publish accuracy/latency/resource receipts on named hardware and licensed
  audio; do not present a CI runner as representative desktop performance.
- [ ] If these gates are not maintainable, remove the user-facing experimental
  path instead of allowing a permanent half-supported provider.

**Gate:** the packaged local path owns its runtime/model lifecycle and has real
offline plus hardware evidence. Merely accepting user-supplied files is not a
supported provider.

## Later — widen only from evidence

- [ ] Add `aarch64` only after an architecture-native package build, launch,
  microphone, and provider smoke gate passes.
- [ ] Consider a Debian package only if updates and native dependency support
  can match the Flatpak contract; do not publish an AppImage for badge count.
- [ ] Convert useful external reports into compatibility rows, FAQs, regression
  tests, credited fixes, and release notes.
- [ ] Publish the prepared technical and workflow stories after the install and
  physical compatibility gates are true.
- [ ] Add translations when installation, privacy, and troubleshooting content
  has an identified reviewer for each language.

## Release shape

| Milestone | User-visible promise | Required proof |
| --- | --- | --- |
| `v1.1` — Transparent first copy | “Install, understand the boundary, and copy a first reviewed transcript.” | Flathub or documented update-channel decision, onboarding sessions, dated provider disclosure, physical compatibility reports |
| `v1.2` — Desktop activation | “Start a review session without first focusing the desk.” | Portal-backed shortcuts/actions plus GNOME/KDE Wayland and X11 evidence |
| `v2.0` — Real provider choice | “Choose lightweight cloud or supported local transcription.” | Packaged model lifecycle, offline proof, hardware/resource receipts, migration and removal contract |

Versions and dates are not promises. A milestone ships only when its entire
public claim is supported by release-specific evidence.

## Non-goals

- No meeting recorder, speaker diarization, chatbot, summarization layer, or
  automatic cloud sync while the core review-first job remains unproven.
- No background recording, transcript/audio analytics, or crash uploads for
  growth reporting.
- No “100% private,” “fully offline,” “type anywhere,” or universal Linux claim
  while the shipped package contradicts it.
- No macOS, Windows, mobile, or browser claim without a native implementation
  and an independently verified release path.
- No star target presented as a product guarantee. Stars should follow useful
  releases, trusted evidence, responsive maintenance, and honest sharing.

## How progress is measured

Use public release downloads, opt-in compatibility reports, reproducible
benchmarks, issue resolution, and returning contributors. The project should
not add behavioral telemetry to manufacture a funnel.

The detailed pre-v1 execution record remains available in Git history. Current
evidence and open gaps live in [support](docs/SUPPORT.md),
[compatibility](docs/COMPATIBILITY.md), [privacy](docs/PRIVACY.md), the
[packaging decision](docs/packaging/DECISION.md), and maintained GitHub issues.
