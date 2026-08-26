"""Audio capture and voice activity detection primitives."""

from typing import Any

__all__ = ["AudioCapture", "VoiceActivityDetector"]


def __getattr__(name: str) -> Any:
    """Load native dependencies only when that capability is actually used."""
    if name == "AudioCapture":
        from .capture import AudioCapture

        return AudioCapture
    if name == "VoiceActivityDetector":
        from .vad import VoiceActivityDetector

        return VoiceActivityDetector
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
