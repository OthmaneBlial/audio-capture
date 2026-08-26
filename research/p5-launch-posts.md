# P5 launch-post research — Voice Transcriber

Prepared from the repository and its published `v0.6.0` release on 27 August
2026. This is a claim and angle bank for two separate launch posts, not a
publication-ready announcement. Anything marked **v1 proof required** must stay
out of public copy until the `v1.0.0` release workflow succeeds and its public
assets have been downloaded and verified.

## The launchable idea

### One-sentence differentiator

**Voice Transcriber is a focused Linux dictation desk that detects speech
locally, makes the transcription boundary visible, and lets the user decide
when text is copied, exported, retained, or discarded.**

This is stronger and more defensible than “a GTK client for Whisper.” The
interesting product decision is not the model choice; it is the combination of
a narrow daily job, transient audio handling, an explicit cloud boundary, and
evidence users can inspect.

### Positioning hierarchy

1. **Job:** get a note, prompt, email, ticket, or draft out of your head and
   into editable text on Linux.
2. **Trust:** local voice activity detection happens before the supported cloud
   provider sees a completed speech segment; the app does not create raw-audio
   recordings.
3. **Control:** review and edit the transcript, then explicitly copy, clear, or
   export it. Text history is opt-in and off by default.
4. **Proof:** a visual tour, a downloadable checksum-backed Flatpak, a narrow
   support matrix, deterministic tests, and a reproducible benchmark receipt
   already exist.
5. **Open-source invitation:** compatibility, accessibility, packaging,
   documentation, provider-contract, benchmark, and release-QA work can be
   bounded into reviewable contributions.

### What not to position it as

- Not a meeting recorder, meeting bot, generic AI assistant, voice archive, or
  continuous background microphone service.
- Not fully offline in the packaged release. Groq is the supported Flatpak
  provider; the local `whisper.cpp` path is a source-only experimental
  prototype.
- Not a universal Linux, macOS, Windows, mobile, browser, AppImage, or Debian
  package.
- Not a vendor-retention guarantee. Provider-side handling is governed by the
  user’s provider account and current provider policies.
- Not a global hotkey or automatic paste utility. Push-to-talk is focused and
  platform capabilities are disclosed instead of simulated.

## Verified claim ledger

The wording below is intentionally precise enough to reuse directly.

