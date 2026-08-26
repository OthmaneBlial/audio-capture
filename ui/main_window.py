"""GTK3 window for a focused, privacy-explicit transcription session."""

from __future__ import annotations

import datetime as dt
import logging
import os
import sys
from pathlib import Path
from typing import Callable, Optional

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gdk, GLib, Gtk

from config import ConfigError, ConfigManager

LOGGER = logging.getLogger(__name__)


class MainWindow(Gtk.Window):
    """A compact recording desk: record, review, copy, and export."""

    def __init__(
        self,
        config: ConfigManager,
        on_start: Optional[Callable[[], bool]] = None,
        on_stop: Optional[Callable[[], None]] = None,
        on_settings_change: Optional[Callable[[], None]] = None,
    ) -> None:
        super().__init__(title="Voice Transcriber")
        self._config = config
        self._on_start = on_start
        self._on_stop = on_stop
        self._on_settings_change_cb = on_settings_change
        self._is_listening = False
        self._status_reset_source: Optional[int] = None
        self._geometry_save_source: Optional[int] = None
        self._pending_geometry: Optional[tuple[int, int]] = None

        self._setup_window()
        self._apply_styles()
        self._setup_ui()
        self._load_initial_settings()

    def _setup_window(self) -> None:
        self.set_default_size(self._config.get("window_width"), self._config.get("window_height"))
        self.set_size_request(360, 320)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_resizable(True)
        self.set_wmclass("voice-transcriber", "Voice Transcriber")
        self.set_role("voice-transcriber")
        self.connect("destroy", Gtk.main_quit)
        self.connect("configure-event", self._on_window_configure)
        try:
            base_path = getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1])
            icon_path = Path(base_path) / "resources" / "icon.svg"
            if icon_path.exists():
                self.set_icon_from_file(str(icon_path))
        except Exception:
            LOGGER.debug("Could not set application icon", exc_info=True)

    def _apply_styles(self) -> None:
        """Use a high-contrast recording-desk visual language, not a generic dashboard."""
        css = b"""
        window { background-color: #101512; color: #F3F7EE; }
        .topbar { background-color: #171D19; border-bottom: 1px solid #334038; padding: 14px 18px; }
        .wordmark { color: #F7FAF2; font-family: Cantarell, sans-serif; font-size: 18px; font-weight: 800; }
        .top-action { background-image: none; background-color: transparent; border: 1px solid transparent; color: #D8E5D2; padding: 7px 10px; border-radius: 7px; box-shadow: none; }
        .top-action:hover, .top-action:focus { background-color: #29352D; border-color: #425247; }
        .content { padding: 22px 24px 20px 24px; }
        .eyebrow { color: #B8E85A; font-family: Cantarell, sans-serif; font-size: 11px; font-weight: 800; letter-spacing: 0.08em; }
        .privacy-note { color: #AAB8AA; font-size: 12px; }
        .record-button { background-image: none; background-color: #B8E85A; border: 1px solid #D7FF8A; color: #16200E; padding: 14px 24px; border-radius: 9px; font-size: 15px; font-weight: 800; box-shadow: none; }
        .record-button:hover, .record-button:focus { background-color: #D0FA78; }
        .record-button.recording { background-color: #EE7C58; border-color: #FFB099; color: #28100A; }
        .record-button.recording:hover, .record-button.recording:focus { background-color: #FF9270; }
        .status-chip { background-color: #1D2821; border: 1px solid #344338; border-radius: 16px; padding: 7px 12px; }
        .status { color: #B4C6B4; font-size: 12px; font-weight: 700; }
        .status.active { color: #C9F57A; }
        .status.error { color: #FFAA8E; }
        .transcript-shell { background-color: #141B17; border: 1px solid #344338; border-radius: 10px; margin-top: 14px; }
        .transcript-view { background-color: transparent; color: #F4F7F0; font-family: Serif; font-size: 17px; line-height: 1.45; padding: 16px; }
        .empty-title { color: #EDF4E7; font-size: 17px; font-weight: 800; }
        .empty-copy { color: #9DAE9F; font-size: 13px; }
        .bottom-rule { border-top: 1px solid #2B382F; padding-top: 14px; }
        .secondary-button { background-image: none; background-color: #253128; border: 1px solid #405044; color: #E5EDE1; padding: 8px 12px; border-radius: 7px; font-weight: 700; box-shadow: none; }
        .secondary-button:hover, .secondary-button:focus { background-color: #334138; border-color: #617264; }
        .danger-button { color: #FFB19B; }
        .settings-box { background-color: #1A211C; color: #F4F7F0; border: 1px solid #405044; border-radius: 9px; padding: 12px; }
        .settings-title { color: #F4F7F0; font-size: 15px; font-weight: 800; }
        .settings-label { color: #C5D1C4; font-size: 12px; font-weight: 700; }
        .settings-help { color: #9DAE9F; font-size: 11px; }
        entry, combobox { background-color: #101512; border: 1px solid #46594B; color: #F4F7F0; border-radius: 6px; padding: 6px; }
        entry:focus, combobox:focus { border-color: #B8E85A; }
        switch slider { background-color: #DCE9D7; }
        switch:checked { background-color: #8FBC3E; }
        """
        provider = Gtk.CssProvider()
        provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    @staticmethod
    def _label(text: str, style_class: str, *, xalign: float = 0.0) -> Gtk.Label:
        label = Gtk.Label(label=text, xalign=xalign)
        label.get_style_context().add_class(style_class)
        label.set_line_wrap(True)
        return label

    def _setup_ui(self) -> None:
        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.add(root)

        topbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        topbar.get_style_context().add_class("topbar")
        root.pack_start(topbar, False, False, 0)
        brand = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
        brand.pack_start(self._label("VOICE TRANSCRIBER", "wordmark"), False, False, 0)
        brand.pack_start(self._label("speech, without the busywork", "privacy-note"), False, False, 0)
        topbar.pack_start(brand, True, True, 0)
        self._save_button = self._make_top_button("Export", "Save the transcript as a UTF-8 text file", self._on_save_clicked)
        topbar.pack_end(self._save_button, False, False, 0)
        settings_button = self._make_top_button("Settings", "Configure Groq and transcription preferences", self._on_settings_clicked)
        topbar.pack_end(settings_button, False, False, 0)

        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        content.get_style_context().add_class("content")
        root.pack_start(content, True, True, 0)
        content.pack_start(self._label("LIVE SESSION", "eyebrow"), False, False, 0)

        self._listen_button = Gtk.Button(label="Start listening")
        self._listen_button.get_style_context().add_class("record-button")
        self._listen_button.set_tooltip_text("Start or stop microphone capture (Ctrl+Enter)")
        self._listen_button.get_accessible().set_name("Start listening")
        self._listen_button.connect("clicked", self._on_listen_clicked)
        content.pack_start(self._listen_button, False, False, 0)

        status_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        status_box.get_style_context().add_class("status-chip")
        status_box.set_halign(Gtk.Align.START)
        self._status_label = self._label("Ready when you are", "status")
        self._status_label.get_accessible().set_name("Transcription status")
        status_box.pack_start(self._status_label, False, False, 0)
        content.pack_start(status_box, False, False, 0)

        content.pack_start(
            self._label("Audio stays in memory until a detected speech segment is sent to Groq for transcription.", "privacy-note"),
            False,
            False,
            0,
        )

        frame = Gtk.Frame()
        frame.set_shadow_type(Gtk.ShadowType.NONE)
        frame.get_style_context().add_class("transcript-shell")
        content.pack_start(frame, True, True, 0)
        overlay = Gtk.Overlay()
        frame.add(overlay)
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        overlay.add(scrolled)
        self._text_view = Gtk.TextView()
        self._text_view.get_style_context().add_class("transcript-view")
        self._text_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self._text_view.set_editable(False)
        self._text_view.set_cursor_visible(False)
        self._text_view.set_accessible_name("Current transcript")
        self._text_buffer = self._text_view.get_buffer()
        self._text_buffer.connect("changed", self._on_transcript_changed)
        scrolled.add(self._text_view)
        self._empty_state = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self._empty_state.set_halign(Gtk.Align.CENTER)
        self._empty_state.set_valign(Gtk.Align.CENTER)
        self._empty_state.pack_start(self._label("Your words will land here", "empty-title", xalign=0.5), False, False, 0)
        self._empty_state.pack_start(
            self._label("Start a session, speak naturally, then copy or export the result.", "empty-copy", xalign=0.5),
            False,
            False,
            0,
        )
        overlay.add_overlay(self._empty_state)

        actions = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        actions.get_style_context().add_class("bottom-rule")
        sticky_label = self._label("Keep on top", "settings-label")
        actions.pack_start(sticky_label, False, False, 0)
        self._sticky_switch = Gtk.Switch()
        self._sticky_switch.set_active(self._config.get("sticky_mode"))
        self._sticky_switch.set_tooltip_text("Keep Voice Transcriber above other windows")
        self._sticky_switch.connect("state-set", self._on_sticky_toggled)
        actions.pack_start(self._sticky_switch, False, False, 0)
        actions.pack_start(Gtk.Box(), True, True, 0)
        copy_button = self._make_secondary_button("Copy", "Copy transcript to clipboard (Ctrl+Shift+C)", self._on_copy_clicked)
        actions.pack_end(copy_button, False, False, 0)
        clear_button = self._make_secondary_button("Clear", "Remove the current transcript", self._on_clear_clicked)
        clear_button.get_style_context().add_class("danger-button")
        actions.pack_end(clear_button, False, False, 0)
        content.pack_end(actions, False, False, 0)

        self._init_settings_popover(settings_button)
        self._install_shortcuts(copy_button, settings_button)

    def _make_top_button(self, label: str, tooltip: str, callback: Callable[..., None]) -> Gtk.Button:
        button = Gtk.Button(label=label)
        button.get_style_context().add_class("top-action")
        button.set_tooltip_text(tooltip)
        button.connect("clicked", callback)
        return button

    def _make_secondary_button(self, label: str, tooltip: str, callback: Callable[..., None]) -> Gtk.Button:
        button = Gtk.Button(label=label)
        button.get_style_context().add_class("secondary-button")
        button.set_tooltip_text(tooltip)
        button.connect("clicked", callback)
        return button

    def _install_shortcuts(self, copy_button: Gtk.Button, settings_button: Gtk.Button) -> None:
        accel_group = Gtk.AccelGroup()
        self.add_accel_group(accel_group)
        self._listen_button.add_accelerator("clicked", accel_group, Gdk.KEY_Return, Gdk.ModifierType.CONTROL_MASK, Gtk.AccelFlags.VISIBLE)
        copy_button.add_accelerator(
            "clicked", accel_group, Gdk.KEY_C, Gdk.ModifierType.CONTROL_MASK | Gdk.ModifierType.SHIFT_MASK, Gtk.AccelFlags.VISIBLE
        )
        settings_button.add_accelerator("clicked", accel_group, Gdk.KEY_comma, Gdk.ModifierType.CONTROL_MASK, Gtk.AccelFlags.VISIBLE)

    def _init_settings_popover(self, parent_button: Gtk.Button) -> None:
        self._popover = Gtk.Popover.new(parent_button)
        self._popover.set_position(Gtk.PositionType.BOTTOM)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.get_style_context().add_class("settings-box")
        box.set_margin_top(8)
        box.set_margin_bottom(8)
        box.set_margin_start(8)
        box.set_margin_end(8)
        self._popover.add(box)
        box.pack_start(self._label("Session settings", "settings-title"), False, False, 0)

        api_row = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        api_row.pack_start(self._label("Groq API key", "settings-label"), False, False, 0)
        self._api_entry = Gtk.Entry()
        self._api_entry.set_visibility(False)
        self._api_entry.set_invisible_char("•")
        self._api_entry.set_width_chars(29)
        self._api_entry.set_placeholder_text("gsk_…")
        self._api_entry.set_text(self._config.saved_value("api_key") or "")
        api_row.pack_start(self._api_entry, False, False, 0)
        if self._config.source_for("api_key") == "environment":
            self._api_entry.set_text("")
            self._api_entry.set_placeholder_text("Set by GROQ_API_KEY")
            self._api_entry.set_sensitive(False)
            api_row.pack_start(
                self._label("GROQ_API_KEY is active and overrides the saved value.", "settings-help"), False, False, 0
            )
        else:
            api_row.pack_start(
                self._label("Saved locally with owner-only file permissions.", "settings-help"), False, False, 0
            )
        box.pack_start(api_row, False, False, 0)

        language_row = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        language_row.pack_start(self._label("Spoken language", "settings-label"), False, False, 0)
        self._language_combo = Gtk.ComboBoxText()
        for code, language in (
            ("auto", "Auto-detect"), ("en", "English"), ("fr", "French"), ("es", "Spanish"),
            ("de", "German"), ("it", "Italian"), ("pt", "Portuguese"), ("ar", "Arabic"), ("zh", "Chinese"),
        ):
            self._language_combo.append(code, language)
        self._language_combo.set_active_id(self._config.get("language"))
        language_row.pack_start(self._language_combo, False, False, 0)
        box.pack_start(language_row, False, False, 0)

        translate_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        translate_row.pack_start(self._label("Translate to English", "settings-label"), True, True, 0)
        self._translate_switch = Gtk.Switch()
        self._translate_switch.set_active(self._config.get("translate_to_english"))
        translate_row.pack_end(self._translate_switch, False, False, 0)
        box.pack_start(translate_row, False, False, 0)

        font_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        font_row.pack_start(self._label("Transcript size", "settings-label"), True, True, 0)
        self._font_scale = Gtk.SpinButton.new_with_range(12, 32, 1)
        self._font_scale.set_value(self._config.get("font_size"))
        font_row.pack_end(self._font_scale, False, False, 0)
        box.pack_start(font_row, False, False, 0)

        opacity_row = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        opacity_row.pack_start(self._label("Window opacity", "settings-label"), False, False, 0)
        self._opacity_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0.5, 1.0, 0.05)
        self._opacity_scale.set_value(self._config.get("opacity"))
        opacity_row.pack_start(self._opacity_scale, False, False, 0)
        box.pack_start(opacity_row, False, False, 0)

        save_button = self._make_secondary_button("Save settings", "Validate and apply preferences", self._on_save_settings)
        box.pack_start(save_button, False, False, 0)
        box.show_all()

    def _load_initial_settings(self) -> None:
        self._update_font_size(self._config.get("font_size"))
        self.set_opacity(self._config.get("opacity"))
        self.set_keep_above(self._config.get("sticky_mode"))

    def _on_save_settings(self, _button: Gtk.Button) -> None:
        try:
            self._config.update(
                {
                    "api_key": self._config.saved_value("api_key")
                    if self._config.source_for("api_key") == "environment"
                    else self._api_entry.get_text(),
                    "language": self._language_combo.get_active_id() or "auto",
                    "translate_to_english": self._translate_switch.get_active(),
                    "font_size": int(self._font_scale.get_value()),
                    "opacity": self._opacity_scale.get_value(),
                }
            )
        except ConfigError as error:
            self.show_error(str(error))
            return
        self._update_font_size(self._config.get("font_size"))
        self.set_opacity(self._config.get("opacity"))
        if self._on_settings_change_cb:
            self._on_settings_change_cb()
        self._popover.popdown()
        self.set_status("Settings saved", "active", reset_after_ms=2_000)

    def _on_settings_clicked(self, _button: Gtk.Button) -> None:
        if self._popover.is_visible():
            self._popover.popdown()
        else:
            self._popover.popup()

    def _on_save_clicked(self, _button: Gtk.Button) -> None:
        text = self._transcript_text()
        if not text:
            self.show_error("There is no transcript to export yet.")
            return
        dialog = Gtk.FileChooserDialog(
            title="Export transcript", parent=self, action=Gtk.FileChooserAction.SAVE
        )
        dialog.add_buttons("Cancel", Gtk.ResponseType.CANCEL, "Export", Gtk.ResponseType.ACCEPT)
        dialog.set_do_overwrite_confirmation(True)
        dialog.set_current_name(f"transcript_{dt.datetime.now():%Y-%m-%d_%H-%M}.txt")
        try:
            if dialog.run() == Gtk.ResponseType.ACCEPT:
                filename = dialog.get_filename()
                if filename:
                    destination = Path(filename)
                    destination.write_text(text + "\n", encoding="utf-8")
                    os.chmod(destination, 0o600)
                    self.set_status(f"Exported {destination.name}", "active", reset_after_ms=2_500)
        except OSError as error:
            self.show_error(f"Could not export transcript: {error}")
        finally:
            dialog.destroy()

    def _on_listen_clicked(self, _button: Gtk.Button) -> None:
        if self._is_listening:
            self.stop_listening()
            return
        started = self._on_start() if self._on_start else True
        if started:
            self.start_listening()

    def start_listening(self) -> None:
        self._is_listening = True
        self._listen_button.set_label("Stop listening")
        self._listen_button.get_accessible().set_name("Stop listening")
        self._listen_button.get_style_context().add_class("recording")
        self.set_status("Listening…", "active")

    def stop_listening(self) -> None:
        self._is_listening = False
        self._listen_button.set_label("Start listening")
        self._listen_button.get_accessible().set_name("Start listening")
        self._listen_button.get_style_context().remove_class("recording")
        if self._on_stop:
            self._on_stop()
        self.set_status("Ready when you are")

    def _on_sticky_toggled(self, _switch: Gtk.Switch, state: bool) -> bool:
        self.set_keep_above(state)
        try:
            self._config.set("sticky_mode", state)
        except ConfigError as error:
            self.show_error(str(error))
        return False

    def _on_copy_clicked(self, _button: Gtk.Button) -> None:
        text = self._transcript_text()
        if not text:
            self.show_error("There is no transcript to copy yet.")
            return
        Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD).set_text(text, -1)
        self.set_status("Transcript copied", "active", reset_after_ms=1_500)

    def _on_clear_clicked(self, _button: Gtk.Button) -> None:
        self._text_buffer.set_text("")
        self.set_status("Transcript cleared")

    def _on_transcript_changed(self, _buffer: Gtk.TextBuffer) -> None:
        self._empty_state.set_visible(not bool(self._transcript_text()))

    def _on_window_configure(self, _widget: Gtk.Widget, event: Gdk.EventConfigure) -> bool:
        # Debounce resize events so changing window size never produces dozens of disk writes.
        if event.width >= 360 and event.height >= 320:
            self._pending_geometry = (int(event.width), int(event.height))
            if self._geometry_save_source is not None:
                GLib.source_remove(self._geometry_save_source)
            self._geometry_save_source = GLib.timeout_add(500, self._save_geometry)
        return False

    def _save_geometry(self) -> bool:
        self._geometry_save_source = None
        if self._pending_geometry is None:
            return False
        width, height = self._pending_geometry
        self._pending_geometry = None
        try:
            self._config.update({"window_width": width, "window_height": height})
        except ConfigError:
            LOGGER.debug("Could not persist window geometry", exc_info=True)
        return False

    def _transcript_text(self) -> str:
        start, end = self._text_buffer.get_bounds()
        return self._text_buffer.get_text(start, end, True).strip()

    def _update_font_size(self, size: int) -> None:
        provider = Gtk.CssProvider()
        provider.load_from_data(f".transcript-view {{ font-size: {size}px; }}".encode())
        Gtk.StyleContext.add_provider(
            self._text_view.get_style_context(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def set_status(self, message: str, style_class: str = "", *, reset_after_ms: Optional[int] = None) -> None:
        GLib.idle_add(self._do_status, message, style_class, reset_after_ms)

    def _do_status(self, message: str, style_class: str, reset_after_ms: Optional[int]) -> bool:
        if self._status_reset_source is not None:
            GLib.source_remove(self._status_reset_source)
            self._status_reset_source = None
        self._status_label.set_text(message)
        context = self._status_label.get_style_context()
        for class_name in ("active", "error"):
            context.remove_class(class_name)
        if style_class:
            context.add_class(style_class)
        if reset_after_ms:
            self._status_reset_source = GLib.timeout_add(
                reset_after_ms, lambda: self._do_status("Ready when you are", "", None)
            )
        return False

    def append_text(self, text: str) -> None:
        GLib.idle_add(self._do_append, text)

    def _do_append(self, text: str) -> bool:
        clean_text = text.strip()
        if not clean_text:
            return False
        end = self._text_buffer.get_end_iter()
        if self._text_buffer.get_char_count() > 0:
            self._text_buffer.insert(end, " ")
        self._text_buffer.insert(self._text_buffer.get_end_iter(), clean_text)
        self._text_view.scroll_to_iter(self._text_buffer.get_end_iter(), 0.0, False, 0.0, 0.0)
        return False

    def show_error(self, message: str) -> None:
        self.set_status(f"{message}", "error")
