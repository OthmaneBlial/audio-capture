"""Main application window with GTK3 - Modern Dark Theme."""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib, Pango
from typing import Callable, Optional, Any
import datetime
from config import ConfigManager


class MainWindow(Gtk.Window):
    """
    Main application window for the speech-to-text transcriber.
    """
    
    def __init__(
        self,
        config: ConfigManager,
        on_start: Optional[Callable[[], None]] = None,
        on_stop: Optional[Callable[[], None]] = None,
        on_settings_change: Optional[Callable[[], None]] = None,
    ):
        """Initialize the main window."""
        super().__init__(title="Voice Transcriber")
        
        self._config = config
        self._on_start = on_start
        self._on_stop = on_stop
        self._on_settings_change_cb = on_settings_change
        self._is_listening = False
        
        self._setup_window()
        self._apply_styles()
        self._setup_ui()
        self._load_initial_settings()
        
    def _setup_window(self) -> None:
        """Configure window properties."""
        w = self._config.get("window_width")
        h = self._config.get("window_height")
        self.set_default_size(w, h)
        self.set_border_width(0)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_resizable(True)
        self.connect("destroy", Gtk.main_quit)
        
    def _apply_styles(self) -> None:
        """Apply CSS styles."""
        css = b"""
        window { background: linear-gradient(180deg, #0f0f1a 0%, #1a1a2e 100%); }
        .header-bar { background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); padding: 10px 16px; }
        .content-box { background: transparent; padding: 20px; }
        
        .listen-btn {
            background: linear-gradient(135deg, #00d2ff 0%, #3a7bd5 100%);
            color: white; font-weight: bold; padding: 12px 32px; border-radius: 50px; border: none;
            box-shadow: 0 4px 15px rgba(0, 210, 255, 0.4);
        }
        .listen-btn:hover { background: linear-gradient(135deg, #00e5ff 0%, #4a8be5 100%); }
        .listen-btn.recording {
            background: linear-gradient(135deg, #ff416c 0%, #ff4b2b 100%);
            box-shadow: 0 4px 15px rgba(255, 65, 108, 0.4);
        }
        
        .status-box { background: rgba(255, 255, 255, 0.05); border-radius: 12px; padding: 8px 16px; margin: 12px 0; }
        .status-text { color: #9ca3af; font-size: 13px; }
        .status-text.active { color: #10b981; }
        .status-text.error { color: #ef4444; }
        
        .transcript-frame { background: rgba(255, 255, 255, 0.03); border-radius: 12px; }
        .transcript-view { background: transparent; color: #e5e7eb; font-family: sans-serif; padding: 16px; }
        
        .icon-btn { background: transparent; border: none; color: white; padding: 8px; border-radius: 50%; }
        .icon-btn:hover { background: rgba(255,255,255,0.2); }
        
        .settings-popover { background: #1a1a2e; color: white; padding: 16px; border: 1px solid #333; }
        .settings-label { color: #bccbd6; font-weight: bold; margin-bottom: 4px; }
        """
        style_provider = Gtk.CssProvider()
        style_provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), style_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
        
    def _setup_ui(self) -> None:
        """Build the UI components."""
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.add(main_box)
        
        # === Header ===
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        header.get_style_context().add_class("header-bar")
        main_box.pack_start(header, False, False, 0)
        
        # Title
        title_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        header.pack_start(title_box, True, True, 0)
        title_box.pack_start(Gtk.Label(label="🎙"), False, False, 0)
        title_box.pack_start(Gtk.Label(label="Voice Transcriber Pro"), False, False, 0)
        
        # Header Buttons (Save, Settings)
        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        header.pack_end(btn_box, False, False, 0)
        
        save_btn = Gtk.Button(label="💾")
        save_btn.get_style_context().add_class("icon-btn")
        save_btn.set_tooltip_text("Save Transcript")
        save_btn.connect("clicked", self._on_save_clicked)
        btn_box.pack_start(save_btn, False, False, 0)
        
        settings_btn = Gtk.Button(label="⚙️")
        settings_btn.get_style_context().add_class("icon-btn")
        settings_btn.set_tooltip_text("Settings")
        settings_btn.connect("clicked", self._on_settings_clicked)
        btn_box.pack_start(settings_btn, False, False, 0)
        
        # === Content ===
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        content.get_style_context().add_class("content-box")
        main_box.pack_start(content, True, True, 0)
        
        # Listen Button
        btn_wrap = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        btn_wrap.set_halign(Gtk.Align.CENTER)
        content.pack_start(btn_wrap, False, False, 0)
        
        self._listen_button = Gtk.Button(label="▶ Start Listening")
        self._listen_button.get_style_context().add_class("listen-btn")
        self._listen_button.connect("clicked", self._on_listen_clicked)
        btn_wrap.pack_start(self._listen_button, False, False, 0)
        
        # Status
        status_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        status_box.get_style_context().add_class("status-box")
        status_box.set_halign(Gtk.Align.CENTER)
        content.pack_start(status_box, False, False, 0)
        
        self._status_label = Gtk.Label(label="Ready to transcribe")
        self._status_label.get_style_context().add_class("status-text")
        status_box.pack_start(self._status_label, False, False, 0)
        
        # Transcript
        frame = Gtk.Frame()
        frame.get_style_context().add_class("transcript-frame")
        content.pack_start(frame, True, True, 0)
        
        scrolled = Gtk.ScrolledWindow()
        frame.add(scrolled)
        
        self._text_view = Gtk.TextView()
        self._text_view.get_style_context().add_class("transcript-view")
        self._text_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self._text_view.set_editable(False)
        self._text_view.set_cursor_visible(False)
        self._text_view.set_left_margin(16)
        self._text_view.set_right_margin(16)
        self._text_view.set_top_margin(16)
        self._text_view.set_bottom_margin(16)
        self._text_buffer = self._text_view.get_buffer()
        self._text_buffer.set_text("Your transcription will appear here...")
        scrolled.add(self._text_view)
        
        # Bottom Controls
        controls = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        main_box.pack_start(controls, False, False, 12)
        controls.set_margin_start(20)
        controls.set_margin_end(20)
        controls.set_margin_bottom(12)
        
        # Sticky
        sticky_box = Gtk.Box(spacing=8)
        controls.pack_start(sticky_box, False, False, 0)
        sticky_box.pack_start(Gtk.Label(label="📌 Stay on top"), False, False, 0)
        self._sticky_switch = Gtk.Switch()
        self._sticky_switch.set_active(self._config.get("sticky_mode"))
        self._sticky_switch.connect("state-set", self._on_sticky_toggled)
        sticky_box.pack_start(self._sticky_switch, False, False, 0)
        
        # Copy & Clear
        controls.pack_start(Gtk.Box(), True, True, 0) # Spacer
        
        copy_btn = Gtk.Button(label="Copy")
        copy_btn.connect("clicked", self._on_copy_clicked)
        controls.pack_end(copy_btn, False, False, 0)
        
        clear_btn = Gtk.Button(label="Clear")
        clear_btn.connect("clicked", self._on_clear_clicked)
        controls.pack_end(clear_btn, False, False, 8)

        # Initialize Settings Popover
        self._init_settings_popover(settings_btn)

    def _init_settings_popover(self, parent_btn):
        """Create the settings popover."""
        self._popover = Gtk.Popover()
        self._popover.set_relative_to(parent_btn)
        self._popover.set_position(Gtk.PositionType.BOTTOM)
        
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.set_margin_top(12)
        box.set_margin_bottom(12)
        box.set_margin_start(12)
        box.set_margin_end(12)
        self._popover.add(box)
        
        # API Key
        box.pack_start(Gtk.Label(label="Groq API Key:", xalign=0), False, False, 0)
        self._api_entry = Gtk.Entry()
        self._api_entry.set_text(self._config.get("api_key") or "")
        self._api_entry.set_visibility(False) # Hide characters
        self._api_entry.set_width_chars(25)
        self._api_entry.connect("changed", self._on_config_changed)
        box.pack_start(self._api_entry, False, False, 0)
        
        # Language
        box.pack_start(Gtk.Label(label="Language:", xalign=0), False, False, 0)
        self._lang_combo = Gtk.ComboBoxText()
        languages = [("auto", "Auto Detect"), ("en", "English"), ("fr", "French"), 
                     ("es", "Spanish"), ("de", "German"), ("it", "Italian"), 
                     ("pt", "Portuguese"), ("ar", "Arabic"), ("zh", "Chinese")]
        for code, name in languages:
            self._lang_combo.append(code, name)
        self._lang_combo.set_active_id(self._config.get("language"))
        self._lang_combo.connect("changed", self._on_config_changed)
        box.pack_start(self._lang_combo, False, False, 0)
        
        # Translation Toggle
        trans_box = Gtk.Box(spacing=8)
        trans_box.pack_start(Gtk.Label(label="Translate to English"), False, False, 0)
        self._trans_switch = Gtk.Switch()
        self._trans_switch.set_active(self._config.get("translate_to_english"))
        self._trans_switch.connect("state-set", lambda s, st: self._on_config_changed(s) or False)
        trans_box.pack_end(self._trans_switch, False, False, 0)
        box.pack_start(trans_box, False, False, 0)
        
        # Font Size
        fs_box = Gtk.Box(spacing=8)
        fs_box.pack_start(Gtk.Label(label="Font Size:"), False, False, 0)
        self._font_scale = Gtk.SpinButton.new_with_range(12, 32, 1)
        self._font_scale.set_value(self._config.get("font_size"))
        self._font_scale.connect("value-changed", self._on_appearance_changed)
        fs_box.pack_end(self._font_scale, False, False, 0)
        box.pack_start(fs_box, False, False, 0)
        
        # Opacity
        op_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        op_box.pack_start(Gtk.Label(label="Window Opacity:", xalign=0), False, False, 0)
        self._opacity_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0.5, 1.0, 0.05)
        self._opacity_scale.set_value(self._config.get("opacity"))
        self._opacity_scale.connect("value-changed", self._on_appearance_changed)
        op_box.pack_start(self._opacity_scale, False, False, 0)
        box.pack_start(op_box, False, False, 0)
        
        box.show_all()

    def _load_initial_settings(self):
        """Apply startup settings."""
        self._update_font_size(self._config.get("font_size"))
        self.set_opacity(self._config.get("opacity"))
        if self._config.get("sticky_mode"):
            self.set_keep_above(True)

    def _on_config_changed(self, widget):
        """Handle config changes (API, Lang, Task)."""
        api_key = self._api_entry.get_text()
        lang = self._lang_combo.get_active_id()
        translate = self._trans_switch.get_active()
        
        self._config.set("api_key", api_key)
        self._config.set("language", lang)
        self._config.set("translate_to_english", translate)
        
        if self._on_settings_change_cb:
            self._on_settings_change_cb()

    def _on_appearance_changed(self, widget):
        """Handle visual settings changes."""
        font_size = int(self._font_scale.get_value())
        opacity = self._opacity_scale.get_value()
        
        self._config.set("font_size", font_size)
        self._config.set("opacity", opacity)
        
        self._update_font_size(font_size)
        self.set_opacity(opacity)

    def _update_font_size(self, size):
        """Determine proper CSS for font size update."""
        # GTK3 CSS provider for font size update
        css = f".transcript-view {{ font-size: {size}px; }}"
        provider = Gtk.CssProvider()
        provider.load_from_data(css.encode())
        context = self._text_view.get_style_context()
        Gtk.StyleContext.add_provider(context, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

    def _on_settings_clicked(self, btn):
        if self._popover.is_visible():
            self._popover.popdown()
        else:
            self._popover.popup()

    def _on_save_clicked(self, btn):
        dialog = Gtk.FileChooserDialog(
            title="Save Transcript", parent=self, action=Gtk.FileChooserAction.SAVE
        )
        dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_SAVE, Gtk.ResponseType.ACCEPT)
        
        now = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
        dialog.set_current_name(f"transcript_{now}.txt")
        
        if dialog.run() == Gtk.ResponseType.ACCEPT:
            filename = dialog.get_filename()
            start, end = self._text_buffer.get_bounds()
            text = self._text_buffer.get_text(start, end, True)
            try:
                with open(filename, 'w') as f:
                    f.write(text)
                self.set_status(f"Saved to {filename}", "active")
            except Exception as e:
                self.show_error(str(e))
        dialog.destroy()
        
    def _on_listen_clicked(self, btn):
        if self._is_listening:
            self.stop_listening()
        else:
            self.start_listening()
            
    def start_listening(self):
        self._is_listening = True
        self._listen_button.set_label("⏹ Stop Listening")
        self._listen_button.get_style_context().add_class("recording")
        self.set_status("Listening...", "active")
        
        start, end = self._text_buffer.get_bounds()
        if self._text_buffer.get_text(start, end, True) == "Your transcription will appear here...":
            self._text_buffer.set_text("")
        if self._on_start: self._on_start()

    def stop_listening(self):
        self._is_listening = False
        self._listen_button.set_label("▶ Start Listening")
        self._listen_button.get_style_context().remove_class("recording")
        self.set_status("Ready", "")
        if self._on_stop: self._on_stop()

    def _on_sticky_toggled(self, switch, state):
        self.set_keep_above(state)
        self._config.set("sticky_mode", state)
        return False

    def _on_copy_clicked(self, btn):
        start, end = self._text_buffer.get_bounds()
        text = self._text_buffer.get_text(start, end, True)
        clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        clipboard.set_text(text, -1)
        self.set_status("Copied!", "active")

    def _on_clear_clicked(self, btn):
        self._text_buffer.set_text("")

    def set_status(self, msg, cls=""):
        GLib.idle_add(lambda: self._do_status(msg, cls))

    def _do_status(self, msg, cls):
        self._status_label.set_text(msg)
        ctx = self._status_label.get_style_context()
        for c in ["active", "error"]: ctx.remove_class(c)
        if cls: ctx.add_class(cls)
        return False
        
    def append_text(self, text):
        GLib.idle_add(lambda: self._do_append(text))
        
    def _do_append(self, text):
        buf = self._text_buffer
        end = buf.get_end_iter()
        if buf.get_char_count() > 0: buf.insert(end, " ")
        buf.insert(buf.get_end_iter(), text)
        self._text_view.scroll_to_iter(buf.get_end_iter(), 0, False, 0, 0)
        return False
        
    def show_error(self, msg):
        self.set_status(f"Error: {msg}", "error")
