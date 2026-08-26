#!/usr/bin/env python3
"""Render complete GitHub release notes from a validated changelog section."""

from __future__ import annotations

import argparse
from pathlib import Path

from check_release import release_section


def render(version: str, commit: str) -> str:
    changes = release_section(version)
    return f"""# Voice Transcriber v{version}

Dictate a thought, review it, and intentionally keep or discard the text on Linux.

## See the workflow

Watch the [three-state guided demo](https://othmaneblial.github.io/audio-capture/#proof)
made with synthetic sample text, then read the
[support matrix](https://github.com/OthmaneBlial/audio-capture/blob/v{version}/docs/SUPPORT.md)
before installing.

## What changed

{changes}

## Install and verify

Download the `x86_64` Flatpak and its `.sha256` file from this release, then run:

```bash
sha256sum --check voice-transcriber-{version}-x86_64.flatpak.sha256
flatpak install --user ./voice-transcriber-{version}-x86_64.flatpak
```

The artifact maps to commit `{commit}`. This release also publishes a CycloneDX
SBOM and downloadable Sigstore provenance/SBOM-attestation bundles. Verify online
with `gh attestation verify voice-transcriber-{version}-x86_64.flatpak --repo OthmaneBlial/audio-capture`.

## Privacy delta

The versioned changelog above contains the complete **Privacy** subsection for
this release. The enduring microphone-to-export contract is documented in the
[privacy notice](https://github.com/OthmaneBlial/audio-capture/blob/v{version}/docs/PRIVACY.md)
and [threat model](https://github.com/OthmaneBlial/audio-capture/blob/v{version}/docs/THREAT-MODEL.md).

## Support boundary

The package targets x86_64 Linux, GTK 3, Wayland/fallback X11, and the system
PulseAudio/PipeWire route. Automated package and accessibility checks are not a
substitute for the separately recorded real-microphone gate. Read
[`docs/SUPPORT.md`](https://github.com/OthmaneBlial/audio-capture/blob/v{version}/docs/SUPPORT.md).

## Benchmark and help wanted

Published benchmark receipts live in
[`benchmarks/results/`](https://github.com/OthmaneBlial/audio-capture/tree/v{version}/benchmarks/results).
Small contributor tasks are labelled
[`good first issue`](https://github.com/OthmaneBlial/audio-capture/labels/good%20first%20issue)
and [`help wanted`](https://github.com/OthmaneBlial/audio-capture/labels/help%20wanted).
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.write_text(render(args.version, args.commit), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
