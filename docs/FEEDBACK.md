# Public feedback loop

Voice Transcriber does not add usage tracking to measure adoption. Useful
feedback becomes a reviewable public artifact instead.

## Where feedback goes

| Feedback | Public route | Resulting artifact |
| --- | --- | --- |
| Reproducible app problem | Bug report form | Test plus fix or documented limitation |
| Linux audio/display combination | Compatibility form | Evidence row in `docs/COMPATIBILITY.md` or a scoped fix |
| Focused workflow improvement | Feature request form | Accepted issue with an explicit contract |
| Repeated setup question | Existing issue or bug report | Answer in `docs/FAQ.md` or troubleshooting docs |
| Security or privacy flaw | Private security policy | Coordinated fix and advisory when appropriate |

GitHub Discussions remains intentionally disabled until the maintainer can
respond there regularly. Issue forms create less ambiguity and attach feedback
to reproducible acceptance criteria.

## What maintainers record

For each useful report, maintainers should link the source issue from the
resulting compatibility row, FAQ entry, documentation change, or regression
test. Credit contributors in the pull request and release notes when they opt
to be named. Aggregate only public repository signals such as downloads,
issues, and merged contributions; never collect audio, transcript, or hidden
behavioral telemetry.

## Questions that improve the product

- Which installation step was unclear or failed?
- Before speaking, could you explain what stays local and what leaves?
- Did the input meter and session state make the active microphone obvious?
- Which exact desktop, audio route, and package version did you test?
- What single dictation task would make the app worth opening tomorrow?

Answers should exclude recordings, transcript content, credentials, private
paths, and unrelated system data.
