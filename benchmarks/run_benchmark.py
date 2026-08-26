#!/usr/bin/env python3
"""Run a Voice Transcriber provider against a prepared licensed corpus."""

from __future__ import annotations

import argparse
import json
import os
import platform
import re
import subprocess
import time
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from transcription import GroqTranscriptionService
from transcription.local_whisper import EXPERIMENTAL_FLAG, LocalWhisperTranscriptionService


def normalize_words(text: str) -> list[str]:
    normalized = unicodedata.normalize("NFKC", text).casefold()
    normalized = re.sub(r"[^\w']+", " ", normalized, flags=re.UNICODE)
    return normalized.split()


def word_error_counts(reference: str, hypothesis: str) -> tuple[int, int]:
    expected = normalize_words(reference)
    actual = normalize_words(hypothesis)
    previous = list(range(len(actual) + 1))
    for row, expected_word in enumerate(expected, start=1):
        current = [row]
        for column, actual_word in enumerate(actual, start=1):
            current.append(
                min(
                    current[column - 1] + 1,
                    previous[column] + 1,
                    previous[column - 1] + (expected_word != actual_word),
                )
            )
        previous = current
    return previous[-1], len(expected)


def percentile(values: list[float], quantile: float) -> float:
    if not values:
        raise ValueError("percentile requires at least one value")
    ordered = sorted(values)
    index = (len(ordered) - 1) * quantile
    lower = int(index)
    upper = min(lower + 1, len(ordered) - 1)
    weight = index - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def decode_flac(path: Path, ffmpeg: str) -> bytes:
    completed = subprocess.run(
        [ffmpeg, "-v", "error", "-i", str(path), "-f", "s16le", "-ac", "1", "-ar", "16000", "-"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if not completed.stdout:
        raise RuntimeError(f"ffmpeg decoded no audio for {path}")
    return completed.stdout


def build_provider(args: argparse.Namespace, errors: list[str]):
    common = {
        "sample_rate": 16000,
        "language": args.language,
        "on_error": lambda error: errors.append(str(error)),
    }
    if args.provider == "groq":
        return GroqTranscriptionService(api_key=os.environ.get("GROQ_API_KEY", ""), **common)
    return LocalWhisperTranscriptionService(
        binary_path=args.local_binary,
        model_path=args.local_model,
        environ={EXPERIMENTAL_FLAG: "1"},
        **common,
    )


def run(
    manifest_path: Path,
    output_path: Path,
    provider: Any,
    *,
    provider_model: str,
    hardware_label: str,
    ffmpeg: str,
    decoder: Callable[[Path, str], bytes] = decode_flac,
) -> dict[str, Any]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema_version") != 1 or not manifest.get("samples"):
        raise ValueError("Unsupported or empty benchmark manifest")
    if not provider.configured:
        raise ValueError(f"Provider {provider.provider_id} is not configured")
    rows = []
    total_errors = 0
    total_reference_words = 0
    latencies = []
    for sample in manifest["samples"]:
        audio = decoder(Path(sample["audio"]), ffmpeg)
        started = time.perf_counter()
        hypothesis = provider.transcribe(audio) or ""
        latency_ms = (time.perf_counter() - started) * 1000
        errors, reference_words = word_error_counts(sample["reference"], hypothesis)
        total_errors += errors
        total_reference_words += reference_words
        latencies.append(latency_ms)
        rows.append(
            {
                "id": sample["id"],
                "speaker": sample["speaker"],
                "reference_words": reference_words,
                "word_errors": errors,
                "wer": errors / reference_words if reference_words else 0.0,
                "latency_ms": round(latency_ms, 3),
                "hypothesis": hypothesis,
            }
        )
    receipt = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "provider": provider.provider_id,
        "provider_model": provider_model,
        "provider_boundary": provider.boundary.audio_destination,
        "hardware_label": hardware_label,
        "runtime": {"system": platform.platform(), "python": platform.python_version()},
        "corpus": {
            "name": manifest["corpus"],
            "source": manifest["source"],
            "license": manifest["license"],
            "archive_md5": manifest["archive_md5"],
            "sample_count": len(rows),
            "speaker_count": len({row["speaker"] for row in rows}),
            "selection": manifest["selection"],
        },
        "summary": {
            "wer": total_errors / total_reference_words if total_reference_words else 0.0,
            "word_errors": total_errors,
            "reference_words": total_reference_words,
            "latency_ms_p50": round(percentile(latencies, 0.50), 3),
            "latency_ms_p95": round(percentile(latencies, 0.95), 3),
        },
        "samples": rows,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--provider", choices=("groq", "local_whisper_cpp"), required=True)
    parser.add_argument("--provider-model", required=True, help="Exact model identifier or checksum")
    parser.add_argument("--hardware-label", required=True, help="Publishable CPU/RAM description")
    parser.add_argument("--language", default="en")
    parser.add_argument("--ffmpeg", default="ffmpeg")
    parser.add_argument("--local-binary", default="")
    parser.add_argument("--local-model", default="")
    args = parser.parse_args()
    errors: list[str] = []
    service = build_provider(args, errors)
    try:
        run(
            args.manifest,
            args.output,
            service,
            provider_model=args.provider_model,
            hardware_label=args.hardware_label,
            ffmpeg=args.ffmpeg,
        )
    finally:
        service.close(wait=True)
    if errors:
        raise RuntimeError(f"Provider reported {len(errors)} error(s); first: {errors[0]}")
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

