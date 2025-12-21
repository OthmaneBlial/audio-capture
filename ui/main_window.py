"""Main application window with GTK3 - Modern Dark Theme."""

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
    - Status indicator with visual feedback
    - Premium dark theme design
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
        super().__init__(title="Voice Transcriber")
        
        self._on_start = on_start
        self._on_stop = on_stop
        self._is_listening = False
        
        self._setup_window()
        self._apply_styles()
        self._setup_ui()
        
    def _setup_window(self) -> None:
        """Configure window properties."""
        self.set_default_size(480, 400)
        self.set_border_width(0)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_resizable(True)
        
        # Enable close button
        self.connect("destroy", Gtk.main_quit)
        
    def _apply_styles(self) -> None:
        """Apply CSS styles to the window."""
        css = b"""
        /* Main window */
        window {
            background: linear-gradient(180deg, #0f0f1a 0%, #1a1a2e 100%);
        }
        
        /* Header bar */
        .header-bar {
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            padding: 16px 20px;
            border-radius: 0;
        }
        
        .header-title {
            color: white;
            font-size: 18px;
            font-weight: bold;
            text-shadow: 0 1px 2px rgba(0,0,0,0.3);
        }
        
        /* Main content area */
        .content-box {
            background: transparent;
            padding: 20px;
        }
        
        /* Listen button */
        .listen-btn {
            background: linear-gradient(135deg, #00d2ff 0%, #3a7bd5 100%);
            color: white;
            font-size: 16px;
            font-weight: bold;
            padding: 14px 32px;
            border-radius: 50px;
            border: none;
            box-shadow: 0 4px 15px rgba(0, 210, 255, 0.4);
            transition: all 0.3s ease;
        }
        
        .listen-btn:hover {
            background: linear-gradient(135deg, #00e5ff 0%, #4a8be5 100%);
            box-shadow: 0 6px 20px rgba(0, 210, 255, 0.5);
        }
        
        .listen-btn.recording {
            background: linear-gradient(135deg, #ff416c 0%, #ff4b2b 100%);
            box-shadow: 0 4px 15px rgba(255, 65, 108, 0.4);
        }

        
        /* Status indicator */
        .status-box {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 12px;
            padding: 12px 20px;
            margin: 16px 0;
        }
        
        .status-icon {
            color: #6b7280;
            font-size: 20px;
        }
        
        .status-icon.active {
            color: #10b981;
        }
        
        .status-icon.error {
            color: #ef4444;
        }
        
        .status-text {
            color: #9ca3af;
            font-size: 14px;
        }
        
        .status-text.active {
            color: #10b981;
        }
        
        /* Transcript area */
        .transcript-frame {
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 16px;
            padding: 0;
        }
        
        .transcript-view {
            background: transparent;
            color: #e5e7eb;
            font-family: 'Inter', 'SF Pro Display', -apple-system, sans-serif;
            font-size: 17px;
            padding: 16px;
        }
        
        .transcript-view text {
            background: transparent;
            color: #e5e7eb;
        }
        
        /* Bottom controls */
        .controls-box {
            background: rgba(255, 255, 255, 0.03);
            border-top: 1px solid rgba(255, 255, 255, 0.1);
            padding: 12px 20px;
        }
        
        /* Sticky toggle */
        .sticky-box {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 20px;
            padding: 6px 12px;
        }
        
        .sticky-label {
            color: #9ca3af;
            font-size: 13px;
        }
        
        switch {
            background: #374151;
            border-radius: 14px;
            min-width: 44px;
            min-height: 24px;
        }
        
        switch:checked {
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        }
        
        switch slider {
            background: white;
            border-radius: 12px;
            min-width: 20px;
            min-height: 20px;
            margin: 2px;
        }
        
        /* Clear button */
        .clear-btn {
            background: rgba(255, 255, 255, 0.1);
            color: #9ca3af;
            font-size: 13px;
            padding: 8px 16px;
            border-radius: 8px;
            border: none;
        }
        
        .clear-btn:hover {
            background: rgba(255, 255, 255, 0.15);
            color: #e5e7eb;
        }
        
        /* Scrollbar styling */
        scrollbar {
            background: transparent;
        }
        
        scrollbar slider {
            background: rgba(255, 255, 255, 0.2);
            border-radius: 4px;
            min-width: 8px;
        }
        
        scrollbar slider:hover {
            background: rgba(255, 255, 255, 0.3);
        }
        """
        
        style_provider = Gtk.CssProvider()
        style_provider.load_from_data(css)
        
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            style_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
        
    def _setup_ui(self) -> None:
        """Build the UI components."""
        # Main vertical container
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.add(main_box)
        
        # === Header Bar ===
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        header.get_style_context().add_class("header-bar")
        main_box.pack_start(header, False, False, 0)
        
        # App icon and title
        title_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        header.pack_start(title_box, True, True, 0)
        
        mic_icon = Gtk.Label(label="🎙")
        mic_icon.set_markup("<span size='x-large'>🎙</span>")
        title_box.pack_start(mic_icon, False, False, 0)
        
        title = Gtk.Label()
        title.set_markup("<span font_weight='bold' size='large' color='white'>Voice Transcriber</span>")
        title_box.pack_start(title, False, False, 0)
        
        # === Content Area ===
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        content.get_style_context().add_class("content-box")
        main_box.pack_start(content, True, True, 0)
        
        # Listen button (centered)
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        button_box.set_halign(Gtk.Align.CENTER)
        content.pack_start(button_box, False, False, 8)
        
        self._listen_button = Gtk.Button()
        self._listen_button.get_style_context().add_class("listen-btn")
        self._update_button_label()
        self._listen_button.connect("clicked", self._on_listen_clicked)
        button_box.pack_start(self._listen_button, False, False, 0)
        
        # Status indicator
        status_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        status_box.get_style_context().add_class("status-box")
        status_box.set_halign(Gtk.Align.CENTER)
        content.pack_start(status_box, False, False, 0)
        
        self._status_icon = Gtk.Label(label="●")
        self._status_icon.get_style_context().add_class("status-icon")
        status_box.pack_start(self._status_icon, False, False, 0)
        
        self._status_label = Gtk.Label(label="Ready to transcribe")
        self._status_label.get_style_context().add_class("status-text")
        status_box.pack_start(self._status_label, False, False, 0)
        
        # Transcript area
        transcript_frame = Gtk.Frame()
        transcript_frame.get_style_context().add_class("transcript-frame")
        transcript_frame.set_shadow_type(Gtk.ShadowType.NONE)
        content.pack_start(transcript_frame, True, True, 0)
        
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        transcript_frame.add(scrolled)
        
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
        scrolled.add(self._text_view)
        
        # Placeholder text
        self._text_buffer.set_text("Your transcription will appear here...")
        
        # === Bottom Controls ===
        controls = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        controls.get_style_context().add_class("controls-box")
        main_box.pack_start(controls, False, False, 0)
        
        # Sticky toggle
        sticky_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        sticky_box.get_style_context().add_class("sticky-box")
        controls.pack_start(sticky_box, False, False, 0)
        
        pin_icon = Gtk.Label(label="📌")
        sticky_box.pack_start(pin_icon, False, False, 0)
        
        sticky_label = Gtk.Label(label="Stay on top")
        sticky_label.get_style_context().add_class("sticky-label")
        sticky_box.pack_start(sticky_label, False, False, 0)
        
        self._sticky_switch = Gtk.Switch()
        self._sticky_switch.connect("state-set", self._on_sticky_toggled)
        sticky_box.pack_start(self._sticky_switch, False, False, 0)
        
        # Spacer
        controls.pack_start(Gtk.Box(), True, True, 0)
        
        # Copy button
        copy_btn = Gtk.Button(label="Copy")
        copy_btn.get_style_context().add_class("clear-btn")  # Reusing clear style
        copy_btn.connect("clicked", self._on_copy_clicked)
        controls.pack_end(copy_btn, False, False, 0)
        
        # Clear button
        clear_btn = Gtk.Button(label="Clear")
        clear_btn.get_style_context().add_class("clear-btn")
        clear_btn.connect("clicked", self._on_clear_clicked)
        controls.pack_end(clear_btn, False, False, 10)  # Added spacing
        
    def _update_button_label(self) -> None:
        """Update the listen button label based on state."""
        if self._is_listening:
            self._listen_button.set_label("⏹  Stop Listening")
        else:
            self._listen_button.set_label("▶  Start Listening")
        
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
        
    def _on_copy_clicked(self, button: Gtk.Button) -> None:
        """Copy transcription to clipboard."""
        start, end = self._text_buffer.get_bounds()
        text = self._text_buffer.get_text(start, end, True)
        
        if text and text != "Your transcription will appear here...":
            clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
            clipboard.set_text(text, -1)
            self.set_status("Copied to clipboard!", "active")
            
            # Reset status after 2 seconds
            GLib.timeout_add(2000, lambda: self.set_status("Ready to transcribe", "") or False)
        
    def _on_clear_clicked(self, button: Gtk.Button) -> None:
        """Clear the transcription text."""
        self._text_buffer.set_text("")
        
    def start_listening(self) -> None:
        """Start listening mode."""
        self._is_listening = True
        self._update_button_label()
        self._listen_button.get_style_context().add_class("recording")
        self.set_status("Listening...", "active")
        
        # Clear placeholder if present
        start, end = self._text_buffer.get_bounds()
        if self._text_buffer.get_text(start, end, True) == "Your transcription will appear here...":
            self._text_buffer.set_text("")
        
        if self._on_start:
            self._on_start()
            
    def stop_listening(self) -> None:
        """Stop listening mode."""
        self._is_listening = False
        self._update_button_label()
        self._listen_button.get_style_context().remove_class("recording")
        self.set_status("Ready to transcribe", "")
        
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
            
            # Add space if there's existing text
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
            status_class: CSS class for styling ("active", "error", or "")
        """
        def do_update():
            self._status_label.set_text(message)
            
            # Update style classes
            icon_ctx = self._status_icon.get_style_context()
            text_ctx = self._status_label.get_style_context()
            
            for cls in ["active", "error"]:
                icon_ctx.remove_class(cls)
                text_ctx.remove_class(cls)
            
            if status_class:
                icon_ctx.add_class(status_class)
                text_ctx.add_class(status_class)
                
            return False
            
        GLib.idle_add(do_update)
        
    def show_error(self, message: str) -> None:
        """
        Show an error message.
        
        Args:
            message: Error message
        """
        self.set_status(f"Error: {message}", "error")
        
    @property
    def is_listening(self) -> bool:
        """Check if currently listening."""
        return self._is_listening
