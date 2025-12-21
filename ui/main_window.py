"""Main application window with GTK3 - Cohesive Modern Theme."""

import os
import sys
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib
from typing import Callable, Optional
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
        
        # Set Application Icon
        try:
            # Determine path to resources
            if getattr(sys, 'frozen', False):
                base_path = sys._MEIPASS
            else:
                base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            
            icon_path = os.path.join(base_path, "resources", "icon.svg")
            if os.path.exists(icon_path):
                self.set_icon_from_file(icon_path)
            else:
                print(f"Icon not found at: {icon_path}")
        except Exception as e:
            print(f"Failed to set icon: {e}")
        
    def _apply_styles(self) -> None:
        """Apply CSS styles with a cohesive palette."""
        # Palette:
        # BG: #1F1F24 (Deep Gray)
        # Header: #151518 (Darker)
        # Accent: #0A84FF (iOS Blue)
        # Text: #F2F2F7 (Whiteish)
        # Subtext: #8E8E93 (Gray)
        
        css = b"""
        /* Global Reset */
        window { 
            background-color: #1F1F24; 
            color: #F2F2F7;
        }
        
        /* Header */
        .header-bar { 
            background-color: #151518;
            border-bottom: 1px solid #2C2C2E;
            padding: 12px 16px; 
        }
        
        /* Content Area */
        .content-box { 
            padding: 24px 32px; 
        }
        
        /* Listen Button (Hero) */
        .listen-btn {
            background-image: linear-gradient(to bottom, #0A84FF, #0077ED);
            color: white; 
            font-weight: bold; 
            font-size: 16px;
            padding: 14px 40px; 
            border-radius: 12px; 
            border: 1px solid #0062C4;
            box-shadow: 0 2px 8px rgba(10, 132, 255, 0.3);
            transition: all 0.2s ease;
        }
        .listen-btn:hover { 
            background-image: linear-gradient(to bottom, #2491FF, #0A84FF);
            box-shadow: 0 4px 12px rgba(10, 132, 255, 0.4);
        }
        .listen-btn:active {
            background-image: none;
            background-color: #0062C4;
        }
        
        .listen-btn.recording {
            background-image: linear-gradient(to bottom, #FF453A, #FF3B30);
            border: 1px solid #D70015;
            box-shadow: 0 0 15px rgba(255, 69, 58, 0.5);
            text-shadow: 0 1px 2px rgba(0,0,0,0.2);
        }
        
        /* Status Banner */
        .status-box { 
            background-color: #2C2C2E; 
            border-radius: 8px; 
            padding: 8px 16px; 
            margin-top: 20px;
            margin-bottom: 0;
        }
        .status-text { 
            color: #AEAEB2; 
            font-size: 13px; 
            font-weight: 500;
        }
        .status-text.active { color: #30D158; } /* Green */
        .status-text.error { color: #FF453A; } /* Red */
        
        /* Transcript Area */
        .transcript-frame { 
            background-color: #252529; 
            border: 1px solid #3A3A3C;
            border-radius: 12px; 
            margin-top: 16px;
        }
        .transcript-view { 
            background-color: transparent; 
            color: #F2F2F7; 
            font-family: 'Inter', sans-serif;
            caret-color: #0A84FF;
            padding: 16px;
        }
        
        /* Header Buttons */
        .icon-btn { 
            background-image: none;
            background-color: transparent; 
            border: none; 
            color: #0A84FF; 
            padding: 8px; 
            border-radius: 8px; 
            box-shadow: none;
            min-width: 32px;
            min-height: 32px;
        }
        .icon-btn:hover { 
            background-color: #2C2C2E; 
        }
        
        /* Secondary Action Buttons (Clear, Copy) */
        .secondary-btn {
            background-image: none;
            background-color: #3A3A3C;
            color: white;
            border: 1px solid #48484A;
            font-size: 13px;
            padding: 8px 20px;
            border-radius: 8px;
            font-weight: 600;
        }
        .secondary-btn:hover {
            background-color: #48484A;
            border-color: #5A5A5C;
        }
        
        /* Settings Popover */
        .settings-popover { 
            background-color: #2C2C2E; 
            color: #F2F2F7; 
            border: 1px solid #3A3A3C; 
            padding: 16px;
            border-radius: 12px;
        }
        .settings-label { 
            color: #AEAEB2; 
            font-weight: 600; 
            font-size: 13px;
            margin-bottom: 4px; 
        }
        
        /* Inputs */
        entry, combobox {
            background-color: #1C1C1E;
            border: 1px solid #3A3A3C;
            color: white;
            border-radius: 6px;
            padding: 4px;
        }
        
        switch slider {
            background: #EBEBF5;
        }
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
        title_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        title_box.set_valign(Gtk.Align.CENTER)
        header.pack_start(title_box, True, True, 0)
        
        # We can use the icon from file for navbar, but here keep text clean
        title_lbl = Gtk.Label()
        title_lbl.set_markup("<span font_weight='800' size='14000' color='white'>Transcriber</span>")
        title_box.pack_start(title_lbl, False, False, 0)
        
        # Header Buttons (Save, Settings)
        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
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
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        content.get_style_context().add_class("content-box")
        main_box.pack_start(content, True, True, 0)
        
        # Listen Button Flow
        btn_wrap = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        btn_wrap.set_halign(Gtk.Align.CENTER)
        content.pack_start(btn_wrap, False, False, 0)
        
        self._listen_button = Gtk.Button(label="▶ Start Transcription")
        self._listen_button.get_style_context().add_class("listen-btn")
        self._listen_button.connect("clicked", self._on_listen_clicked)
        btn_wrap.pack_start(self._listen_button, False, False, 0)
        
        # Status (Compact)
        status_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        status_box.get_style_context().add_class("status-box")
        status_box.set_halign(Gtk.Align.CENTER)
        content.pack_start(status_box, False, False, 0)
        
        self._status_label = Gtk.Label(label="Initialised and ready")
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
        self._text_view.set_left_margin(8)
        self._text_view.set_right_margin(8)
        self._text_view.set_top_margin(8)
        self._text_view.set_bottom_margin(8)
        self._text_buffer = self._text_view.get_buffer()
        self._text_buffer.set_text("")
        scrolled.add(self._text_view)
        
        # Bottom Controls
        controls = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        controls.set_margin_top(16)
        content.pack_start(controls, False, False, 0)
        
        # Sticky
        sticky_box = Gtk.Box(spacing=8)
        lbl = Gtk.Label(label="Top")
        lbl.get_style_context().add_class("status-text") # reuse style
        sticky_box.pack_start(lbl, False, False, 0)
        self._sticky_switch = Gtk.Switch()
        self._sticky_switch.set_active(self._config.get("sticky_mode"))
        self._sticky_switch.connect("state-set", self._on_sticky_toggled)
        sticky_box.pack_start(self._sticky_switch, False, False, 0)
        controls.pack_start(sticky_box, False, False, 0)
        
        # Spacer
        controls.pack_start(Gtk.Box(), True, True, 0) 
        
        # Action Buttons
        copy_btn = Gtk.Button(label="Copy")
        copy_btn.get_style_context().add_class("secondary-btn")
        copy_btn.connect("clicked", self._on_copy_clicked)
        controls.pack_end(copy_btn, False, False, 0)
        
        clear_btn = Gtk.Button(label="Clear")
        clear_btn.get_style_context().add_class("secondary-btn")
        clear_btn.connect("clicked", self._on_clear_clicked)
        controls.pack_end(clear_btn, False, False, 8)

        # Initialize Settings Popover
        self._init_settings_popover(settings_btn)

    def _init_settings_popover(self, parent_btn):
        """Create the settings popover."""
        self._popover = Gtk.Popover()
        self._popover.set_relative_to(parent_btn)
        self._popover.set_position(Gtk.PositionType.BOTTOM)
        self._popover.get_style_context().add_class("settings-popover")
        
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        box.set_margin_top(8)
        box.set_margin_bottom(8)
        box.set_margin_start(8)
        box.set_margin_end(8)
        self._popover.add(box)
        
        # Header
        box.pack_start(Gtk.Label(label="Preferences", xalign=0), False, False, 0)
        
        # API Key
        row_api = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        row_api.pack_start(Gtk.Label(label="Groq API Key", xalign=0, name="settings-label"), False, False, 0)
        self._api_entry = Gtk.Entry()
        self._api_entry.set_text(self._config.get("api_key") or "")
        self._api_entry.set_visibility(False)
        self._api_entry.set_width_chars(25)
        self._api_entry.set_placeholder_text("gsk_...")
        self._api_entry.connect("changed", self._on_config_changed)
        row_api.pack_start(self._api_entry, False, False, 0)
        box.pack_start(row_api, False, False, 0)
        
        # Language
        row_lang = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        row_lang.pack_start(Gtk.Label(label="Language", xalign=0, name="settings-label"), False, False, 0)
        self._lang_combo = Gtk.ComboBoxText()
        languages = [("auto", "Auto Detect"), ("en", "English"), ("fr", "French"), 
                     ("es", "Spanish"), ("de", "German"), ("it", "Italian"), 
                     ("pt", "Portuguese"), ("ar", "Arabic"), ("zh", "Chinese")]
        for code, name in languages:
            self._lang_combo.append(code, name)
        self._lang_combo.set_active_id(self._config.get("language"))
        self._lang_combo.connect("changed", self._on_config_changed)
        row_lang.pack_start(self._lang_combo, False, False, 0)
        box.pack_start(row_lang, False, False, 0)
        
        # Translation Toggle
        row_trans = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)
        row_trans.pack_start(Gtk.Label(label="Translate to English", xalign=0), True, True, 0)
        self._trans_switch = Gtk.Switch()
        self._trans_switch.set_active(self._config.get("translate_to_english"))
        self._trans_switch.connect("state-set", lambda s, st: self._on_config_changed(s) or False)
        row_trans.pack_start(self._trans_switch, False, False, 0)
        box.pack_start(row_trans, False, False, 0)
        
        # Font Size
        row_font = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)
        row_font.pack_start(Gtk.Label(label="Font Size", xalign=0), True, True, 0)
        self._font_scale = Gtk.SpinButton.new_with_range(12, 32, 1)
        self._font_scale.set_value(self._config.get("font_size"))
        self._font_scale.connect("value-changed", self._on_appearance_changed)
        row_font.pack_start(self._font_scale, False, False, 0)
        box.pack_start(row_font, False, False, 0)
        
        # Opacity
        row_op = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        row_op.pack_start(Gtk.Label(label="Opacity", xalign=0), False, False, 0)
        self._opacity_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0.5, 1.0, 0.05)
        self._opacity_scale.set_value(self._config.get("opacity"))
        self._opacity_scale.connect("value-changed", self._on_appearance_changed)
        row_op.pack_start(self._opacity_scale, False, False, 0)
        box.pack_start(row_op, False, False, 0)
        
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
                self.set_status(f"Saved to {os.path.basename(filename)}", "active")
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
        self._listen_button.set_label("⏹ Stop")
        self._listen_button.get_style_context().add_class("recording")
        self.set_status("Listening...", "active")
        
        start, end = self._text_buffer.get_bounds()
        text = self._text_buffer.get_text(start, end, True)
        if text.strip() == "Your transcription will appear here...":
            self._text_buffer.set_text("")
            
        if self._on_start: self._on_start()

    def stop_listening(self):
        self._is_listening = False
        self._listen_button.set_label("▶ Start Transcription")
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
        GLib.timeout_add(1500, lambda: self.set_status("Ready") or False)

    def _on_clear_clicked(self, btn):
        self._text_buffer.set_text("")
        self.set_status("Cleared")

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
