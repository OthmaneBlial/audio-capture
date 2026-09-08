"""Structured, owner-only transcript exports."""

from __future__ import annotations

import datetime as dt
import os
import tempfile
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
    """Atomically write only the selected file with owner read/write permissions."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.is_symlink():
        raise OSError(f"Refusing to overwrite symbolic link: {destination}")
    descriptor: Optional[int] = None
    temp_path: Optional[Path] = None
    try:
        descriptor, temp_name = tempfile.mkstemp(
            prefix=f".{destination.name}-", suffix=".tmp", dir=destination.parent, text=True
        )
        temp_path = Path(temp_name)
        with os.fdopen(descriptor, "w", encoding="utf-8") as output:
            descriptor = None
            output.write(document.content)
            output.flush()
            os.fsync(output.fileno())
        os.chmod(temp_path, 0o600)
        os.replace(temp_path, destination)
    finally:
        if descriptor is not None:
            try:
                os.close(descriptor)
            except OSError:
                pass
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)