| Public claim that is safe now | Repository evidence | Important qualifier |
| --- | --- | --- |
| “Dictate a thought, review it, and paste it anywhere on Linux.” | `README.md` opening and product site | “Paste” means copy the text and paste it in the destination; the app does not silently inject keystrokes. |
| The app is designed for short daily dictation: notes, prompts, emails, tickets, and drafts. | `README.md`, `ROADMAP.md` | Do not extend this to meetings or long-form recording without evidence. |
| Microphone frames and the input meter stay in bounded memory; the app does not save raw audio. | `docs/PRIVACY.md`, `docs/DATA-FLOW.md`, `audio/capture.py`, privacy tests | The operating system, provider, clipboard, exports, and user-supplied local executable are separate trust boundaries. |
| Voice activity detection runs locally and silence is not submitted as a standalone transcription request. | `docs/DATA-FLOW.md`, `audio/vad.py`, `main.py` | Completed speech segments do leave the device in Groq mode. |
| Groq cloud mode sends an in-memory WAV payload only after a speech segment closes. | `docs/PRIVACY.md`, `transcription/groq_service.py`, `transcription/groq_transport.py` | Do not promise a Groq retention period; link current official provider documents. |
| The user can inspect the interface, Settings, microphone inputs, diagnostics, and privacy boundary without configuring a key. | `README.md`, first-run/onboarding implementation and tests | In packaged cloud mode, Start remains blocked until a plausible user-managed Groq key is available. |
| The transcript is editable and supports copy, explicit export, undo/redo, clear confirmation, and optional copy-on-final. | `README.md`, `docs/DAILY-DICTATION.md`, UI/export/transcript tests | Copy-on-final is opt-in; automatic paste is not claimed. |
| Optional transcript history is text-only, disabled by default, retention-limited from 1–365 days, and clearable. | `README.md`, `docs/PRIVACY.md`, `history.py`, history tests | Explicit exports and clipboard contents are outside the app’s cleanup boundary. |
| The request and capture paths use bounded queues so a slow device/provider cannot create unbounded in-app work. | `README.md`, `docs/ARCHITECTURE.md`, audio/provider implementations and tests | This is a reliability property, not a latency guarantee. |
| The supported packaged provider is Groq `whisper-large-v3-turbo`; a typed provider boundary normalizes capabilities, cancellation, limits, and errors. | `docs/PROVIDERS.md`, `transcription/provider.py` | The user supplies and controls the Groq key. |
| An experimental source-only `whisper.cpp` path uses a Linux memory-backed descriptor, downloads nothing automatically, and writes no raw-audio file. | `docs/PROVIDERS.md`, `docs/PRIVACY.md`, `transcription/local_whisper.py` | It is disabled in Flatpak and must not be called supported, universally offline, or hardware-neutral. |
| A public `v0.6.0` x86_64 Flatpak and checksum are downloadable. | `README.md`; public release `https://github.com/OthmaneBlial/audio-capture/releases/tag/v0.6.0` | Current release assets are the Flatpak and `.sha256` only. Do not claim a public SBOM/attestation for `v0.6.0`. |
| The `v0.6.0` Flatpak SHA-256 is `fd4e59b2af2f72f9158ce8275fde30fddb3ff90b9fb7d7888770d53e9874e3ea`. | Public GitHub release asset digest and checksum verification recorded in `ROADMAP.md` evidence | Tie the digest specifically to `voice-transcriber-0.6.0-x86_64.flatpak`. |
| The reproducible local benchmark used 25 LibriSpeech `test-clean` samples from 25 speakers and reported 37 errors over 627 reference words: 5.90% WER, 1,043.810 ms p50, and 1,508.576 ms p95. | `benchmarks/results/local-tiny-en-github-runner.json` and `ROADMAP.md` | Name the exact environment: `whisper.cpp` commit `9781133…`, `tiny.en`, AMD EPYC 7763 GitHub runner. This is not end-to-end microphone latency and not a universal accuracy score. |
| The current trust suite contains 58 deterministic tests; exact-commit CI covers Python 3.9, 3.11, and 3.14, branch coverage above 70%, build, hashed dependency audit, Bandit, Ruff, and compilation. | P4 implementation evidence in `ROADMAP.md`; run `33018105244` | Treat this as source/CI proof, not physical audio-hardware proof. |
| Flatpak run `33018105481` passed manifest/AppStream/repository linting, an offline no-download rebuild, install, GTK/CLI smoke, and removal. | P4 implementation evidence in `ROADMAP.md` | One documented App-ID affiliation exception remains; this is not Flathub approval. |
| CodeQL run `33018105062` passed all detected languages with no open alerts at verification time. | P4 implementation evidence in `ROADMAP.md` | Say “no open alerts at verification time,” not “secure” or “vulnerability-free.” |

### Claims reserved for the successful v1 release

Use these only after the public `v1.0.0` release exists and every downloaded
asset has been checked:

- The v1 release publishes an installable Flatpak, checksum, CycloneDX SBOM,
  deterministic test report, Sigstore provenance bundle, and SBOM-attestation
  bundle.
- `gh attestation verify` succeeds against the downloaded v1 Flatpak.
- The release notes contain an explicit privacy delta, benchmark delta, support
  boundary, demo link, and help-wanted links.
- The version, tag, changelog, package metadata, and source all resolve to the
  same release commit.

The automation for these outcomes exists in `.github/workflows/release.yml`,
but configuration is not public-release proof. A successful tag workflow and
public re-download are the gate.

## Shared links and visual assets

