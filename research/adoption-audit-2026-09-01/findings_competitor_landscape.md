# Open-source Linux dictation landscape

Snapshot: **2026-09-01**. Adoption counts are point-in-time GitHub signals, not verified active-user counts. Research used official repositories, READMEs, release pages, project sites, and GitHub's repository API.

## What the field already offers

| Project | Current proposition and workflow | Visible adoption / activity | Implication for Voice Transcriber |
| --- | --- | --- | --- |
| [Speech Note](https://github.com/mkiol/dsnote) | Full offline GUI workbench for STT, TTS, translation, and notes. Multiple local engines, in-app model browser, [Flathub install](https://flathub.org/apps/net.mkiol.SpeechNote), global shortcuts, clipboard, and active-window insertion; Wayland insertion uses `ydotool`. | **1,620 stars / 73 forks**; repository pushed 2026-09-01. | The “desktop transcript editor + offline privacy” space is already mature. A GTK desk alone is not differentiation. |
| [nerd-dictation](https://github.com/ideasman42/nerd-dictation) | Small, hackable, offline Vosk CLI. Users bind begin/end/cancel commands themselves; supports PipeWire/PulseAudio and several X11/Wayland output tools plus custom text-processing hooks. | **1,913 stars / 170 forks**; last push 2025-10-10; no GitHub release. | Simplicity and hackability have durable appeal, but the setup is expert-oriented. Voice Transcriber should not try to out-hack this CLI. |
| [Vocalinux](https://github.com/VocaHQ/vocalinux) | Polished offline GUI dictation into any app: push-to-talk/toggle, whisper.cpp/Whisper/Vosk, Vulkan acceleration, tray, audio feedback, graphical settings, model management, AppImage and AUR. | **791 stars / 84 forks** since 2025-04; active [v0.16.1 release](https://github.com/VocaHQ/vocalinux/releases/tag/v0.16.1) on 2026-08-30; 63 x86_64 AppImage downloads observed two days after release. | “100% offline Linux voice typing that just works” is already a direct, credible claim with visible product proof. |
| [Voxtype](https://github.com/peteonrails/voxtype) | Linux-native, local-by-default cursor dictation with seven engines, CPU/GPU packages, compositor keybindings, OSD/audio feedback, replacements/spoken punctuation, optional local-LLM pipe, and meeting export. Signed `.deb`, `.rpm`, AUR, and binary releases. | **1,330 stars / 113 forks** since 2025-11; active [v1.0.1 release](https://github.com/peteonrails/voxtype/releases/tag/v1.0.1) on 2026-08-31. | Performance, engine breadth, packaging, Wayland integration, and “local Wispr Flow” are difficult territory for a Groq-first app to own. |
| [whisrs](https://github.com/y0sif/whisrs) | Hybrid cloud/local Rust daemon: Groq, Deepgram, OpenAI, whisper.cpp, or local sidecars; layout-aware cursor injection, interactive setup, tray/OSD, GNOME extension, history, TTS, and LLM commands. Its README explicitly distinguishes daily-driven and community-confirmed desktops from unverified ones. | **99 stars / 30 forks** since 2026-03; [v0.1.26](https://github.com/y0sif/whisrs/releases/tag/v0.1.26) published 2026-08-18; 71 full x86_64 tarball downloads observed. | Even the hybrid provider niche already has a fast-moving Linux-first entrant with explicit compatibility evidence. |

Counts above were read from the official GitHub API endpoints for [Speech Note](https://api.github.com/repos/mkiol/dsnote), [nerd-dictation](https://api.github.com/repos/ideasman42/nerd-dictation), [Vocalinux](https://api.github.com/repos/VocaHQ/vocalinux), [Voxtype](https://api.github.com/repos/peteonrails/voxtype), and [whisrs](https://api.github.com/repos/y0sif/whisrs).

## Saturated claims to avoid

Voice Transcriber should not lead with any of these as if they were unique:

- “Private/offline Linux dictation” — Speech Note, Vocalinux, Voxtype, and nerd-dictation already ship local paths; Voice Transcriber's packaged path is cloud-based.
- “Works on Wayland and X11” or “type anywhere” — competitors document compositor-specific injection and fallbacks; Voice Transcriber intentionally does not simulate paste and has no global shortcut claim.
- “Open-source Wispr Flow alternative” — this is now the default category framing across multiple newer projects.
- Model/engine breadth, GPU speed, hotkeys, tray/OSD, or meeting transcription — Voxtype and Vocalinux are materially ahead on these axes.
- “Flatpak available” by itself — Speech Note is already on Flathub; a manually downloaded Flatpak asset carries more evaluation friction.

## Positioning Voice Transcriber could credibly own

1. **Review-first dictation, not invisible text injection.** Frame the product as a deliberate `capture -> review/edit -> copy/export` desk for prompts, emails, tickets, and drafts. The segment states, undo/redo, explicit export, optional bounded text history, and absence of automatic cross-app typing support this claim. This is a narrower audience than system-wide voice typing, but it is coherent and safer for high-consequence text.

2. **The inspectable cloud boundary.** The strongest distinctive asset is not “privacy” in the abstract; it is precise disclosure: local VAD, silence excluded, completed segments sent only after explicit consent, no app-created audio files, provider limitations stated, opt-in transcript retention, and diagnostics that do not silently probe the network. Competitor READMEs generally foreground “offline”; Voice Transcriber can own **honest, visible provider choice and data flow** for users who value cloud speed but want informed control.

3. **Low-hardware, no-model-download onboarding.** Groq-first transcription can be positioned as the fast path for users who do not want multi-gigabyte models, GPU tuning, or resident model RAM. This must always sit beside the explicit cloud disclosure; claiming general privacy would lose credibility against local-first competitors.

4. **Failure-aware, evidence-backed desktop UX.** Visible pending/complete/error states, bounded queues, recoverable network/rate-limit errors, microphone diagnostics, and a scoped compatibility matrix can become a trust proposition: users can tell what happened and what left the machine. This is more defensible than broad “works everywhere” language.

## Adoption takeaway

There is demonstrable star interest in Linux dictation: two focused projects created within roughly the last year already show about **800–1,300 stars**, while older tools sit around **1,600–1,900**. That proves category demand, not automatic demand for this implementation. Voice Transcriber is currently at **0 stars** on the [official repository](https://github.com/OthmaneBlial/audio-capture), and its supported package lacks the category's most expected behaviors: supported local inference, system-wide hotkey/insertion, and low-friction repository distribution.

The credible conversion story is therefore: **“Dictate sensitive or high-consequence drafts into a transparent review desk; see exactly when speech crosses the provider boundary; edit before anything reaches another app.”** If the project instead wants the broader daily voice-typing audience, supported local inference plus reliable Wayland/X11 insertion and mainstream packaging are table stakes, not differentiators.

## Sources

- Speech Note official README and install: https://github.com/mkiol/dsnote
- Speech Note Flathub listing: https://flathub.org/apps/net.mkiol.SpeechNote
- nerd-dictation official README: https://github.com/ideasman42/nerd-dictation/blob/main/readme.rst
- Vocalinux official README/site/release: https://github.com/VocaHQ/vocalinux · https://vocalinux.com/ · https://github.com/VocaHQ/vocalinux/releases/tag/v0.16.1
- Voxtype official README/site/release: https://github.com/peteonrails/voxtype · https://voxtype.io/ · https://github.com/peteonrails/voxtype/releases/tag/v1.0.1
- whisrs official README/release: https://github.com/y0sif/whisrs · https://github.com/y0sif/whisrs/releases/tag/v0.1.26
