"""Structured, owner-only transcript exports."""

from __future__ import annotations

import datetime as dt
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Optional

ExportFormat = Literal["text", "markdown", "timestamped"]


@dataclass(frozen=True)
class ExportDocument:
    format: ExportFormat
    extension: str
    suggested_name: str
    content: str


def build_export(
    text: str,
    export_format: ExportFormat,
    *,
    created_at: Optional[dt.datetime] = None,
) -> ExportDocument:
    clean_text = text.strip()
    if not clean_text:
        raise ValueError("transcript must not be empty")
    if export_format not in {"text", "markdown", "timestamped"}:
        raise ValueError(f"unsupported export format: {export_format}")
    moment = created_at or dt.datetime.now().astimezone()
    stamp = moment.strftime("%Y-%m-%d_%H-%M")
    if export_format == "markdown":
        return ExportDocument(
            export_format,
            ".md",
            f"transcript_{stamp}.md",
            f"# Voice transcript\n\n{clean_text}\n",
        )
    if export_format == "timestamped":
        visible_stamp = moment.strftime("%Y-%m-%d %H:%M:%S %Z").strip()
        return ExportDocument(
            export_format,
            ".txt",
            f"transcript_{stamp}_timestamped.txt",
            f"[{visible_stamp}] {clean_text}\n",
        )
    return ExportDocument(export_format, ".txt", f"transcript_{stamp}.txt", clean_text + "\n")


def write_export(destination: Path, document: ExportDocument) -> None:
    """Write only the selected file with owner read/write permissions."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as output:
            output.write(document.content)
            output.flush()
            os.fsync(output.fileno())
    except Exception:
        try:
            os.close(descriptor)
        except OSError:
            pass
        raise
    os.chmod(destination, 0o600)
