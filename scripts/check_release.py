#!/usr/bin/env python3
"""Fail a release when public version surfaces or changelog evidence drift."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _match(path: str, pattern: str) -> str:
    text = (ROOT / path).read_text(encoding="utf-8")
    found = re.search(pattern, text, flags=re.MULTILINE)
    if not found:
        raise ValueError(f"Could not read version from {path}")
    return found.group(1)


def release_section(version: str) -> str:
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    pattern = rf"^## \[{re.escape(version)}\].*?\n(?P<body>.*?)(?=^## \[|\Z)"
    found = re.search(pattern, changelog, flags=re.MULTILINE | re.DOTALL)
    if not found:
        raise ValueError(f"CHANGELOG.md has no {version} release section")
    return found.group("body").strip()


def check(expected: str) -> dict[str, str]:
    versions = {
        "main.py": _match("main.py", r'^__version__ = "([^"]+)"'),
        "pyproject.toml": _match("pyproject.toml", r'^version = "([^"]+)"'),
        "AppStream": _match(
            "packaging/io.github.othmaneblial.audio_capture.metainfo.xml",
            r'<release version="([^"]+)"',
        ),
        "Flatpak smoke": _match(
            "packaging/smoke_test_flatpak.sh", r'voice-transcriber ([0-9]+\.[0-9]+\.[0-9]+)"'
        ),
    }
    mismatches = {surface: value for surface, value in versions.items() if value != expected}
    if mismatches:
        details = ", ".join(f"{surface}={value}" for surface, value in mismatches.items())
        raise ValueError(f"Expected release {expected}; mismatched surfaces: {details}")
    section = release_section(expected)
    if "### Privacy" not in section:
        raise ValueError(f"CHANGELOG.md {expected} must contain a Privacy subsection")
    if "### Verification" not in section:
        raise ValueError(f"CHANGELOG.md {expected} must contain a Verification subsection")
    return versions


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tag", help="Release tag, for example v1.0.0")
    args = parser.parse_args()
    if not re.fullmatch(r"v[0-9]+\.[0-9]+\.[0-9]+", args.tag):
        raise SystemExit("release tag must match vMAJOR.MINOR.PATCH")
    version = args.tag.removeprefix("v")
    for surface, value in check(version).items():
        print(f"{surface}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
