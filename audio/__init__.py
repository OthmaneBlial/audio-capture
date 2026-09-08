"""Audio capture and voice activity detection primitives."""

from typing import Any

__all__ = [
    "AudioCapture",
    "DeviceIdentityMismatch",
    "InputDevice",
    "VoiceActivityDetector",
    "device_identity",
    "list_input_devices",
]


def __getattr__(name: str) -> Any:
    """Load native dependencies only when that capability is actually used."""
    if name == "AudioCapture":
        from .capture import AudioCapture

        return AudioCapture
    if name in {"DeviceIdentityMismatch", "InputDevice", "device_identity", "list_input_devices"}:
        from .capture import (
            DeviceIdentityMismatch,
            InputDevice,
            device_identity,
            list_input_devices,
        )

        return {
            "DeviceIdentityMismatch": DeviceIdentityMismatch,
            "InputDevice": InputDevice,
            "device_identity": device_identity,
            "list_input_devices": list_input_devices,
        }[name]
    if name == "VoiceActivityDetector":
        from .vad import VoiceActivityDetector

        return VoiceActivityDetector
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
