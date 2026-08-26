"""Opt-in transcript history with bounded retention and explicit deletion."""

from __future__ import annotations

import datetime as dt
import json
import os
import tempfile
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable, Optional

SCHEMA_VERSION = 1


@dataclass(frozen=True)
class HistoryEntry:
    id: str
    created_at: str
    text: str


class HistoryStore:
    """Store transcript text only; callers decide whether history is enabled."""

    def __init__(
        self,
        data_dir: Optional[Path] = None,
        *,
        now: Callable[[], dt.datetime] = lambda: dt.datetime.now(dt.timezone.utc),
    ) -> None:
        root = data_dir or self._default_data_dir()
        self._directory = root
        self._path = root / "history.json"
        self._now = now

    @property
    def path(self) -> Path:
        return self._path

    @staticmethod
    def _default_data_dir() -> Path:
        configured = os.environ.get("XDG_DATA_HOME", "").strip()
        base = Path(configured) if configured else Path.home() / ".local" / "share"
        return base / "voice-transcriber"

    def add(self, text: str, *, retention_days: int) -> HistoryEntry:
        clean_text = text.strip()
        if not clean_text:
            raise ValueError("history text must not be empty")
        self._validate_retention(retention_days)
        entries = self._pruned(self._read(), retention_days)
        if entries and entries[-1].text == clean_text:
            self._write(entries)
            return entries[-1]
        created = self._now().astimezone(dt.timezone.utc)
        entry = HistoryEntry(
            id=str(uuid.uuid4()),
            created_at=created.isoformat().replace("+00:00", "Z"),
            text=clean_text,
        )
        entries.append(entry)
        self._write(entries)
        return entry

    def list(self, *, retention_days: int) -> list[HistoryEntry]:
        self._validate_retention(retention_days)
        loaded = self._read()
        entries = self._pruned(loaded, retention_days)
        if entries != loaded:
            self._write(entries)
        return list(reversed(entries))

    def delete(self, entry_id: str) -> bool:
        entries = self._read()
        remaining = [entry for entry in entries if entry.id != entry_id]
        if len(remaining) == len(entries):
            return False
        self._write(remaining)
        return True

    def clear(self) -> None:
        if self._path.exists():
            self._path.unlink()
        try:
            self._directory.rmdir()
        except OSError:
            pass

    @staticmethod
    def _validate_retention(retention_days: int) -> None:
        if isinstance(retention_days, bool) or not isinstance(retention_days, int):
            raise ValueError("retention_days must be an integer")
        if not 1 <= retention_days <= 365:
            raise ValueError("retention_days must be between 1 and 365")

    def _pruned(self, entries: list[HistoryEntry], retention_days: int) -> list[HistoryEntry]:
        threshold = self._now().astimezone(dt.timezone.utc) - dt.timedelta(days=retention_days)
        kept = []
        for entry in entries:
            try:
                created = dt.datetime.fromisoformat(entry.created_at.replace("Z", "+00:00"))
            except ValueError:
                continue
            if created.astimezone(dt.timezone.utc) >= threshold:
                kept.append(entry)
        return kept

    def _read(self) -> list[HistoryEntry]:
        if not self._path.exists():
            return []
        try:
            payload = json.loads(self._path.read_text(encoding="utf-8"))
            if payload.get("schema_version") != SCHEMA_VERSION:
                raise ValueError("unsupported history schema; refusing to overwrite it")
            if not isinstance(payload.get("entries"), list):
                return []
            entries = []
            for item in payload["entries"]:
                if not isinstance(item, dict):
                    continue
                entry = HistoryEntry(
                    id=str(item.get("id", "")),
                    created_at=str(item.get("created_at", "")),
                    text=str(item.get("text", "")).strip(),
                )
                if entry.id and entry.created_at and entry.text:
                    entries.append(entry)
            return entries
        except (OSError, json.JSONDecodeError, AttributeError):
            return []

    def _write(self, entries: list[HistoryEntry]) -> None:
        self._directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(self._directory, 0o700)
        descriptor, temp_name = tempfile.mkstemp(
            prefix=".history-", suffix=".json", dir=self._directory, text=True
        )
        temp_path = Path(temp_name)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as output:
                json.dump(
                    {"schema_version": SCHEMA_VERSION, "entries": [asdict(entry) for entry in entries]},
                    output,
                    indent=2,
                    sort_keys=True,
                )
                output.write("\n")
                output.flush()
                os.fsync(output.fileno())
            os.chmod(temp_path, 0o600)
            os.replace(temp_path, self._path)
        finally:
            temp_path.unlink(missing_ok=True)
