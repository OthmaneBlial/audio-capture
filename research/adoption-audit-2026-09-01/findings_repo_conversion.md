# Repository and demo conversion findings

Research snapshot: 2026-09-01. This track reviewed current repository pages/READMEs and GitHub's official guidance. Star counts are useful adoption signals, not proof that any README element caused that adoption.

## Comparable repositories

| Repository | Current signal | Directly observed conversion pattern |
| --- | ---: | --- |
| [Handy](https://github.com/cjpais/Handy) | 30,800 stars; pushed 2026-08-31 ([GitHub API](https://api.github.com/repos/cjpais/Handy)) | Opens with a one-sentence offline promise and the four-step job story (“press, speak, release, get text”), then quick start. It states Linux/Wayland limitations, troubleshooting paths, system requirements, a roadmap, and release-signature verification. |
| [Buzz](https://github.com/chidiwilliams/buzz) | 21,258 stars; pushed 2026-08-28 ([GitHub API](https://api.github.com/repos/chidiwilliams/buzz)) | Uses license, CI, coverage, release, and download badges; a large real-product banner; distro-specific Flatpak/Snap/AppImage installs; an honest unsigned-Windows warning; a screenshot gallery; and a direct “star and share” support request. |
| [VoiceInk](https://github.com/Beingpax/VoiceInk) | 6,231 stars; pushed 2026-09-01 ([GitHub API](https://api.github.com/repos/Beingpax/VoiceInk)) | Puts the icon, platform/release/download/star badges, a prominent download button, and a product screenshot before the feature list. It makes the commercial binary versus build-from-source tradeoff explicit and clearly says pull requests are currently closed. |
| [OpenWhispr](https://github.com/OpenWhispr/openwhispr) | 5,944 stars; pushed 2026-09-01 ([GitHub API](https://api.github.com/repos/OpenWhispr/openwhispr)) | Leads with category positioning, platform/release/download/star badges, and a compact Website / Docs / Download / API / Changelog link row. Its download table maps each platform directly to a usable artifact and its privacy paragraph distinguishes local from optional cloud processing. |
| [Speech Note](https://github.com/mkiol/dsnote) | 1,620 stars; pushed 2026-09-01 ([GitHub API](https://api.github.com/repos/mkiol/dsnote)) | Linux-native proof: a large Flathub CTA, exact offline/no-network language, documented models, global shortcuts and active-window insertion, contribution/translation routes, explicit star/review/share CTAs, and a long maintained list of demos and independent reviews. |

## Evidence from the repositories

1. **The first screen answers “what happens when I use it?”** Handy describes the complete interaction in plain language before architecture. OpenWhispr similarly says “press a hotkey, speak” and names the result. These are easier to evaluate than a generic list of technologies or adjectives.

2. **Install choice is converted into a small, platform-shaped decision.** Buzz exposes Flatpak, Snap, and AppImage under Linux; Speech Note puts Flathub at the top; OpenWhispr lists artifact formats in a compact table. VoiceInk also separates “download the maintained binary” from “build the source,” so the cost of each route is clear.

3. **Visual proof is product proof, not decoration.** Buzz shows a banner plus seven captioned workflow screenshots. VoiceInk places a real app image immediately under its opening description. Speech Note links current release demos and independent coverage. A viewer can verify that a usable interface and workflow exist without installing first.

4. **Trust comes from bounded, inspectable statements.** Handy documents known platform issues, system requirements, workarounds, and artifact verification. Buzz discloses an unsigned installer warning. OpenWhispr says which paths are local and which are cloud-enabled. VoiceInk states the paid-binary/source-build distinction and its current PR policy. These disclosures reduce unpleasant surprises.

5. **Contribution asks are specific.** Handy gives five concrete steps; OpenWhispr links a development guide; Speech Note offers code, issue, feature-request, and translation routes. VoiceInk demonstrates that an honest “not accepting PRs” statement is better than implying a contribution path that maintainers will not service.

6. **The star request follows delivered value.** Buzz asks users to star and share after installation instructions. Speech Note asks for a star, package-manager review, social mention, or donation in its support section. Neither makes starring the primary hero action.

## Official GitHub guidance

- GitHub says a README is often the first thing visitors see and should explain what the project does, why it is useful, how to start, where to get help, and who maintains/contributes: [About READMEs](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-readmes).
- GitHub's community profile treats README, `LICENSE`, `CODE_OF_CONDUCT`, and `CONTRIBUTING` as recommended community-health files; it also supports a security policy and valid issue templates. Potential contributors use this profile to decide whether to participate: [About community profiles](https://docs.github.com/en/communities/setting-up-your-project-for-healthy-contributions/about-community-profiles-for-public-repositories).
- GitHub says a custom social-preview image helps identify a project when repository links are shared, recommending 1280×640 for best display and a solid background when uncertain: [Social media preview](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/customizing-your-repositorys-social-media-preview).

## Inference and recommended application to Voice Transcriber

The following is synthesis, not causal proof about star growth.

1. **Make the evaluation path complete in the first viewport:** one precise Linux job statement, one honest offline/privacy sentence, a short real workflow GIF or video poster, and a primary “Download for Linux” action. Keep “Build from source” secondary.
2. **Show the whole workflow in 15–30 seconds:** start capture, visible recording state, stop, transcript result, and copy/export or insertion into the target app. Add 3–5 captioned screenshots below for settings, model selection, history/export, and error/permission states. Avoid mockups that cannot be reproduced in the release.
3. **Use a release-shaped install matrix:** only list formats that are actually maintained, with architecture, minimum distro/session requirements, package size/model download expectations, and one copyable command or direct artifact link per route. State X11/Wayland behavior explicitly.
4. **Turn privacy into an auditable data-flow box:** say whether audio, transcripts, crash data, or telemetry ever leave the machine; whether temporary audio is retained; which model downloads require network access; what permissions are needed; and which optional integrations change the boundary. Link the relevant code/configuration. Avoid “100% private” unless every shipped path supports that claim.
5. **Add trust proof near the install decision:** license, latest release, CI status, supported Linux targets, checksums/signature verification, known limitations, troubleshooting, and a security-reporting route. Download counts may be shown if accurate, but should not replace functional proof.
6. **Make contribution routes serviceable:** add/link `CONTRIBUTING`, issue forms for bugs and feature requests, a security policy, reproducible development/test commands, and a small set of genuinely scoped `good first issue` tasks. If PR capacity is limited, say so and offer documentation, testing, distro packaging, or translation paths instead.
7. **Ask for a star after the user has evidence:** a restrained closing line such as “If Voice Transcriber works on your Linux setup, star the repo and tell us your distro/session” combines the growth request with useful feedback. Also set a readable 1280×640 GitHub social preview based on the real interface.

Highest-leverage sequence: real demo proof → direct maintained Linux download → auditable privacy/limitations → contribution/help routes → restrained star/share CTA. This reduces the largest evaluation risks before asking for advocacy.
