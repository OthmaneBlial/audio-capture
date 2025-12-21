"""Main application window with GTK3."""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib, Pango
from typing import Callable, Optional


class MainWindow(Gtk.Window):
    """
    Main application window for the speech-to-text transcriber.
    
    Features:
    - Live transcription display with auto-scroll
    - Start/Stop listening toggle
    - Always-on-top (sticky) mode toggle
    - Status indicator
    - Minimal, clean design
    """
    
    def __init__(
        self,
        on_start: Optional[Callable[[], None]] = None,
        on_stop: Optional[Callable[[], None]] = None,
    ):
        """
        Initialize the main window.
        
        Args:
            on_start: Callback when listening starts
            on_stop: Callback when listening stops
        """
        super().__init__(title="🎤 Voice Transcriber")
        
        self._on_start = on_start
        self._on_stop = on_stop
        self._is_listening = False
        
        self._setup_window()
        self._setup_ui()
        self._apply_styles()
        
    def _setup_window(self) -> None:
        """Configure window properties."""
        self.set_default_size(400, 300)
        self.set_border_width(10)
        self.set_position(Gtk.WindowPosition.CENTER)
        
        # Enable close button
        self.connect("destroy", Gtk.main_quit)
        
    def _setup_ui(self) -> None:
        """Build the UI components."""
        # Main vertical box
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.add(main_box)
        
        # Header with controls
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        main_box.pack_start(header_box, False, False, 0)
        
        # Start/Stop button
        self._listen_button = Gtk.Button(label="▶ Start Listening")
        self._listen_button.connect("clicked", self._on_listen_clicked)
        self._listen_button.get_style_context().add_class("listen-button")
        header_box.pack_start(self._listen_button, True, True, 0)
        
        # Sticky mode toggle
        sticky_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        sticky_label = Gtk.Label(label="📌 Sticky")
        self._sticky_switch = Gtk.Switch()
        self._sticky_switch.connect("state-set", self._on_sticky_toggled)
        sticky_box.pack_start(sticky_label, False, False, 0)
        sticky_box.pack_start(self._sticky_switch, False, False, 0)
        header_box.pack_end(sticky_box, False, False, 0)
        
        # Status indicator
        self._status_label = Gtk.Label(label="Ready")
        self._status_label.get_style_context().add_class("status-label")
        main_box.pack_start(self._status_label, False, False, 0)
        
        # Transcription display
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled_window.set_min_content_height(200)
        main_box.pack_start(scrolled_window, True, True, 0)
        
        self._text_view = Gtk.TextView()
        self._text_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self._text_view.set_editable(False)
        self._text_view.set_cursor_visible(False)
        self._text_view.set_left_margin(10)
        self._text_view.set_right_margin(10)
        self._text_view.set_top_margin(10)
        self._text_view.set_bottom_margin(10)
        self._text_buffer = self._text_view.get_buffer()
        scrolled_window.add(self._text_view)
        
        # Clear button
        clear_button = Gtk.Button(label="🗑 Clear")
        clear_button.connect("clicked", self._on_clear_clicked)
        main_box.pack_start(clear_button, False, False, 0)
        
    def _apply_styles(self) -> None:
        """Apply CSS styles to the window."""
        css = b"""
        window {
            background-color: #1e1e2e;
        }
        
        .listen-button {
            background-color: #89b4fa;
            color: #1e1e2e;
            font-weight: bold;
            padding: 10px 20px;
            border-radius: 8px;
        }
        
        .listen-button:hover {
            background-color: #74c7ec;
        }
        
        .listen-button.listening {
            background-color: #f38ba8;
        }
        
        .listen-button.listening:hover {
            background-color: #eba0ac;
        }
        
        .status-label {
            color: #a6adc8;
            font-size: 12px;
        }
        
        .status-label.listening {
            color: #a6e3a1;
        }
        
        .status-label.error {
            color: #f38ba8;
        }
        
        textview {
            background-color: #313244;
            color: #cdd6f4;
            font-family: monospace;
            font-size: 14px;
            border-radius: 8px;
        }
        
        textview text {
            background-color: #313244;
            color: #cdd6f4;
        }
        
        button {
            background-color: #45475a;
            color: #cdd6f4;
            border: none;
            border-radius: 6px;
            padding: 8px 16px;
        }
        
        button:hover {
            background-color: #585b70;
        }
        
        switch {
            background-color: #45475a;
            border-radius: 12px;
        }
        
        switch:checked {
            background-color: #89b4fa;
        }
        
        label {
            color: #cdd6f4;
        }
        """
        
        style_provider = Gtk.CssProvider()
        style_provider.load_from_data(css)
        
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            style_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
        
    def _on_listen_clicked(self, button: Gtk.Button) -> None:
        """Handle listen button click."""
        if self._is_listening:
            self.stop_listening()
        else:
            self.start_listening()
            
    def _on_sticky_toggled(self, switch: Gtk.Switch, state: bool) -> bool:
        """Handle sticky mode toggle."""
        self.set_keep_above(state)
        return False
        
    def _on_clear_clicked(self, button: Gtk.Button) -> None:
        """Clear the transcription text."""
        self._text_buffer.set_text("")
        
    def start_listening(self) -> None:
        """Start listening mode."""
        self._is_listening = True
        self._listen_button.set_label("⏹ Stop Listening")
        self._listen_button.get_style_context().add_class("listening")
        self.set_status("🎤 Listening...", "listening")
        
        if self._on_start:
            self._on_start()
            
    def stop_listening(self) -> None:
        """Stop listening mode."""
        self._is_listening = False
        self._listen_button.set_label("▶ Start Listening")
        self._listen_button.get_style_context().remove_class("listening")
        self.set_status("Ready", "")
        
        if self._on_stop:
            self._on_stop()
            
    def append_text(self, text: str) -> None:
        """
        Append transcribed text to the display.
        
        Thread-safe: can be called from any thread.
        
        Args:
            text: Text to append
        """
        def do_append():
            end_iter = self._text_buffer.get_end_iter()
            
            # Add space or newline if there's existing text
            if self._text_buffer.get_char_count() > 0:
                self._text_buffer.insert(end_iter, " ")
                end_iter = self._text_buffer.get_end_iter()
            
            self._text_buffer.insert(end_iter, text)
            
            # Auto-scroll to bottom
            end_iter = self._text_buffer.get_end_iter()
            self._text_view.scroll_to_iter(end_iter, 0.0, False, 0.0, 0.0)
            
            return False
            
        GLib.idle_add(do_append)
        
    def set_status(self, message: str, status_class: str = "") -> None:
        """
        Update the status label.
        
        Thread-safe: can be called from any thread.
        
        Args:
            message: Status message
            status_class: CSS class for styling ("listening", "error", or "")
        """
        def do_update():
            self._status_label.set_text(message)
            
            # Update style class
            context = self._status_label.get_style_context()
            context.remove_class("listening")
            context.remove_class("error")
            
            if status_class:
                context.add_class(status_class)
                
            return False
            
        GLib.idle_add(do_update)
        
    def show_error(self, message: str) -> None:
        """
        Show an error message.
        
        Args:
            message: Error message
        """
        self.set_status(f"❌ {message}", "error")
        
    @property
    def is_listening(self) -> bool:
        """Check if currently listening."""
        return self._is_listening
