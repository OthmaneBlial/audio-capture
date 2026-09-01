# Installation, privacy, and desktop-integration findings

Research date: 1 September 2026. Sources are current official documentation,
project repositories, and package listings. Product-gap statements below are
inferences from those sources and the current Voice Transcriber repository.

## Evidence that sets user expectations

- **A normal Linux install is remote-backed and updateable.** Flatpak's user
  documentation treats remotes as the place users search for apps, supports
  installation by app ID or `.flatpakref`, and updates installed apps with
  `flatpak update`. Speech Note is already discoverable on Flathub with an
  Install action, `x86_64` and `aarch64` builds, and roughly 8,400 monthly
  downloads on the listing at review time. By comparison, Voice Transcriber's
  downloaded bundle requires several manual commands and explicitly creates no
  update remote.
  Sources: [Flatpak usage](https://docs.flatpak.org/en/latest/using-flatpak.html),
  [Speech Note on Flathub](https://flathub.org/en/apps/net.mkiol.SpeechNote).

- **Offline is a concrete packaged mode, not an architectural possibility.**
  Speech Note's Flathub listing says voice and text processing remain local and
  that no data is sent to the Internet. Its project documentation exposes
  in-app model downloads and packages `whisper.cpp` in its base and smaller
  “Tiny” variants. The upstream `whisper.cpp` project supports CPU-only and
  several GPU paths, quantization, and Linux; its published model resource
  examples range from 75 MiB disk / about 273 MB memory for `tiny` to 2.9 GiB /
  about 3.9 GB for `large`. Voice Transcriber's local provider is currently a
  source-only, user-assembled experiment disabled in the Flatpak.
  Sources: [Speech Note repository](https://github.com/mkiol/dsnote),
  [whisper.cpp repository](https://github.com/ggml-org/whisper.cpp).

- **Desktop dictation means activation while another application has focus.**
  Speech Note provides actions to start/cancel listening, copy the result, or
  target the active window, plus configurable global shortcuts. The official
  XDG Desktop Portal `GlobalShortcuts` v2 API supplies session-bound shortcuts,
  user-facing binding UI, and separate activated/deactivated signals suitable
  for global hold-to-talk. Direct text insertion remains a separate and fragile
  problem: Speech Note documents that its Wayland path requires an external
  `ydotool` daemon and additional Flatpak socket permission.
  Sources: [Speech Note desktop actions](https://github.com/mkiol/dsnote#command-line-options),
  [XDG Global Shortcuts portal](https://flatpak.github.io/xdg-desktop-portal/docs/doc-org.freedesktop.portal.GlobalShortcuts.html).

- **Cloud onboarding needs retention, location, and cost facts.** Groq's current
  data documentation says usage metadata is always retained and excludes
  inputs/outputs. Inference customer data is not retained by default, but input
  and output may be logged for reliability or abuse investigation for up to 30
  days; Zero Data Retention is available to all customers, and retained customer
  data is located in US GCP buckets. Groq's speech-to-text documentation also
  says each request has a 10-second minimum billed length. Since Voice
  Transcriber submits completed VAD segments as separate requests, short
  segments can make billed time materially larger than spoken time.
  Sources: [Groq customer-data controls](https://console.groq.com/docs/your-data),
  [Groq speech-to-text limits and pricing](https://console.groq.com/docs/speech-to-text).

## Actionable gaps for Voice Transcriber

| Priority | Gap | Recommended product change | Evidence of completion |
| --- | --- | --- | --- |
| **P0** | The release is a GitHub-hosted single-file Flatpak with no update remote, no software-center discovery, and only `x86_64`. | Finish the official Flathub submission, including the documented App-ID affiliation review. Make the primary README/site CTA the Flathub install; keep the checksumed bundle as an advanced fallback. Add `aarch64` only after an architecture-native build and microphone/provider smoke gate pass. | A fresh supported desktop can find, install, launch, and update the app through Flathub; the listing exposes screenshots, privacy boundary, permissions, architectures, and support links. |
| **P0** | “Local” cannot be selected in the supported package and requires users to source both a binary and model. This leaves the strongest privacy preference to a competitor. | Ship a supported local provider in the Flatpak, with an in-app model manager. Offer a small recommended CPU model first, show download size, expected RAM, language scope, license/source, checksum, acceleration status, and a delete-model action before download. Cloud must remain optional, not a prerequisite for exploring or using local mode. | Clean install to first local transcript succeeds without a Groq key, compiler, terminal, or network after the model is downloaded; offline behavior is verified with the network disabled and covered by release-specific hardware evidence. |
| **P0** | First-run cloud consent says audio leaves the device but does not give the user the current retention/location controls or the 10-second billing floor at the decision point. | Present a compact, dated Groq facts card before the first upload: what is sent, current default/exception retention, ZDR link, data location, and the minimum billed request length. Keep the live provider-policy links and avoid an undated promise. Show session spoken seconds versus estimated billed seconds locally; add a measured coalescing/economy option only if it preserves acceptable latency. | A first-time tester can correctly explain the boundary and cost model; the UI links directly to Groq Data Controls; automated tests prove the estimate never sends telemetry or stores audio/transcript content. |
| **P1** | In-window `Ctrl+Enter` and focused hold-to-talk stop working once the user returns to the editor, browser, or terminal where dictation is needed. | Implement `GlobalShortcuts` portal capability detection and bind global toggle plus hold-to-talk actions. Render the shortcut returned by the portal and give an explicit fallback on unsupported desktops. Add stable single-instance CLI/D-Bus actions for show, start, stop, cancel, and stop-and-copy. | Global activation works on supported GNOME/KDE Wayland and X11 test targets while another app is focused; unsupported portal backends fail visibly without grabbing keys. |
| **P1** | The product currently ends at Copy and deliberately avoids active-window insertion. | Keep clipboard delivery as the supported safe default. Do not make `ydotool` or simulated typing a mandatory dependency. If active-window insertion is explored, gate it as an opt-in integration with a narrow threat model, desktop-specific instructions, and real Wayland/X11 evidence. | Copy workflow is reliable across declared desktops; any insertion feature is clearly capability-gated and cannot silently broaden Flatpak filesystem/device access. |
| **P1** | The wizard configures inputs, but the real onboarding outcome is still an unproven end-to-end first copied transcript. | Turn onboarding into a resumable “first sentence” path: choose Local or Groq with side-by-side boundaries, pick and meter the microphone, run one real test phrase, review/edit, copy, and show success. Put microphone, portal, network/key, and model remediation inline. Preserve **Explore first**. | Ten privacy-safe clean-machine sessions meet the roadmap's under-five-minute install-to-first-copy target, with failures classified by step and no analytics added. |

## Recommended sequence

1. Submit the current cloud package to Flathub and prove install/update.
2. Add portal global shortcuts and a real first-sentence onboarding receipt.
3. Promote local transcription only after the runtime, model lifecycle, offline
   test, resource disclosure, and hardware matrix are supported in the package.
4. Treat active-window typing and additional architectures as evidence-gated
   expansions, not launch claims.

The defensible differentiator is therefore **privacy-explicit Linux dictation
with a genuine provider choice**: lightweight Groq when the user accepts a
dated, visible cloud boundary, and a packaged local mode when audio must not
leave the machine. Documentation already supports that position; installation
and daily desktop activation are the missing product proof.
