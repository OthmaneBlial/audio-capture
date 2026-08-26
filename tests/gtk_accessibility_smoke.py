#!/usr/bin/env python3
"""Manual/CI GTK smoke for first-run focusable controls and explicit boundary copy."""

from __future__ import annotations

import tempfile
from dataclasses import dataclass
from pathlib import Path

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import GLib, Gtk

from config import ConfigManager
from ui.main_window import MainWindow


@dataclass
class FakeDevice:
    index: int = 4
    name: str = "Test microphone"
    is_default: bool = True


def descendants(widget: Gtk.Widget) -> list[Gtk.Widget]:
    found = [widget]
    if isinstance(widget, Gtk.Container):
        for child in widget.get_children():
            found.extend(descendants(child))
    return found


def main() -> int:
    with tempfile.TemporaryDirectory() as directory:
        config = ConfigManager(Path(directory), environ={})
        window = MainWindow(
            config,
            on_start=lambda: False,
            on_stop=lambda: None,
            on_settings_change=lambda: None,
            on_list_input_devices=lambda: [FakeDevice()],
        )
        window.show_all()
        failures: list[str] = []

        def inspect_dialog() -> bool:
            dialogs = [
                candidate
                for candidate in Gtk.Window.list_toplevels()
                if isinstance(candidate, Gtk.Dialog)
                and candidate.get_title() == "Set up Voice Transcriber"
            ]
            if len(dialogs) != 1:
                failures.append(f"expected one first-run dialog, found {len(dialogs)}")
            else:
                dialog = dialogs[0]
                widgets = descendants(dialog)
                visible_text = " ".join(
                    widget.get_text()
                    for widget in widgets
                    if isinstance(widget, Gtk.Label) and widget.get_visible()
                )
                for required_copy in (
                    "Know the boundary before you speak",
                    "Provider · Groq cloud",
                    "completed speech segments",
                    "Local: silence detection",
                ):
                    if required_copy not in visible_text:
                        failures.append(f"missing first-run copy: {required_copy}")

                interactive_types = (Gtk.Button, Gtk.Entry, Gtk.ComboBox, Gtk.CheckButton)
                unnamed = []
                for widget in widgets:
                    if not isinstance(widget, interactive_types) or not widget.get_visible():
                        continue
                    accessible_name = widget.get_accessible().get_name()
                    fallback_label = widget.get_label() if isinstance(widget, Gtk.Button) else None
                    if not (accessible_name or fallback_label):
                        unnamed.append(type(widget).__name__)
                if unnamed:
                    failures.append(f"unnamed interactive controls: {unnamed}")

                entries = [widget for widget in widgets if isinstance(widget, Gtk.Entry)]
                checks = [widget for widget in widgets if isinstance(widget, Gtk.CheckButton)]
                combos = [widget for widget in widgets if isinstance(widget, Gtk.ComboBox)]
                if len(entries) != 1 or len(checks) != 1 or len(combos) != 2:
                    failures.append(
                        f"unexpected setup controls: entries={len(entries)} checks={len(checks)} combos={len(combos)}"
                    )
                dialog.response(Gtk.ResponseType.CANCEL)
            GLib.timeout_add(80, inspect_main_desk)
            return False

        def inspect_main_desk() -> bool:
            widgets = descendants(window)
            text_views = [widget for widget in widgets if isinstance(widget, Gtk.TextView)]
            if len(text_views) != 1 or not text_views[0].get_editable():
                failures.append("main transcript must be one editable text view")
            button_labels = {
                widget.get_label()
                for widget in widgets
                if isinstance(widget, Gtk.Button) and widget.get_visible()
            }
            for label in (
                "History",
                "Export",
                "Settings",
                "Start listening",
                "Undo",
                "Redo",
                "Clear",
                "Copy",
            ):
                if label not in button_labels:
                    failures.append(f"missing daily-dictation button: {label}")
            window.update_segment_state("gtk-smoke", "pending", "Waiting for provider")
            GLib.timeout_add(80, inspect_segment_state)
            return False

        def inspect_segment_state() -> bool:
            visible_text = " ".join(
                widget.get_text()
                for widget in descendants(window)
                if isinstance(widget, Gtk.Label) and widget.get_visible()
            )
            if "Segment 1 · Waiting for provider" not in visible_text:
                failures.append("pending segment state is not visible")
            settings_buttons = [
                widget
                for widget in descendants(window)
                if isinstance(widget, Gtk.Button) and widget.get_label() == "Settings"
            ]
            if settings_buttons:
                settings_buttons[0].clicked()
                GLib.timeout_add(100, inspect_settings)
            else:
                failures.append("could not open Settings for daily-dictation smoke")
                GLib.timeout_add(20, stop)
            return False

        def inspect_settings() -> bool:
            widgets = descendants(window._popover)
            names = {
                widget.get_accessible().get_name()
                for widget in widgets
                if widget.get_accessible().get_name()
            }
            for required_name in (
                "Capture control mode",
                "Copy transcript after each final segment",
                "Keep local transcript history",
                "History retention days",
            ):
                if required_name not in names:
                    failures.append(f"missing accessible Settings control: {required_name}")
            window._popover.popdown()
            GLib.timeout_add(20, stop)
            return False

        def stop() -> bool:
            window.destroy()
            Gtk.main_quit()
            return False

        GLib.timeout_add(250, inspect_dialog)
        Gtk.main()
        if failures:
            raise AssertionError("; ".join(failures))
        print("GTK first-run boundary and accessibility smoke test passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
