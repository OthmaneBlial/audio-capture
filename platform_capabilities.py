"""Honest desktop capability detection for optional dictation conveniences."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Optional


@dataclass(frozen=True)
class DesktopCapabilities:
    session_type: str
    sandboxed: bool
    focused_push_to_talk: bool
    tray_window_toggle: bool
    global_shortcut: bool
    explanation: str


def detect_desktop_capabilities(
    environ: Optional[Mapping[str, str]] = None,
    *,
    flatpak_info: Path = Path("/.flatpak-info"),
) -> DesktopCapabilities:
    values = environ if environ is not None else os.environ
    session = values.get("XDG_SESSION_TYPE", "").strip().lower() or "unknown"
    sandboxed = flatpak_info.exists()
    tray = session == "x11" and not sandboxed
    if session == "wayland":
        explanation = (
            "Focused push-to-talk works. This build does not register a global shortcut or legacy tray icon on Wayland."
        )
    elif tray:
        explanation = (
            "Focused push-to-talk and the legacy X11 tray window toggle are available. Global shortcuts are not registered."
        )
    else:
        explanation = (
            "Focused push-to-talk works. The desktop session does not expose a reliable tray or global-shortcut capability."
        )
    return DesktopCapabilities(
        session_type=session,
        sandboxed=sandboxed,
        focused_push_to_talk=True,
        tray_window_toggle=tray,
        global_shortcut=False,
        explanation=explanation,
    )
