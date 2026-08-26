#!/usr/bin/env python3
"""Verify LibriSpeech test-clean and create a deterministic benchmark manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import tarfile
from pathlib import Path

ARCHIVE_MD5 = "32fa31d27d2e1cad72775fee3f4849a9"
ARCHIVE_URL = "https://openslr.org/resources/12/test-clean.tar.gz"
LICENSE = "CC BY 4.0"


def file_md5(path: Path) -> str:
    digest = hashlib.md5(usedforsecurity=False)
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_extract(archive: Path, destination: Path) -> None:
    """Extract only regular files/directories that remain under destination."""
    destination.mkdir(parents=True, exist_ok=True)
    root = destination.resolve()
    with tarfile.open(archive, "r:gz") as bundle:
        for member in bundle.getmembers():
            target = (destination / member.name).resolve()
            if root not in target.parents and target != root:
                raise ValueError(f"Archive member escapes destination: {member.name}")
            if member.issym() or member.islnk() or member.isdev():
                raise ValueError(f"Archive member type is not allowed: {member.name}")
        bundle.extractall(destination)


def collect_entries(root: Path) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    for transcript_path in sorted(root.rglob("*.trans.txt")):
        for line in transcript_path.read_text(encoding="utf-8").splitlines():
            sample_id, reference = line.split(" ", 1)
            audio_path = transcript_path.parent / f"{sample_id}.flac"
            if not audio_path.is_file():
                raise FileNotFoundError(f"Missing audio for {sample_id}")
            speaker, chapter, _utterance = sample_id.split("-", 2)
            entries.append(
                {
                    "id": sample_id,
                    "speaker": speaker,
                    "chapter": chapter,
                    "audio": str(audio_path.resolve()),
                    "reference": reference,
                }
            )
    if not entries:
        raise ValueError("No LibriSpeech transcript entries were found")
    return entries


def deterministic_sample(entries: list[dict[str, str]], count: int) -> list[dict[str, str]]:
    """Select a stable speaker-diverse slice without random state."""
    if count < 1 or count > len(entries):
        raise ValueError("sample count must be between 1 and the corpus size")
    by_speaker: dict[str, list[dict[str, str]]] = {}
    for entry in sorted(entries, key=lambda item: item["id"]):
        by_speaker.setdefault(entry["speaker"], []).append(entry)
    speakers = sorted(by_speaker)
    selected: list[dict[str, str]] = []
    round_index = 0
    while len(selected) < count:
        made_progress = False
        for speaker in speakers:
            samples = by_speaker[speaker]
            if round_index < len(samples):
                selected.append(samples[round_index])
                made_progress = True
                if len(selected) == count:
                    break
        if not made_progress:
            break
        round_index += 1
    return selected


def prepare(archive: Path, output_dir: Path, count: int) -> Path:
    checksum = file_md5(archive)
    if checksum != ARCHIVE_MD5:
        raise ValueError(f"test-clean checksum mismatch: expected {ARCHIVE_MD5}, got {checksum}")
    extracted = output_dir / "extracted"
    if extracted.exists():
        shutil.rmtree(extracted)
    safe_extract(archive, extracted)
    entries = deterministic_sample(collect_entries(extracted / "LibriSpeech" / "test-clean"), count)
    manifest = {
        "schema_version": 1,
        "corpus": "LibriSpeech test-clean",
        "source": ARCHIVE_URL,
        "archive_md5": ARCHIVE_MD5,
        "license": LICENSE,
        "selection": "sorted speakers, one sorted utterance per speaker per round",
        "samples": entries,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True, help="Downloaded test-clean.tar.gz")
    parser.add_argument("--output-dir", type=Path, required=True, help="External working directory")
    parser.add_argument("--sample-count", type=int, default=25)
    args = parser.parse_args()
    manifest = prepare(args.archive, args.output_dir, args.sample_count)
    print(manifest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

