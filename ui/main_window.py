"""GTK3 window for a focused, privacy-explicit transcription session."""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any, Callable, Optional

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gdk, GLib, Gtk

from config import ConfigError, ConfigManager
from exports import ExportFormat, build_export, write_export
from history import HistoryEntry, HistoryStore
from onboarding import (
    GROQ_DATA_CONTROLS_URL,
    GROQ_SPEECH_TO_TEXT_URL,
    OnboardingError,
    groq_cloud_disclosure,
    validate_cloud_setup,
    validate_local_setup,
)
from platform_capabilities import detect_desktop_capabilities
from transcript import SegmentTracker, UndoHistory
from transcription.local_whisper import local_mode_enabled

LOGGER = logging.getLogger(__name__)


class MainWindow(Gtk.Window):
    """A compact recording desk: record, review, copy, and export."""

    def __init__(
        self,
        config: ConfigManager,
        on_start: Optional[Callable[[], bool]] = None,
        on_stop: Optional[Callable[[], None]] = None,
        on_settings_change: Optional[Callable[[], None]] = None,
        on_list_input_devices: Optional[Callable[[], list[Any]]] = None,
    ) -> None:
        super().__init__(title="Voice Transcriber")
        self._config = config
        self._on_start = on_start
        self._on_stop = on_stop
        self._on_settings_change_cb = on_settings_change
        self._on_list_input_devices = on_list_input_devices
        self._is_listening = False
        self._has_refreshed_input_devices = False
        self._status_reset_source: Optional[int] = None
        self._geometry_save_source: Optional[int] = None
        self._pending_geometry: Optional[tuple[int, int]] = None
        self._undo_history = UndoHistory()
        self._applying_snapshot = False
        self._suppress_next_click = False
        self._segment_tracker = SegmentTracker(max_visible=4)
        self._history = HistoryStore()
        self._capabilities = detect_desktop_capabilities()
        self._experimental_local_available = local_mode_enabled()
        self._tray_icon: Optional[Any] = None

        self._setup_window()
        self._apply_styles()
        self._setup_ui()
        self._load_initial_settings()
        self._setup_tray_toggle()
        if not self._config.get("onboarding_complete"):
            GLib.idle_add(self._show_first_run)

    def _setup_window(self) -> None:
        self.set_default_size(self._config.get("window_width"), self._config.get("window_height"))
        self.set_size_request(360, 320)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_resizable(True)
        self.set_wmclass("voice-transcriber", "Voice Transcriber")
        self.set_role("voice-transcriber")
        self.connect("destroy", self._on_destroy)
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
        .segment-strip { background-color: #141B17; border: 1px solid #344338; border-radius: 8px; padding: 6px 10px; }
        .segment-state { color: #AAB8AA; font-size: 11px; }
        .segment-state.pending { color: #D5EAA9; }
        .segment-state.complete { color: #B8E85A; }
        .segment-state.error { color: #FFAA8E; }
        .input-monitor { padding: 3px 1px 0 1px; }
        .input-label { color: #C5D1C4; font-size: 11px; font-weight: 800; letter-spacing: 0.08em; }
        .input-source { color: #9DAE9F; font-size: 11px; }
        levelbar trough { min-height: 8px; border-radius: 99px; background-color: #263229; border: 1px solid #3A4A3E; }
        levelbar block.filled { border-radius: 99px; background-color: #B8E85A; }
        .transcript-shell { background-color: #141B17; border: 1px solid #344338; border-radius: 10px; margin-top: 14px; }
        .transcript-view { background-color: transparent; color: #F4F7F0; font-family: Serif; font-size: 17px; padding: 16px; }
        .empty-title { color: #EDF4E7; font-size: 17px; font-weight: 800; }
        .empty-copy { color: #9DAE9F; font-size: 13px; }
        .bottom-rule { border-top: 1px solid #2B382F; padding-top: 14px; }
        .secondary-button { background-image: none; background-color: #253128; border: 1px solid #405044; color: #E5EDE1; padding: 8px 12px; border-radius: 7px; font-weight: 700; box-shadow: none; }
        .secondary-button:hover, .secondary-button:focus { background-color: #334138; border-color: #617264; }
        .danger-button { color: #FFB19B; }
        .history-card { background-color: #141B17; border: 1px solid #344338; border-radius: 8px; padding: 10px; }
        .settings-box { background-color: #1A211C; color: #F4F7F0; border: 1px solid #405044; border-radius: 9px; padding: 12px; }
        .settings-title { color: #F4F7F0; font-size: 15px; font-weight: 800; }
        .settings-label { color: #C5D1C4; font-size: 12px; font-weight: 700; }
        .settings-help { color: #9DAE9F; font-size: 11px; }
        .onboarding-boundary { background-color: #111813; border: 1px solid #405044; border-radius: 8px; padding: 12px; }
        .onboarding-error { color: #FFAA8E; font-size: 12px; font-weight: 700; }
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
        settings_button = self._make_top_button("Settings", "Configure provider and transcription preferences", self._on_settings_clicked)
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
        self._listen_button.connect("button-press-event", self._on_listen_pressed)
        self._listen_button.connect("button-release-event", self._on_listen_released)
        content.pack_start(self._listen_button, False, False, 0)

        status_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        status_box.get_style_context().add_class("status-chip")
        status_box.set_halign(Gtk.Align.START)
        self._status_label = self._label("Ready when you are", "status")
        self._status_label.get_accessible().set_name("Transcription status")
        status_box.pack_start(self._status_label, False, False, 0)
        content.pack_start(status_box, False, False, 0)

        self._segment_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        self._segment_box.get_style_context().add_class("segment-strip")
        self._segment_box.get_accessible().set_name("Recent transcription segment states")
        self._segment_box.set_no_show_all(True)
        content.pack_start(self._segment_box, False, False, 0)

        input_monitor = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        input_monitor.get_style_context().add_class("input-monitor")
        input_meta = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        input_meta.pack_start(self._label("INPUT SIGNAL", "input-label"), False, False, 0)
        input_meta.pack_start(Gtk.Box(), True, True, 0)
        self._input_source_label = self._label("System default microphone", "input-source", xalign=1.0)
        self._input_source_label.set_tooltip_text("The microphone selected for the next recording session")
        self._input_source_label.get_accessible().set_name("Selected microphone")
        input_meta.pack_end(self._input_source_label, False, False, 0)
        input_monitor.pack_start(input_meta, False, False, 0)
        self._input_level = Gtk.LevelBar.new_for_interval(0.0, 1.0)
        self._input_level.set_mode(Gtk.LevelBarMode.CONTINUOUS)
        self._input_level.set_value(0.0)
        self._input_level.set_tooltip_text("Live microphone signal level. It is not an audio recording.")
        self._input_level.get_accessible().set_name("Live microphone signal level")
        input_monitor.pack_start(self._input_level, False, False, 0)
        content.pack_start(input_monitor, False, False, 0)

        self._provider_boundary_label = self._label("", "privacy-note")
        self._provider_boundary_label.get_accessible().set_name("Active transcription data boundary")
        content.pack_start(self._provider_boundary_label, False, False, 0)

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
        self._text_view.set_editable(True)
        self._text_view.set_cursor_visible(True)
        self._text_view.get_accessible().set_name("Editable current transcript")
        self._text_buffer = self._text_view.get_buffer()
        self._text_buffer.connect("insert-text", self._on_text_edit_before)
        self._text_buffer.connect("delete-range", self._on_text_edit_before)
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

        actions = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        actions.get_style_context().add_class("bottom-rule")
        edit_actions = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        sticky_label = self._label("Keep on top", "settings-label")
        edit_actions.pack_start(sticky_label, False, False, 0)
        self._sticky_switch = Gtk.CheckButton()
        self._sticky_switch.set_active(self._config.get("sticky_mode"))
        self._sticky_switch.set_tooltip_text("Keep Voice Transcriber above other windows")
        self._sticky_switch.get_accessible().set_name("Keep Voice Transcriber on top")
        self._sticky_switch.connect("toggled", self._on_sticky_toggled)
        edit_actions.pack_start(self._sticky_switch, False, False, 0)
        edit_actions.pack_start(Gtk.Box(), True, True, 0)
        undo_button = self._make_secondary_button("Undo", "Undo transcript edit (Ctrl+Z)", self._on_undo_clicked)
        redo_button = self._make_secondary_button("Redo", "Redo transcript edit (Ctrl+Shift+Z)", self._on_redo_clicked)
        edit_actions.pack_end(redo_button, False, False, 0)
        edit_actions.pack_end(undo_button, False, False, 0)
        actions.pack_start(edit_actions, False, False, 0)
        output_actions = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        history_button = self._make_secondary_button(
            "History",
            "Review or permanently delete opt-in transcript history",
            self._on_history_clicked,
        )
        output_actions.pack_start(history_button, False, False, 0)
        output_actions.pack_start(Gtk.Box(), True, True, 0)
        copy_button = self._make_secondary_button("Copy", "Copy transcript to clipboard (Ctrl+Shift+C)", self._on_copy_clicked)
        output_actions.pack_end(copy_button, False, False, 0)
        clear_button = self._make_secondary_button("Clear", "Remove the current transcript", self._on_clear_clicked)
        clear_button.get_style_context().add_class("danger-button")
        output_actions.pack_end(clear_button, False, False, 0)
        actions.pack_start(output_actions, False, False, 0)
        content.pack_end(actions, False, False, 0)

        self._init_settings_popover(settings_button)
        self._install_shortcuts(copy_button, settings_button, undo_button, redo_button)

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

    def _install_shortcuts(
        self,
        copy_button: Gtk.Button,
        settings_button: Gtk.Button,
        undo_button: Gtk.Button,
        redo_button: Gtk.Button,
    ) -> None:
        accel_group = Gtk.AccelGroup()
        self.add_accel_group(accel_group)
        self._listen_button.add_accelerator("clicked", accel_group, Gdk.KEY_Return, Gdk.ModifierType.CONTROL_MASK, Gtk.AccelFlags.VISIBLE)
        copy_button.add_accelerator(
            "clicked", accel_group, Gdk.KEY_C, Gdk.ModifierType.CONTROL_MASK | Gdk.ModifierType.SHIFT_MASK, Gtk.AccelFlags.VISIBLE
        )
        settings_button.add_accelerator("clicked", accel_group, Gdk.KEY_comma, Gdk.ModifierType.CONTROL_MASK, Gtk.AccelFlags.VISIBLE)
        undo_button.add_accelerator(
            "clicked", accel_group, Gdk.KEY_z, Gdk.ModifierType.CONTROL_MASK, Gtk.AccelFlags.VISIBLE
        )
        redo_button.add_accelerator(
            "clicked",
            accel_group,
            Gdk.KEY_z,
            Gdk.ModifierType.CONTROL_MASK | Gdk.ModifierType.SHIFT_MASK,
            Gtk.AccelFlags.VISIBLE,
        )

    def _init_settings_popover(self, parent_button: Gtk.Button) -> None:
        self._popover = Gtk.Popover.new(parent_button)
        self._popover.set_position(Gtk.PositionType.BOTTOM)
        settings_scroll = Gtk.ScrolledWindow()
        settings_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        settings_scroll.set_min_content_width(340)
        settings_scroll.set_min_content_height(420)
        self._popover.add(settings_scroll)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.get_style_context().add_class("settings-box")
        box.set_margin_top(8)
        box.set_margin_bottom(8)
        box.set_margin_start(8)
        box.set_margin_end(8)
        settings_scroll.add(box)
        box.pack_start(self._label("Session settings", "settings-title"), False, False, 0)

        provider_row = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        provider_row.pack_start(self._label("Transcription provider", "settings-label"), False, False, 0)
        self._provider_combo = Gtk.ComboBoxText()
        self._provider_combo.append("groq", "Groq cloud · fast, user-managed key")
        if self._experimental_local_available or self._config.get("provider_mode") == "local_whisper_cpp":
            self._provider_combo.append(
                "local_whisper_cpp", "Local whisper.cpp · experimental source install"
            )
        self._provider_combo.set_active_id(self._config.get("provider_mode"))
        if self._provider_combo.get_active_id() is None:
            self._provider_combo.set_active_id("groq")
        self._provider_combo.get_accessible().set_name("Transcription provider")
        provider_row.pack_start(self._provider_combo, False, False, 0)
        self._provider_help = self._label("", "settings-help")
        provider_row.pack_start(self._provider_help, False, False, 0)
        self._provider_policy_links = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        settings_data_link = Gtk.LinkButton.new_with_label(
            GROQ_DATA_CONTROLS_URL, "Current Groq data controls"
        )
        settings_data_link.get_accessible().set_name("Open current Groq data controls")
        settings_speech_link = Gtk.LinkButton.new_with_label(
            GROQ_SPEECH_TO_TEXT_URL, "Speech pricing and limits"
        )
        settings_speech_link.get_accessible().set_name(
            "Open current Groq speech pricing and limits"
        )
        self._provider_policy_links.pack_start(settings_data_link, False, False, 0)
        self._provider_policy_links.pack_start(settings_speech_link, False, False, 0)
        provider_row.pack_start(self._provider_policy_links, False, False, 0)
        box.pack_start(provider_row, False, False, 0)

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
        self._api_row = api_row

        self._local_runtime_row = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self._local_runtime_row.pack_start(
            self._label("Experimental local runtime", "settings-label"), False, False, 0
        )
        self._local_binary_entry = Gtk.Entry()
        self._local_binary_entry.set_placeholder_text("/path/to/whisper-cli")
        self._local_binary_entry.set_text(self._config.get("local_binary_path"))
        self._local_binary_entry.get_accessible().set_name("Local whisper CLI path")
        self._local_runtime_row.pack_start(self._local_binary_entry, False, False, 0)
        self._local_model_entry = Gtk.Entry()
        self._local_model_entry.set_placeholder_text("/path/to/ggml-model.bin")
        self._local_model_entry.set_text(self._config.get("local_model_path"))
        self._local_model_entry.get_accessible().set_name("Local GGML model path")
        self._local_runtime_row.pack_start(self._local_model_entry, False, False, 0)
        self._local_runtime_row.pack_start(
            self._label(
                "No audio is sent to a provider. You supply and audit both files; model size and speed depend on your hardware.",
                "settings-help",
            ),
            False,
            False,
            0,
        )
        box.pack_start(self._local_runtime_row, False, False, 0)

        device_row = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        device_row.pack_start(self._label("Microphone input", "settings-label"), False, False, 0)
        device_controls = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self._device_combo = Gtk.ComboBoxText()
        self._device_combo.append("default", "System default microphone")
        self._device_combo.set_active_id("default")
        self._device_combo.set_hexpand(True)
        self._device_combo.get_accessible().set_name("Microphone input")
        device_controls.pack_start(self._device_combo, True, True, 0)
        refresh_button = self._make_secondary_button(
            "Refresh", "Find currently available microphone inputs", self._on_refresh_input_devices
        )
        device_controls.pack_end(refresh_button, False, False, 0)
        device_row.pack_start(device_controls, False, False, 0)
        self._device_help = self._label(
            "Choose a source, then start a new session to use it.", "settings-help"
        )
        device_row.pack_start(self._device_help, False, False, 0)
        box.pack_start(device_row, False, False, 0)

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
        self._translate_switch = Gtk.CheckButton()
        self._translate_switch.set_active(self._config.get("translate_to_english"))
        self._translate_switch.get_accessible().set_name("Translate to English")
        translate_row.pack_end(self._translate_switch, False, False, 0)
        box.pack_start(translate_row, False, False, 0)

        capture_row = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        capture_row.pack_start(self._label("Capture control", "settings-label"), False, False, 0)
        self._capture_mode_combo = Gtk.ComboBoxText()
        self._capture_mode_combo.append("toggle", "Click to start / stop")
        self._capture_mode_combo.append("push_to_talk", "Hold to talk while app is focused")
        self._capture_mode_combo.set_active_id(self._config.get("capture_mode"))
        self._capture_mode_combo.get_accessible().set_name("Capture control mode")
        capture_row.pack_start(self._capture_mode_combo, False, False, 0)
        capture_row.pack_start(
            self._label(self._capabilities.explanation, "settings-help"), False, False, 0
        )
        box.pack_start(capture_row, False, False, 0)

        copy_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        copy_row.pack_start(self._label("Copy after each final segment", "settings-label"), True, True, 0)
        self._copy_on_final_switch = Gtk.CheckButton()
        self._copy_on_final_switch.set_active(self._config.get("copy_on_final"))
        self._copy_on_final_switch.get_accessible().set_name("Copy transcript after each final segment")
        copy_row.pack_end(self._copy_on_final_switch, False, False, 0)
        box.pack_start(copy_row, False, False, 0)

        history_row = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        history_toggle = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        history_toggle.pack_start(self._label("Keep local transcript history", "settings-label"), True, True, 0)
        self._history_switch = Gtk.CheckButton()
        self._history_switch.set_active(self._config.get("history_enabled"))
        self._history_switch.get_accessible().set_name("Keep local transcript history")
        history_toggle.pack_end(self._history_switch, False, False, 0)
        history_row.pack_start(history_toggle, False, False, 0)
        retention = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        retention.pack_start(self._label("Delete after", "settings-help"), True, True, 0)
        self._history_retention = Gtk.SpinButton.new_with_range(1, 365, 1)
        self._history_retention.set_value(self._config.get("history_retention_days"))
        self._history_retention.get_accessible().set_name("History retention days")
        retention.pack_end(self._history_retention, False, False, 0)
        retention.pack_end(self._label("days", "settings-help"), False, False, 0)
        history_row.pack_start(retention, False, False, 0)
        history_row.pack_start(
            self._label(f"Disabled by default · text only · {self._history.path}", "settings-help"),
            False,
            False,
            0,
        )
        box.pack_start(history_row, False, False, 0)

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
        self._provider_combo.connect("changed", self._sync_provider_controls)
        box.show_all()
        self._sync_provider_controls()

    def _load_initial_settings(self) -> None:
        self._update_font_size(self._config.get("font_size"))
        self.set_opacity(self._config.get("opacity"))
        self.set_keep_above(self._config.get("sticky_mode"))
        self._apply_capture_mode()
        self.refresh_provider_boundary()

    def refresh_provider_boundary(self) -> None:
        """Keep the active provider and transmission boundary visible on the desk."""
        if self._config.get("provider_mode") == "local_whisper_cpp":
            message = "Local model · audio stays on this device · experimental source-install mode"
        else:
            message = "Groq cloud · each completed speech segment leaves this device over HTTPS · raw audio is not saved by this app"
        self._provider_boundary_label.set_text(message)
        self._provider_boundary_label.set_tooltip_text(message)

    def _sync_provider_controls(self, *_args: Any) -> None:
        local = self._provider_combo.get_active_id() == "local_whisper_cpp"
        if local:
            help_text = (
                "Experimental local mode is enabled for this source session. It is deliberately unavailable in the current Flatpak."
                if self._experimental_local_available
                else "Experimental local mode is disabled. Set VOICE_TRANSCRIBER_EXPERIMENTAL_LOCAL=1 in a source install or switch to Groq."
            )
        else:
            provider_facts, billing_facts = groq_cloud_disclosure()
            help_text = (
                "Completed speech segments leave the device; silence detection and the live meter "
                f"stay local. {provider_facts} {billing_facts}"
            )
        self._provider_help.set_text(help_text)
        self._provider_policy_links.set_visible(not local)
        self._api_row.set_visible(not local)
        self._local_runtime_row.set_visible(local)

    def _apply_capture_mode(self) -> None:
        if self._is_listening:
            return
        push_to_talk = self._config.get("capture_mode") == "push_to_talk"
        label = "Hold to talk" if push_to_talk else "Start listening"
        self._listen_button.set_label(label)
        self._listen_button.get_accessible().set_name(label)
        tooltip = (
            "Hold while speaking; release to stop (focused app only)"
            if push_to_talk
            else "Start or stop microphone capture (Ctrl+Enter)"
        )
        self._listen_button.set_tooltip_text(tooltip)

    def _show_first_run(self) -> bool:
        """Offer a keyboard-operable provider choice with its exact data boundary."""
        dialog = Gtk.Dialog(title="Set up Voice Transcriber", transient_for=self, modal=True)
        dialog.set_default_size(500, 620)
        dialog.add_button("Explore first", Gtk.ResponseType.CANCEL)
        save_button = dialog.add_button("Save and continue", Gtk.ResponseType.APPLY)
        save_button.get_style_context().add_class("suggested-action")
        dialog.set_default_response(Gtk.ResponseType.APPLY)

        content_area = dialog.get_content_area()
        content_area.set_spacing(0)
        setup_scroll = Gtk.ScrolledWindow()
        setup_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        content_area.pack_start(setup_scroll, True, True, 0)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.set_spacing(12)
        box.set_margin_top(18)
        box.set_margin_bottom(18)
        box.set_margin_start(20)
        box.set_margin_end(20)
        setup_scroll.add(box)
        box.pack_start(self._label("FIRST RUN", "eyebrow"), False, False, 0)
        title = self._label("Know the boundary before you speak", "settings-title")
        title.get_accessible().set_name("First-run setup")
        box.pack_start(title, False, False, 0)
        intro = self._label("", "privacy-note")
        box.pack_start(intro, False, False, 0)

        provider_combo: Optional[Gtk.ComboBoxText] = None
        if self._experimental_local_available:
            box.pack_start(self._label("Transcription provider", "settings-label"), False, False, 0)
            provider_combo = Gtk.ComboBoxText()
            provider_combo.append("groq", "Groq cloud · user-managed key")
            provider_combo.append("local_whisper_cpp", "Local whisper.cpp · experimental")
            provider_combo.set_active_id(self._config.get("provider_mode"))
            provider_combo.get_accessible().set_name("First-run transcription provider")
            box.pack_start(provider_combo, False, False, 0)

        boundary = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        boundary.get_style_context().add_class("onboarding-boundary")
        boundary_title = self._label("", "settings-label")
        boundary_sent = self._label("", "settings-help")
        boundary_local = self._label("", "settings-help")
        boundary_provider_facts = self._label("", "settings-help")
        boundary_billing = self._label("", "settings-help")
        facts_links = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        data_controls_link = Gtk.LinkButton.new_with_label(
            GROQ_DATA_CONTROLS_URL, "Current Groq data controls"
        )
        data_controls_link.get_accessible().set_name("Open current Groq data controls")
        speech_docs_link = Gtk.LinkButton.new_with_label(
            GROQ_SPEECH_TO_TEXT_URL, "Speech pricing and limits"
        )
        speech_docs_link.get_accessible().set_name("Open current Groq speech pricing and limits")
        facts_links.pack_start(data_controls_link, False, False, 0)
        facts_links.pack_start(speech_docs_link, False, False, 0)
        boundary.pack_start(boundary_title, False, False, 0)
        boundary.pack_start(boundary_sent, False, False, 0)
        boundary.pack_start(boundary_local, False, False, 0)
        boundary.pack_start(boundary_provider_facts, False, False, 0)
        boundary.pack_start(boundary_billing, False, False, 0)
        boundary.pack_start(facts_links, False, False, 0)
        box.pack_start(boundary, False, False, 0)

        key_label = self._label("Groq API key", "settings-label")
        box.pack_start(key_label, False, False, 0)
        key_entry = Gtk.Entry()
        key_entry.set_visibility(False)
        key_entry.set_invisible_char("•")
        key_entry.set_placeholder_text("gsk_…")
        key_entry.set_activates_default(True)
        key_entry.get_accessible().set_name("Groq API key")
        if self._config.source_for("api_key") == "environment":
            key_entry.set_placeholder_text("Set by GROQ_API_KEY")
            key_entry.set_sensitive(False)
        else:
            key_entry.set_text(self._config.saved_value("api_key") or "")
        box.pack_start(key_entry, False, False, 0)

        local_runtime = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        local_runtime.pack_start(
            self._label("whisper.cpp executable and GGML model", "settings-label"), False, False, 0
        )
        local_binary_entry = Gtk.Entry()
        local_binary_entry.set_placeholder_text("/path/to/whisper-cli")
        local_binary_entry.set_text(self._config.get("local_binary_path"))
        local_binary_entry.get_accessible().set_name("Local whisper CLI path")
        local_runtime.pack_start(local_binary_entry, False, False, 0)
        local_model_entry = Gtk.Entry()
        local_model_entry.set_placeholder_text("/path/to/ggml-model.bin")
        local_model_entry.set_text(self._config.get("local_model_path"))
        local_model_entry.get_accessible().set_name("Local GGML model path")
        local_runtime.pack_start(local_model_entry, False, False, 0)
        local_runtime.pack_start(
            self._label(
                "You supply these files. Nothing is downloaded automatically; model size, RAM use, and latency depend on your hardware.",
                "settings-help",
            ),
            False,
            False,
            0,
        )
        box.pack_start(local_runtime, False, False, 0)

        language_label = self._label("Spoken language", "settings-label")
        box.pack_start(language_label, False, False, 0)
        language_combo = Gtk.ComboBoxText()
        for code, language in (
            ("auto", "Auto-detect"),
            ("en", "English"),
            ("fr", "French"),
            ("es", "Spanish"),
            ("de", "German"),
            ("it", "Italian"),
            ("pt", "Portuguese"),
            ("ar", "Arabic"),
            ("zh", "Chinese"),
        ):
            language_combo.append(code, language)
        language_combo.set_active_id(self._config.get("language"))
        language_combo.get_accessible().set_name("Spoken language")
        box.pack_start(language_combo, False, False, 0)

        device_label = self._label("Microphone input", "settings-label")
        box.pack_start(device_label, False, False, 0)
        device_combo = Gtk.ComboBoxText()
        device_combo.append("default", "System default microphone")
        saved_device = self._config.get("input_device_index")
        selected_device = "default" if saved_device is None else str(saved_device)
        try:
            devices = self._on_list_input_devices() if self._on_list_input_devices else []
        except Exception:
            LOGGER.debug("Could not discover inputs during first-run setup", exc_info=True)
            devices = []
        known_devices = {"default"}
        for device in devices:
            identifier = str(device.index)
            known_devices.add(identifier)
            device_combo.append(identifier, f"{device.name}{' · default' if device.is_default else ''}")
        if selected_device not in known_devices and selected_device != "default":
            device_combo.append(selected_device, f"Saved device #{selected_device} · unavailable")
        device_combo.set_active_id(selected_device)
        device_combo.get_accessible().set_name("Microphone input")
        box.pack_start(device_combo, False, False, 0)

        consent = Gtk.CheckButton(
            label="I understand that completed speech segments will be sent to Groq."
        )
        consent.set_tooltip_text("Required before cloud transcription can be enabled")
        consent.get_accessible().set_name("Confirm Groq cloud data boundary")
        box.pack_start(consent, False, False, 0)
        error_label = self._label("", "onboarding-error")
        error_label.set_no_show_all(True)
        box.pack_start(error_label, False, False, 0)

        def selected_provider() -> str:
            return provider_combo.get_active_id() if provider_combo is not None else "groq"

        def sync_first_run_provider(*_args: Any) -> None:
            local = selected_provider() == "local_whisper_cpp"
            provider_facts, billing_facts = groq_cloud_disclosure()
            key_label.set_visible(not local)
            key_entry.set_visible(not local)
            consent.set_visible(not local)
            local_runtime.set_visible(local)
            boundary_provider_facts.set_visible(not local)
            boundary_billing.set_visible(not local)
            facts_links.set_visible(not local)
            if local:
                intro.set_text(
                    "Voice activity detection and transcription run locally. Raw audio is passed in memory to your whisper.cpp process and is not saved by this app."
                )
                boundary_title.set_text("Provider · Local whisper.cpp (experimental)")
                boundary_sent.set_text("Sent: nothing to a transcription provider.")
                boundary_local.set_text(
                    "Local: speech audio in memory, model execution, input meter, active transcript, and preferences."
                )
            else:
                intro.set_text(
                    "Voice activity detection runs locally. When a speech segment ends, that segment is sent to Groq cloud for transcription. Raw audio is not saved by this app."
                )
                boundary_title.set_text("Provider · Groq cloud")
                boundary_sent.set_text(
                    "Sent: completed speech segments and the selected language/translation request."
                )
                boundary_local.set_text(
                    "Local: silence detection, input meter, active transcript, and preferences."
                )
                boundary_provider_facts.set_text(provider_facts)
                boundary_billing.set_text(billing_facts)

        if provider_combo is not None:
            provider_combo.connect("changed", sync_first_run_provider)
        dialog.show_all()
        sync_first_run_provider()
        error_label.hide()

        try:
            while True:
                response = dialog.run()
                if response != Gtk.ResponseType.APPLY:
                    return False
                try:
                    provider_mode = selected_provider()
                    if provider_mode == "local_whisper_cpp":
                        binary_path, model_path = validate_local_setup(
                            local_binary_entry.get_text(), local_model_entry.get_text()
                        )
                        clean_key = self._config.saved_value("api_key")
                    else:
                        configured_key = (
                            self._config.get("api_key")
                            if self._config.source_for("api_key") == "environment"
                            else key_entry.get_text()
                        )
                        clean_key = validate_cloud_setup(
                            configured_key,
                            data_boundary_confirmed=consent.get_active(),
                        )
                        binary_path = self._config.get("local_binary_path")
                        model_path = self._config.get("local_model_path")
                    selected = device_combo.get_active_id()
                    self._config.update(
                        {
                            "api_key": self._config.saved_value("api_key")
                            if self._config.source_for("api_key") == "environment"
                            else clean_key,
                            "provider_mode": provider_mode,
                            "local_binary_path": binary_path,
                            "local_model_path": model_path,
                            "language": language_combo.get_active_id() or "auto",
                            "input_device_index": None
                            if not selected or selected == "default"
                            else int(selected),
                            "onboarding_complete": True,
                        }
                    )
                except (ConfigError, OnboardingError) as error:
                    error_label.set_text(str(error))
                    error_label.show()
                    continue

                self._language_combo.set_active_id(self._config.get("language"))
                self._provider_combo.set_active_id(self._config.get("provider_mode"))
                self._local_binary_entry.set_text(self._config.get("local_binary_path"))
                self._local_model_entry.set_text(self._config.get("local_model_path"))
                self._sync_provider_controls()
                self._device_combo.set_active_id(selected or "default")
                if self._config.source_for("api_key") != "environment":
                    self._api_entry.set_text(self._config.saved_value("api_key"))
                if self._on_settings_change_cb:
                    self._on_settings_change_cb()
                self.set_status("Setup complete · ready to start", "active", reset_after_ms=3_000)
                return False
        finally:
            dialog.destroy()

    def _on_save_settings(self, _button: Gtk.Button) -> None:
        try:
            provider_mode = self._provider_combo.get_active_id() or "groq"
            local_binary_path = self._local_binary_entry.get_text()
            local_model_path = self._local_model_entry.get_text()
            if provider_mode == "local_whisper_cpp":
                if not self._experimental_local_available:
                    raise OnboardingError(
                        "Experimental local mode is disabled for this session. Start a source install with VOICE_TRANSCRIBER_EXPERIMENTAL_LOCAL=1."
                    )
                local_binary_path, local_model_path = validate_local_setup(
                    local_binary_path, local_model_path
                )
            self._config.update(
                {
                    "api_key": self._config.saved_value("api_key")
                    if self._config.source_for("api_key") == "environment"
                    else self._api_entry.get_text(),
                    "provider_mode": provider_mode,
                    "local_binary_path": local_binary_path,
                    "local_model_path": local_model_path,
                    "language": self._language_combo.get_active_id() or "auto",
                    "translate_to_english": self._translate_switch.get_active(),
                    "font_size": int(self._font_scale.get_value()),
                    "opacity": self._opacity_scale.get_value(),
                    "input_device_index": self._selected_input_device_index(),
                    "capture_mode": self._capture_mode_combo.get_active_id() or "toggle",
                    "copy_on_final": self._copy_on_final_switch.get_active(),
                    "history_enabled": self._history_switch.get_active(),
                    "history_retention_days": int(self._history_retention.get_value()),
                }
            )
        except (ConfigError, OnboardingError) as error:
            self.show_error(str(error))
            return
        self._update_font_size(self._config.get("font_size"))
        self.set_opacity(self._config.get("opacity"))
        self._apply_capture_mode()
        if self._config.get("history_enabled"):
            self._history.list(retention_days=self._config.get("history_retention_days"))
        if self._on_settings_change_cb:
            self._on_settings_change_cb()
        self._popover.popdown()
        self.set_status("Settings saved · microphone choice applies next session", "active", reset_after_ms=2_500)

    def _on_settings_clicked(self, _button: Gtk.Button) -> None:
        if self._popover.is_visible():
            self._popover.popdown()
        else:
            self._refresh_input_devices()
            self._popover.popup()

    def _on_refresh_input_devices(self, _button: Gtk.Button) -> None:
        self._refresh_input_devices()

    def _selected_input_device_index(self) -> Optional[int]:
        selected = self._device_combo.get_active_id()
        return None if not selected or selected == "default" else int(selected)

    def _refresh_input_devices(self) -> None:
        """Populate the picker only when requested; discovery opens PortAudio briefly."""
        selected = self._device_combo.get_active_id()
        if not self._has_refreshed_input_devices:
            saved = self._config.get("input_device_index")
            selected = "default" if saved is None else str(saved)

        self._device_combo.remove_all()
        self._device_combo.append("default", "System default microphone")
        if self._on_list_input_devices is None:
            self._device_help.set_text("Input discovery is unavailable in this session.")
            self._device_combo.set_active_id("default")
            self._has_refreshed_input_devices = True
            return

        try:
            devices = self._on_list_input_devices()
        except Exception:
            LOGGER.debug("Could not list microphone inputs", exc_info=True)
            self._device_help.set_text("Could not list inputs. The system default remains available.")
            if selected and selected != "default":
                self._device_combo.append(selected, f"Saved device #{selected} · unavailable")
            self._device_combo.set_active_id(selected if selected else "default")
            self._has_refreshed_input_devices = True
            return

        available_ids = {"default"}
        for device in devices:
            identifier = str(device.index)
            available_ids.add(identifier)
            suffix = " · default" if device.is_default else ""
            self._device_combo.append(identifier, f"{device.name}{suffix}")
        if not devices:
            self._device_help.set_text("No explicit inputs found. Connect a microphone or use the system default.")
        else:
            self._device_help.set_text(f"{len(devices)} input{'s' if len(devices) != 1 else ''} found. Choice applies next session.")

        if selected not in available_ids and selected != "default":
            self._device_combo.append(selected, f"Saved device #{selected} · unavailable")
        self._device_combo.set_active_id(selected if selected else "default")
        self._has_refreshed_input_devices = True

    def _on_save_clicked(self, _button: Gtk.Button) -> None:
        text = self._transcript_text()
        if not text:
            self.show_error("There is no transcript to export yet.")
            return
        format_combo = Gtk.ComboBoxText()
        format_combo.append("text", "Plain text (.txt)")
        format_combo.append("markdown", "Markdown (.md)")
        format_combo.append("timestamped", "Timestamped text (.txt)")
        format_combo.set_active_id("text")
        format_combo.get_accessible().set_name("Export format")
        format_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        format_box.set_margin_top(8)
        format_box.set_margin_bottom(8)
        format_box.set_margin_start(8)
        format_box.set_margin_end(8)
        format_box.pack_start(self._label("Format", "settings-label"), False, False, 0)
        format_box.pack_start(format_combo, True, True, 0)
        format_box.show_all()
        dialog = Gtk.FileChooserDialog(
            title="Export transcript", parent=self, action=Gtk.FileChooserAction.SAVE
        )
        dialog.add_buttons("Cancel", Gtk.ResponseType.CANCEL, "Export", Gtk.ResponseType.ACCEPT)
        dialog.set_do_overwrite_confirmation(True)
        dialog.set_extra_widget(format_box)
        initial = build_export(text, "text")
        dialog.set_current_name(initial.suggested_name)

        def update_name(_combo: Gtk.ComboBoxText) -> None:
            selected = format_combo.get_active_id() or "text"
            document = build_export(text, selected)
            dialog.set_current_name(document.suggested_name)

        format_combo.connect("changed", update_name)
        try:
            if dialog.run() == Gtk.ResponseType.ACCEPT:
                filename = dialog.get_filename()
                if filename:
                    destination = Path(filename)
                    export_format: ExportFormat = format_combo.get_active_id() or "text"
                    document = build_export(text, export_format)
                    if self._confirm_export(destination, document.format):
                        write_export(destination, document)
                        self.set_status(
                            f"Exported {destination.name} · owner-only permissions",
                            "active",
                            reset_after_ms=2_500,
                        )
        except OSError as error:
            self.show_error(f"Could not export transcript: {error}")
        finally:
            dialog.destroy()

    def _confirm_export(self, destination: Path, export_format: str) -> bool:
        confirmation = Gtk.MessageDialog(
            transient_for=self,
            modal=True,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.NONE,
            text="Write this transcript export?",
        )
        confirmation.format_secondary_text(
            f"Destination: {destination}\nFormat: {export_format}\nPermissions: owner read/write only"
        )
        confirmation.add_button("Back", Gtk.ResponseType.CANCEL)
        confirmation.add_button("Write export", Gtk.ResponseType.ACCEPT)
        try:
            return confirmation.run() == Gtk.ResponseType.ACCEPT
        finally:
            confirmation.destroy()

    def _on_listen_clicked(self, _button: Gtk.Button) -> None:
        if self._suppress_next_click:
            self._suppress_next_click = False
            return
        if self._is_listening:
            self.stop_listening()
            return
        started = self._on_start() if self._on_start else True
        if started:
            self.start_listening()

    def _on_listen_pressed(self, _button: Gtk.Button, event: Gdk.EventButton) -> bool:
        if self._config.get("capture_mode") != "push_to_talk" or event.button != 1:
            return False
        self._suppress_next_click = True
        if not self._is_listening:
            started = self._on_start() if self._on_start else True
            if started:
                self.start_listening()
        return False

    def _on_listen_released(self, _button: Gtk.Button, event: Gdk.EventButton) -> bool:
        if self._config.get("capture_mode") == "push_to_talk" and event.button == 1:
            self._suppress_next_click = True
            if self._is_listening:
                self.stop_listening()
        return False

    def start_listening(self) -> None:
        self._is_listening = True
        label = (
            "Release to stop"
            if self._config.get("capture_mode") == "push_to_talk"
            else "Stop listening"
        )
        self._listen_button.set_label(label)
        self._listen_button.get_accessible().set_name(label)
        self._listen_button.get_style_context().add_class("recording")
        self.set_status("Listening…", "active")

    def stop_listening(self) -> None:
        self._is_listening = False
        self._apply_capture_mode()
        self._listen_button.get_style_context().remove_class("recording")
        self.set_input_level(0.0)
        if self._on_stop:
            self._on_stop()
        self.set_status("Ready when you are")

    def _on_sticky_toggled(self, checkbox: Gtk.CheckButton) -> None:
        state = checkbox.get_active()
        self.set_keep_above(state)
        try:
            self._config.set("sticky_mode", state)
        except ConfigError as error:
            self.show_error(str(error))

    def _on_copy_clicked(self, _button: Gtk.Button) -> None:
        self.copy_transcript()

    def copy_transcript(self, *, automatic: bool = False) -> None:
        text = self._transcript_text()
        if not text:
            if not automatic:
                self.show_error("There is no transcript to copy yet.")
            return
        Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD).set_text(text, -1)
        message = "Final transcript copied automatically" if automatic else "Transcript copied"
        self.set_status(message, "active", reset_after_ms=1_500)

    def copy_transcript_after_final(self) -> None:
        GLib.idle_add(self._do_copy_transcript_after_final)

    def _do_copy_transcript_after_final(self) -> bool:
        self.copy_transcript(automatic=True)
        return False

    def _on_clear_clicked(self, _button: Gtk.Button) -> None:
        if not self._transcript_text():
            return
        dialog = Gtk.MessageDialog(
            transient_for=self,
            modal=True,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.NONE,
            text="Discard the current transcript?",
        )
        detail = (
            "This clears the desk. It will not be added to history. Existing explicit exports are unchanged."
            if self._config.get("history_enabled")
            else "History is off, so this text cannot be recovered unless you already copied or exported it."
        )
        dialog.format_secondary_text(detail)
        dialog.add_button("Keep editing", Gtk.ResponseType.CANCEL)
        dialog.add_button("Discard transcript", Gtk.ResponseType.ACCEPT)
        try:
            if dialog.run() == Gtk.ResponseType.ACCEPT:
                self._replace_transcript("", remember=True)
                self.set_status("Transcript permanently cleared from this desk")
        finally:
            dialog.destroy()

    def _on_history_clicked(self, _button: Gtk.Button) -> None:
        if not self._config.get("history_enabled"):
            dialog = Gtk.MessageDialog(
                transient_for=self,
                modal=True,
                message_type=Gtk.MessageType.INFO,
                buttons=Gtk.ButtonsType.CLOSE,
                text="Local history is off",
            )
            dialog.format_secondary_text(
                f"Nothing is saved automatically. Enable text-only history in Settings if you want it.\n\nStorage: {self._history.path}"
            )
            dialog.run()
            dialog.destroy()
            return

        try:
            entries = self._history.list(
                retention_days=self._config.get("history_retention_days")
            )
        except (OSError, ValueError) as error:
            self.show_error(f"Could not read local history: {error}")
            return
        dialog = Gtk.Dialog(title="Local transcript history", transient_for=self, modal=True)
        dialog.set_default_size(560, 440)
        dialog.add_button("Close", Gtk.ResponseType.CLOSE)
        if entries:
            clear_button = dialog.add_button("Clear all history", Gtk.ResponseType.REJECT)
            clear_button.get_style_context().add_class("destructive-action")
        area = dialog.get_content_area()
        area.set_spacing(10)
        area.set_margin_top(14)
        area.set_margin_bottom(14)
        area.set_margin_start(14)
        area.set_margin_end(14)
        area.pack_start(
            self._label(
                f"Text only · automatically removed after {self._config.get('history_retention_days')} days · {self._history.path}",
                "settings-help",
            ),
            False,
            False,
            0,
        )
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        entries_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        scrolled.add(entries_box)
        area.pack_start(scrolled, True, True, 0)
        if not entries:
            entries_box.pack_start(
                self._label("No retained transcripts yet.", "empty-copy", xalign=0.5),
                True,
                True,
                20,
            )
        for entry in entries:
            entries_box.pack_start(self._history_card(entry), False, False, 0)
        dialog.show_all()
        try:
            if dialog.run() == Gtk.ResponseType.REJECT and self._confirm_clear_history():
                self._history.clear()
                self.set_status("All local history permanently deleted", "active", reset_after_ms=2_500)
        finally:
            dialog.destroy()

    def _history_card(self, entry: HistoryEntry) -> Gtk.Box:
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=7)
        card.get_style_context().add_class("history-card")
        created = entry.created_at.replace("T", " ").replace("Z", " UTC")
        card.pack_start(self._label(created, "settings-help"), False, False, 0)
        preview = entry.text if len(entry.text) <= 180 else entry.text[:177] + "…"
        card.pack_start(self._label(preview, "settings-label"), False, False, 0)
        actions = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        use_button = self._make_secondary_button(
            "Use on desk",
            "Replace the current desk with this retained transcript",
            lambda _button, item=entry: self._restore_history_entry(item),
        )
        copy_button = self._make_secondary_button(
            "Copy",
            "Copy this retained transcript",
            lambda _button, item=entry: self._copy_history_entry(item),
        )
        delete_button = self._make_secondary_button(
            "Delete",
            "Permanently delete this retained transcript",
            lambda _button, item=entry, widget=card: self._delete_history_entry(item, widget),
        )
        delete_button.get_style_context().add_class("danger-button")
        actions.pack_end(delete_button, False, False, 0)
        actions.pack_end(copy_button, False, False, 0)
        actions.pack_end(use_button, False, False, 0)
        card.pack_start(actions, False, False, 0)
        return card

    def _restore_history_entry(self, entry: HistoryEntry) -> None:
        if self._transcript_text() and not self._confirm_replace_transcript():
            return
        self._replace_transcript(entry.text, remember=True)
        self.set_status("History entry opened on the editable desk", "active", reset_after_ms=2_000)

    def _copy_history_entry(self, entry: HistoryEntry) -> None:
        Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD).set_text(entry.text, -1)
        self.set_status("History entry copied", "active", reset_after_ms=1_500)

    def _delete_history_entry(self, entry: HistoryEntry, card: Gtk.Widget) -> None:
        confirmation = Gtk.MessageDialog(
            transient_for=self,
            modal=True,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.OK_CANCEL,
            text="Permanently delete this history entry?",
        )
        try:
            if confirmation.run() == Gtk.ResponseType.OK and self._history.delete(entry.id):
                card.destroy()
                self.set_status("History entry permanently deleted", "active", reset_after_ms=1_500)
        finally:
            confirmation.destroy()

    def _confirm_replace_transcript(self) -> bool:
        dialog = Gtk.MessageDialog(
            transient_for=self,
            modal=True,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.NONE,
            text="Replace the current transcript?",
        )
        dialog.format_secondary_text("You can undo this replacement after returning to the desk.")
        dialog.add_button("Keep current", Gtk.ResponseType.CANCEL)
        dialog.add_button("Replace", Gtk.ResponseType.ACCEPT)
        try:
            return dialog.run() == Gtk.ResponseType.ACCEPT
        finally:
            dialog.destroy()

    def _confirm_clear_history(self) -> bool:
        dialog = Gtk.MessageDialog(
            transient_for=self,
            modal=True,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.NONE,
            text="Permanently delete all local history?",
        )
        dialog.format_secondary_text("Explicit exports are not affected. This history cannot be recovered.")
        dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
        dialog.add_button("Delete all", Gtk.ResponseType.ACCEPT)
        try:
            return dialog.run() == Gtk.ResponseType.ACCEPT
        finally:
            dialog.destroy()

    def _on_undo_clicked(self, _button: Gtk.Button) -> None:
        current = self._transcript_text(raw=True)
        replacement = self._undo_history.undo(current)
        if replacement != current:
            self._replace_transcript(replacement, remember=False)
            self.set_status("Edit undone", "active", reset_after_ms=1_000)

    def _on_redo_clicked(self, _button: Gtk.Button) -> None:
        current = self._transcript_text(raw=True)
        replacement = self._undo_history.redo(current)
        if replacement != current:
            self._replace_transcript(replacement, remember=False)
            self.set_status("Edit restored", "active", reset_after_ms=1_000)

    def _on_text_edit_before(self, _buffer: Gtk.TextBuffer, *_args: Any) -> None:
        if not self._applying_snapshot:
            self._undo_history.remember(self._transcript_text(raw=True))

    def _replace_transcript(self, text: str, *, remember: bool) -> None:
        current = self._transcript_text(raw=True)
        if remember:
            self._undo_history.remember(current)
        self._applying_snapshot = True
        try:
            self._text_buffer.set_text(text)
        finally:
            self._applying_snapshot = False

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

    def _setup_tray_toggle(self) -> None:
        if not self._capabilities.tray_window_toggle or not hasattr(Gtk, "StatusIcon"):
            return
        try:
            self._tray_icon = Gtk.StatusIcon.new_from_icon_name(
                "io.github.othmaneblial.audio_capture"
            )
            self._tray_icon.set_tooltip_text("Voice Transcriber · toggle window")
            self._tray_icon.connect("activate", self._on_tray_activate)
            self._tray_icon.set_visible(True)
        except Exception:
            self._tray_icon = None
            LOGGER.debug("Legacy X11 tray toggle is unavailable", exc_info=True)

    def _on_tray_activate(self, _icon: Any) -> None:
        if self.get_visible():
            self.hide()
        else:
            self.show_all()
            self.present()

    def _on_destroy(self, _window: Gtk.Window) -> None:
        if self._config.get("history_enabled"):
            text = self._transcript_text()
            if text:
                try:
                    self._history.add(
                        text,
                        retention_days=self._config.get("history_retention_days"),
                    )
                except (OSError, ValueError):
                    LOGGER.warning("Could not save opt-in transcript history", exc_info=True)
        if self._tray_icon is not None:
            self._tray_icon.set_visible(False)
        Gtk.main_quit()

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

    def _transcript_text(self, *, raw: bool = False) -> str:
        start, end = self._text_buffer.get_bounds()
        text = self._text_buffer.get_text(start, end, True)
        return text if raw else text.strip()

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
        self._undo_history.remember(self._transcript_text(raw=True))
        self._applying_snapshot = True
        try:
            end = self._text_buffer.get_end_iter()
            if self._text_buffer.get_char_count() > 0:
                self._text_buffer.insert(end, " ")
            self._text_buffer.insert(self._text_buffer.get_end_iter(), clean_text)
        finally:
            self._applying_snapshot = False
        self._text_view.scroll_to_iter(self._text_buffer.get_end_iter(), 0.0, False, 0.0, 0.0)
        return False

    def update_segment_state(self, request_id: str, state: str, detail: Optional[str]) -> None:
        """Show a bounded per-request state without retaining audio or transcript text."""
        GLib.idle_add(self._do_update_segment_state, request_id, state, detail)

    def _do_update_segment_state(
        self, request_id: str, state: str, detail: Optional[str]
    ) -> bool:
        try:
            self._segment_tracker.update(request_id, state, detail)
        except ValueError:
            LOGGER.debug("Ignored invalid segment state: %s", state)
            return False
        for child in self._segment_box.get_children():
            child.destroy()
        for status in self._segment_tracker.visible():
            marker = {"pending": "●", "complete": "✓", "error": "!"}[status.state]
            label = self._label(
                f"{marker} Segment {status.ordinal} · {status.detail}", "segment-state"
            )
            label.get_style_context().add_class(status.state)
            label.get_accessible().set_name(
                f"Segment {status.ordinal}, {status.state}: {status.detail}"
            )
            self._segment_box.pack_start(label, False, False, 0)
        self._segment_box.set_no_show_all(False)
        self._segment_box.show_all()
        return False

    def set_input_level(self, level: float) -> None:
        """Update the visual meter from any capture thread without retaining audio."""
        try:
            normalized = max(0.0, min(1.0, float(level)))
        except (TypeError, ValueError):
            normalized = 0.0
        GLib.idle_add(self._do_set_input_level, normalized)

    def _do_set_input_level(self, level: float) -> bool:
        self._input_level.set_value(level)
        return False

    def set_input_source(self, name: str) -> None:
        """Show the active microphone identity without exposing any captured data."""
        clean_name = " ".join(name.split()) or "System default microphone"
        GLib.idle_add(self._do_set_input_source, clean_name)

    def _do_set_input_source(self, name: str) -> bool:
        self._input_source_label.set_text(name)
        self._input_source_label.set_tooltip_text(name)
        return False

    def show_error(self, message: str) -> None:
        self.set_status(f"{message}", "error")