- Project site: <https://othmaneblial.github.io/audio-capture/>
- Guided three-state tour GIF: <https://othmaneblial.github.io/audio-capture/assets/voice-transcriber-tour.gif>
- Ready state: <https://othmaneblial.github.io/audio-capture/assets/demo-01-ready.png>
- Listening state: <https://othmaneblial.github.io/audio-capture/assets/demo-02-active.png>
- Completed transcript: <https://othmaneblial.github.io/audio-capture/assets/demo-03-complete.png>
- Current stable release: <https://github.com/OthmaneBlial/audio-capture/releases/tag/v0.6.0>
- Latest release alias: <https://github.com/OthmaneBlial/audio-capture/releases/latest>
- Install/package guide: <https://github.com/OthmaneBlial/audio-capture/blob/main/docs/packaging/FLATPAK.md>
- Privacy notice: <https://github.com/OthmaneBlial/audio-capture/blob/main/docs/PRIVACY.md>
- Field-level data flow: <https://github.com/OthmaneBlial/audio-capture/blob/main/docs/DATA-FLOW.md>
- Provider boundary matrix: <https://github.com/OthmaneBlial/audio-capture/blob/main/docs/PROVIDERS.md>
- Support boundary: <https://github.com/OthmaneBlial/audio-capture/blob/main/docs/SUPPORT.md>
- Compatibility evidence: <https://github.com/OthmaneBlial/audio-capture/blob/main/docs/COMPATIBILITY.md>
- Benchmark method: <https://github.com/OthmaneBlial/audio-capture/blob/main/benchmarks/README.md>
- Committed benchmark receipt: <https://github.com/OthmaneBlial/audio-capture/blob/main/benchmarks/results/local-tiny-en-github-runner.json>
- Issues: <https://github.com/OthmaneBlial/audio-capture/issues>
- Good first issues: <https://github.com/OthmaneBlial/audio-capture/labels/good%20first%20issue>
- Help wanted: <https://github.com/OthmaneBlial/audio-capture/labels/help%20wanted>

For a versioned launch, replace `/blob/main/` and `/tree/main/` with the exact
release tag so the post keeps pointing to immutable evidence.

### Official external links already appropriate to cite

- Groq speech-to-text documentation: <https://console.groq.com/docs/speech-to-text>
- Groq customer-data documentation: <https://console.groq.com/docs/your-data>
- Groq privacy policy: <https://groq.com/privacy-policy>
- LibriSpeech corpus and license context: <https://openslr.org/12/>
- `whisper.cpp` CLI contract: <https://github.com/ggml-org/whisper.cpp/blob/master/examples/cli/README.md>
- Flatpak manifest documentation: <https://docs.flatpak.org/en/latest/manifests.html>
- Flatpak sandbox permissions: <https://docs.flatpak.org/en/latest/sandbox-permissions.html>
- GitHub artifact attestations: <https://docs.github.com/en/actions/how-tos/secure-your-work/use-artifact-attestations/use-artifact-attestations>

## Post 1 — technical launch

### Recommended angle

**Building a privacy-explicit Linux dictation app: bounded audio, local VAD,
visible provider boundaries, and release evidence.**

The technical story should explain design decisions and their tradeoffs, not
pretend the cloud disappears. The memorable contrast is: privacy claims are
often adjectives; here the boundary is a UI state, a data-flow table, a bounded
implementation, a regression suite, and a release artifact.

### Suggested title options

1. “Building a privacy-explicit Linux voice-to-text app”
2. “From microphone to text: the auditable architecture of Voice Transcriber”
3. “Local VAD, explicit cloud: designing trustworthy Linux dictation”
4. After v1 proof: “How Voice Transcriber makes Linux dictation releases verifiable”

### Hook options

- “The honest architecture diagram for most cloud transcription tools should
  have an arrow leaving the device. Voice Transcriber keeps that arrow—and
  makes it visible.”
- “I did not want another audio recorder. I wanted a small Linux desk that
  forgets the audio and keeps only the words I choose.”
- “A privacy label is not enough. I wanted every release to answer: what leaves
  the device, what is stored, what is bounded, and what can a user verify?”

### Evidence-led outline

1. **Start with the job, not the stack.** Short notes/prompts/emails/tickets,
   not meeting capture. Show the animated tour before explaining GTK.
2. **Draw the exact path.** `microphone -> bounded frames -> local VAD ->
   completed segment -> provider -> editable transcript`. Explain why silence
   is not a request and why “local VAD” is not “offline transcription.”
3. **Explain transient defaults.** No app-created raw-audio files, bounded
   capture/request work, no analytics or project server, live transcript in
   GTK memory, text history off by default.
4. **Make the boundary a product feature.** The active provider and data
   destination are visible in onboarding, Settings, and the desk. The Groq key
   is user-managed. Provider errors are normalized without logging response
   bodies, credentials, transcripts, or local model paths.
5. **Show the provider abstraction without overselling it.** Groq is supported;
   local `whisper.cpp` is deliberately feature-flagged, source-only, and
   disabled in Flatpak until it passes equal packaging/hardware gates.
