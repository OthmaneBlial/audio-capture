# Contributor map

Voice Transcriber welcomes small, testable changes that preserve its explicit
privacy boundary. You do not need a microphone, Groq account, or API key to
make a useful first contribution.

## Choose the shortest relevant path

| If you want to… | Start here | Evidence expected |
| --- | --- | --- |
| Understand the process and boundaries | [Architecture tour](ARCHITECTURE-TOUR.md) | Name the component and contract your change affects |
| Run checks without credentials or hardware | [Development without a key](DEVELOPMENT-WITHOUT-KEY.md) | Unit tests, Ruff, and compilation |
| Add audio/provider test coverage | [Fake audio fixtures](FAKE-AUDIO-FIXTURES.md) | Deterministic bytes and injected external boundaries |
| Change GTK copy, states, or interaction | [UI contribution guide](UI-GUIDE.md) | Unit coverage plus mapped GTK/accessibility evidence where relevant |
| Change Flatpak or release files | [Packaging guide](PACKAGING-GUIDE.md) | Lints, offline rebuild, installed-bundle smoke, and explicit manual gaps |
| Pick up a public task | [Issue-to-PR path](ISSUE-TO-PR.md) | A focused PR linked to acceptance criteria |

The project-wide setup, review expectations, and private security-reporting
route remain in [CONTRIBUTING.md](../../CONTRIBUTING.md). Current newcomer-sized
tasks are labelled [`good first issue`](https://github.com/OthmaneBlial/audio-capture/labels/good%20first%20issue); tasks needing an additional environment or reviewer are labelled [`help wanted`](https://github.com/OthmaneBlial/audio-capture/labels/help%20wanted).

## Definition of done

A contribution is ready when the user-visible contract is clear, deterministic
checks pass, documentation matches behavior, and any physical-device or
provider-account validation that was not performed is stated plainly. Never
include an API key, recording, transcript, config file, home path, or full
environment dump in an issue, fixture, log, or pull request.
