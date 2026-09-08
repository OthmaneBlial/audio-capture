"""Pure transcript state used by the GTK desk and unit tests."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Literal, Optional

SegmentState = Literal["pending", "complete", "error"]


@dataclass(frozen=True)
class SegmentStatus:
    """One bounded, user-visible transcription request state."""

    request_id: str
    ordinal: int
    state: SegmentState
    detail: str


class SegmentTracker:
    """Track recent request states without retaining audio or transcript content."""

    def __init__(self, *, max_visible: int = 4) -> None:
        if max_visible < 1:
            raise ValueError("max_visible must be positive")
        self._max_visible = max_visible
        self._ordinals: dict[str, int] = {}
        self._states: dict[str, SegmentStatus] = {}
        self._order: deque[str] = deque()
        self._next_ordinal = 1

    def update(
        self,
        request_id: str,
        state: SegmentState,
        detail: Optional[str] = None,
    ) -> SegmentStatus:
        if not request_id.strip():
            raise ValueError("request_id must not be empty")
        if state not in {"pending", "complete", "error"}:
            raise ValueError(f"unsupported segment state: {state}")
        if request_id not in self._ordinals:
            self._ordinals[request_id] = self._next_ordinal
            self._next_ordinal += 1
            self._order.append(request_id)
            self._evict_oldest()
        safe_detail = (detail or self._default_detail(state)).strip()
        status = SegmentStatus(request_id, self._ordinals[request_id], state, safe_detail)
        self._states[request_id] = status
        return status

    def visible(self) -> list[SegmentStatus]:
        return [self._states[item] for item in self._order if item in self._states]

    def clear(self) -> None:
        """Discard visible request states when their session generation ends."""
        self._ordinals.clear()
        self._states.clear()
        self._order.clear()

    @property
    def retained_count(self) -> int:
        """Return the number of request states retained for the recent strip."""
        return len(self._states)

    def _evict_oldest(self) -> None:
        while len(self._order) > self._max_visible:
            expired = self._order.popleft()
            self._ordinals.pop(expired, None)
            self._states.pop(expired, None)

    @staticmethod
    def _default_detail(state: SegmentState) -> str:
        return {
            "pending": "Waiting for transcription",
            "complete": "Added to transcript",
            "error": "Transcription failed",
        }[state]


class UndoHistory:
    """Bounded text snapshots for GTK3, which has no built-in TextView undo."""

    def __init__(self, *, limit: int = 100) -> None:
        if limit < 1:
            raise ValueError("limit must be positive")
        self._limit = limit
        self._undo: list[str] = []
        self._redo: list[str] = []

    @property
    def can_undo(self) -> bool:
        return bool(self._undo)

    @property
    def can_redo(self) -> bool:
        return bool(self._redo)

    def remember(self, text: str) -> None:
        if self._undo and self._undo[-1] == text:
            return
        self._undo.append(text)
        del self._undo[:-self._limit]
        self._redo.clear()

    def clear(self) -> None:
        """Discard every in-memory snapshot after a destructive clear."""
        self._undo.clear()
        self._redo.clear()

    def undo(self, current: str) -> str:
        if not self._undo:
            return current
        previous = self._undo.pop()
        self._redo.append(current)
        return previous

    def redo(self, current: str) -> str:
        if not self._redo:
            return current
        following = self._redo.pop()
        self._undo.append(current)
        return following