6. **Use the benchmark as a reproducibility example.** Include corpus checksum,
   25-speaker selection, exact model/build/hardware, numerator/denominator, and
   p50/p95. Explain why the project refuses a context-free “94.1% accurate”
   slogan.
7. **Show distribution evidence.** Current release: checksum-backed x86_64
   Flatpak. After successful v1 only: SBOM, test report, provenance and
   attestation verification.
8. **End with bounded contribution tasks.** Ask for one exact compatibility,
   accessibility, translation, benchmark, fixture, packaging, or release-QA
   contribution—not a generic star request.

### Technical screenshots/diagrams to include

- Animated tour above the fold.
- A small two-column boundary diagram: “stays local” versus “sent after speech
  closes.” Use the wording from `docs/DATA-FLOW.md`.
- A benchmark receipt card containing corpus, model revision/checksum,
  hardware, 37/627, p50, and p95.
- For v1 only, a terminal excerpt showing checksum verification and successful
  `gh attestation verify` against the downloaded artifact.

### Technical CTA

“Pick one open proof gap—your Linux audio stack, an Orca pass, a translated
install guide, a local benchmark reproduction, or release-asset verification—
and post the smallest sanitized result that another contributor can repeat.”

## Post 2 — user-focused demo launch

### Recommended angle

**Speak the rough thought, correct the text, and move it into the tool where it
belongs—without building an audio archive.**

This post should be visual and outcome-first. Mention architecture only where
it answers a user question: “Is it recording me?”, “Where does speech go?”,
“Do I need a key?”, “Can I delete the result?”, and “Will it run on my setup?”

### Suggested title options

1. “Voice Transcriber: a focused Linux dictation desk for notes and prompts”
2. “Speak it, review it, paste it: private-by-design dictation for Linux”
3. “A Linux voice-to-text workflow that shows where your audio goes”
4. “Turn a spoken thought into editable text on Linux”

### Hook options

- “Sometimes the sentence is already clear in your head; typing is the part
  that gets in the way.”
- “Voice Transcriber is for the 30 seconds between having an idea and putting
  it into an email, prompt, ticket, or note.”
- “Open it, confirm the microphone, speak, edit the text, and decide whether to
  copy, export, keep, or clear it.”

### 60–90 second demo sequence

1. Open the app without a key. Show microphone discovery, Settings, and the
   visible privacy/provider boundary. State that no fake transcript appears.
2. Configure a tester-owned Groq key and acknowledge that completed speech
   segments will leave the device.
3. Select a microphone and move the local input meter with a short phrase.
4. Start listening and dictate one realistic sample, such as: “Draft a short
   issue explaining that the export confirmation should name the destination.”
5. Stop, correct one word, undo/redo once, and show pending-to-complete state.
6. Copy the text and paste it into a neutral local editor. Do not imply the app
   pasted automatically.
7. Export once to a visibly chosen destination, then clear the desk.
8. Show that history is off by default; briefly point to the opt-in retention
   control rather than enabling it silently.
9. Close on the support matrix and the exact release download, followed by one
   targeted feedback question.

### User benefits that can be stated without hype

- Faster capture of a rough thought when typing interrupts concentration.
- A small native desk with no recording library or account owned by the
  project.
- Visible microphone, provider, request state, transcript, and retention
  choices.
- Editable text before it reaches the destination.
- Intentional copy/export/clear behavior instead of silent automation.
- A release and privacy boundary that can be inspected before committing a key.

### User CTA

“Try one short note on a supported x86_64 Linux desktop, then report the exact
session/audio combination and the first point where the workflow felt unclear.
Do not attach recordings, transcripts, credentials, or full system dumps.”

## Honest limitations block for both posts

Keep a compact version of this close to the install CTA:

> The current Flatpak targets x86_64 Linux and uses a user-managed Groq key for
> supported transcription. X11/Wayland and PipeWire/PulseAudio declarations and
> automated smoke tests are published, but representative real-microphone
> reports are still being collected. The local whisper.cpp provider is an
> experimental source-only path, disabled in Flatpak. No macOS, Windows,
> browser, mobile, AppImage, Debian package, Bluetooth microphone, universal
> global shortcut, or fully offline support is claimed.

Additional caveats for technical copy:

- The product tour uses synthetic sample text and mirrors current UI states; it
  is not a recording of a real provider response.
