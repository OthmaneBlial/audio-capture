#!/usr/bin/env python3
"""Generate a deterministic CycloneDX SBOM for the Flatpak application layer."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import uuid
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def _requirements() -> list[dict[str, Any]]:
    dependency_data = json.loads(
        (ROOT / "packaging" / "python3-dependencies.json").read_text(encoding="utf-8")
    )
    hashes: dict[str, str] = {}
    for module in dependency_data["modules"]:
        source = module["sources"][0]
        package_name = module["name"].removeprefix("python3-").casefold()
        hashes[package_name] = source["sha256"]
    components = []
    for line in (ROOT / "packaging" / "requirements-flatpak.txt").read_text().splitlines():
        if not line or line.startswith("#"):
            continue
        name, version = line.split("==", 1)
        normalized = name.casefold()
        component = {
            "type": "library",
            "bom-ref": f"pkg:pypi/{normalized}@{version}",
            "name": name,
            "version": version,
            "purl": f"pkg:pypi/{normalized}@{version}",
        }
        if normalized in hashes:
            component["hashes"] = [{"alg": "SHA-256", "content": hashes[normalized]}]
        components.append(component)
    return components


def build_sbom(version: str, commit: str, timestamp: str) -> dict[str, Any]:
    manifest = (ROOT / "io.github.othmaneblial.audio_capture.yml").read_text(encoding="utf-8")
    runtime = re.search(r"^runtime: (.+)$", manifest, flags=re.MULTILINE)
    runtime_version = re.search(r'^runtime-version: "?([^"\n]+)', manifest, flags=re.MULTILINE)
    portaudio_version = re.search(r"portaudio/archive/refs/tags/v([^/]+)\.tar", manifest)
    if not (runtime and runtime_version and portaudio_version):
        raise ValueError("Could not read Flatpak runtime or PortAudio version")
    application_ref = f"pkg:generic/voice-transcriber@{version}"
    components = _requirements()
    components.extend(
        [
            {
                "type": "library",
                "bom-ref": f"pkg:generic/portaudio@{portaudio_version.group(1)}",
                "name": "PortAudio",
                "version": portaudio_version.group(1),
            },
            {
                "type": "framework",
                "bom-ref": f"pkg:generic/{runtime.group(1)}@{runtime_version.group(1)}",
                "name": runtime.group(1),
                "version": runtime_version.group(1),
                "scope": "required",
                "properties": [
                    {
                        "name": "voice-transcriber:flatpak-runtime",
                        "value": "runtime supplied outside the application bundle",
                    }
                ],
            },
        ]
    )
    return {
        "bomFormat": "CycloneDX",
        "specVersion": "1.6",
        "serialNumber": f"urn:uuid:{uuid.uuid5(uuid.NAMESPACE_URL, f'{version}:{commit}')}",
        "version": 1,
        "metadata": {
            "timestamp": timestamp,
            "component": {
                "type": "application",
                "bom-ref": application_ref,
                "name": "voice-transcriber",
                "version": version,
                "licenses": [{"license": {"id": "MIT"}}],
                "externalReferences": [
                    {
                        "type": "vcs",
                        "url": f"https://github.com/OthmaneBlial/audio-capture/tree/{commit}",
                    }
                ],
            },
            "properties": [
                {"name": "voice-transcriber:commit", "value": commit},
                {"name": "voice-transcriber:scope", "value": "Flatpak application layer"},
            ],
        },
        "components": components,
        "dependencies": [
            {"ref": application_ref, "dependsOn": [component["bom-ref"] for component in components]}
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--timestamp", required=True, help="ISO-8601 commit timestamp")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        dt.datetime.fromisoformat(args.timestamp.replace("Z", "+00:00"))
    except ValueError as error:
        raise SystemExit("--timestamp must be ISO-8601") from error
    payload = build_sbom(args.version, args.commit, args.timestamp)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
