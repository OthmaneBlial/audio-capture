# Contributor map

Voice Transcriber welcomes small, testable changes that preserve its explicit
privacy boundary. You do not need a microphone, Groq account, or API key to
make a useful contribution.

## Choose the shortest relevant path

| If you want to… | Start here | Evidence expected |
| --- | --- | --- |
| Understand the process and boundaries | [Architecture tour](ARCHITECTURE-TOUR.md) | Name the component and contract your change affects |
| Run checks without credentials or hardware | [Development without a key](DEVELOPMENT-WITHOUT-KEY.md) | Format, tests, clippy, and dependency-policy output |
| Add audio/provider test coverage | [Deterministic audio tests](FAKE-AUDIO-FIXTURES.md) | Rust fixtures or injected boundaries with no hardware dependency |
| Change capture states or interaction | [UI contribution guide](UI-GUIDE.md) | Unit coverage plus a real desktop screenshot or clear manual gap |
| Change native packaging or releases | [Packaging guide](PACKAGING-GUIDE.md) | Archive, checksum, extraction, and target-specific evidence |
| Propose a bounded improvement | [Issue-to-PR path](ISSUE-TO-PR.md) | A focused issue and pull request linked to acceptance criteria |

The project-wide setup, review expectations, and private security-reporting
route remain in [CONTRIBUTING.md](../../CONTRIBUTING.md). The previous issue
queue was closed when the runtime was rewritten; new tasks should describe the
current Rust code and be opened only after the scope is checked against this
repository.

## Definition of done

A contribution is ready when the user-visible contract is clear, deterministic
checks pass, documentation matches behavior, and any physical-device or
provider-account validation that was not performed is stated plainly. Never
include an API key, recording, transcript, config file, home path, or full
environment dump in an issue, fixture, log, or pull request.