- The benchmark measures local file transcription on one named GitHub runner,
  not capture latency, cloud latency, every accent/language, or laptop battery
  behavior.
- The app cannot control provider-side processing/retention, clipboard history,
  exported-file backups, OS-level capture, or a user-supplied local binary.
- Existing automated GTK/Xvfb, package, and unit checks do not replace physical
  microphone plus desktop-compositor evidence.
- `v0.6.0` does not include the later SBOM/provenance assets; claim those only
  after the v1 release proves them publicly.

## SEO suggestions

### Technical post

- **Primary keyword:** `open source Linux voice to text`
- **Secondary:** `Linux dictation app`, `GTK speech to text`, `local voice
  activity detection`, `Whisper Linux app`, `privacy focused transcription`,
  `Flatpak voice transcription`, `voice transcription architecture`,
  `software supply chain attestation`
- **Suggested slug:** `/blog/open-source-linux-voice-to-text-architecture`
- **Suggested meta description:** “How Voice Transcriber combines local voice
  detection, explicit cloud boundaries, bounded audio processing and verifiable
  Linux releases.”

### User demo post

- **Primary keyword:** `Linux dictation app`
- **Secondary:** `voice to text Linux`, `speech to text Linux`, `dictate notes
  on Linux`, `Linux voice typing`, `open source dictation`, `GTK voice
  transcriber`, `privacy focused voice to text`
- **Suggested slug:** `/blog/linux-dictation-app-demo`
- **Suggested meta description:** “See how Voice Transcriber turns a spoken
  note into editable text on Linux while showing what stays local and what is
  sent for transcription.”

### SEO guardrails

- Put the primary keyword in the title, H1, first 100 words, slug, and meta
  description, but keep the project name near it.
- Prefer “privacy-explicit” or “shows where audio goes” over the unsupported
  claims “private,” “anonymous,” “zero retention,” or “offline.”
- Do not target “meeting transcription,” “Windows voice typing,” “Mac
  dictation,” or “real-time translation” unless the product scope changes and
  matching evidence exists.
- Add descriptive alt text to the three screenshots; label all preview text as
  synthetic.
- Link internally to the privacy notice, support matrix, data flow, Flatpak
  guide, benchmark method, and contributor map; link externally only to
  authoritative provider, corpus, packaging, and attestation documents.

## Feedback questions worth asking

Ask two or three per post, not all of them at once.

### First-success and UX

1. On which distribution, desktop session, audio server, and microphone type
   did the first copied transcript succeed or fail?
2. How many minutes passed from install to the first useful copied transcript?
3. Which step was least clear: install, key setup, microphone selection,
   provider boundary, start/stop, correction, copy/export, or deletion?
4. Did the input meter make the selected microphone obvious before recording?
5. Was the difference between live transcript, opt-in history, clipboard, and
   explicit export understandable?

### Trust and privacy

6. Before pressing Start, could you correctly explain what stays local and
   what is sent to Groq?
7. Which additional proof would change your willingness to try it: real-device
   compatibility, provider-policy summary, release attestation, benchmark on
   laptop hardware, accessibility review, or local-mode packaging?
8. Was any label easy to misread as “fully offline” or “zero provider
   retention”? Quote only the label, never private transcript content.
9. Does history-off-by-default match your expectation, and is its storage and
   deletion boundary clear enough?

### Contribution and roadmap

10. Which bounded task could you verify in one session: device matrix,
    accessibility, translation, package smoke, provider fixture, benchmark, or
    release QA?
11. If you reproduced a failure, can you reduce it to sanitized diagnostics and
    steps without sharing a recording, transcript, key, or full environment?
12. What one daily dictation workflow is missing without turning the app into a
    meeting recorder or generic assistant?

## Recommended publication order

1. Finish and publicly verify the v1 release artifacts.
2. Update immutable release-tag links, exact digest, workflow evidence, and the
   limitations block in both drafts.
3. Publish the user demo first so technical readers have a concrete workflow to
   inspect.
4. Publish the technical article next, linking to the demo and evidence.
5. Repurpose each article into one short GitHub/LinkedIn-style post built around
   a single feedback question; do not lead with “please star.”
6. Convert useful responses into a compatibility entry, FAQ, reproducible bug,
   credited documentation change, or narrow issue. Report zero feedback as
   zero feedback rather than inventing social proof.

