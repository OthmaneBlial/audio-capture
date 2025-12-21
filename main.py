#!/usr/bin/env python3
"""
Real-Time Voice Transcriber

A lightweight Linux desktop application that continuously listens to
microphone input and transcribes speech to text using Groq's Whisper
Large V3 Turbo model.

Usage:
    python main.py

Environment Variables:
    GROQ_API_KEY: Your Groq API key (required)
"""

import os
import sys
import threading
import signal
import time
from typing import Optional

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

from audio import AudioCapture, VoiceActivityDetector
from transcription import GroqTranscriptionService
from ui import MainWindow
from config import ConfigManager


class VoiceTranscriberApp:
    """
    Main application controller.
    
    Coordinates audio capture, voice activity detection,
    transcription, and UI updates.
    """
    
    def __init__(self):
        """Initialize the application."""
        self._running = False
        self._processing_thread: Optional[threading.Thread] = None
        self._audio: Optional[AudioCapture] = None
        self._vad: Optional[VoiceActivityDetector] = None
        
        # Initialize configuration
        self._config = ConfigManager()
        
        # Get settings
        api_key = self._config.get("api_key")
        language = self._config.get("language")
        translate = self._config.get("translate_to_english")
        
        # Warn if no key (but don't exit, UI will handle it)
        if not api_key or "your_api_key" in api_key:
            print("Notice: No API key found in config or env. Running in mock mode.")
        
        # Initialize transcription service
        self._transcriber = GroqTranscriptionService(
            api_key=api_key,
            sample_rate=16000,
            language=language,
            on_transcription=self._on_transcription,
            on_error=self._on_transcription_error,
        )
        self._transcriber.update_config(translate=translate)
        
        # Initialize UI (must be done before GTK main loop)
        self._window = MainWindow(
            config=self._config,
            on_start=self._start_listening,
            on_stop=self._stop_listening,
            on_settings_change=self._on_settings_change,
        )
        
    def _on_settings_change(self) -> None:
        """Handle settings changes from UI."""
        api_key = self._config.get("api_key")
        language = self._config.get("language")
        translate = self._config.get("translate_to_english")
        
        self._transcriber.update_config(
            api_key=api_key,
            language=language,
            translate=translate
        )
        print("Configuration updated")
        
    def _start_listening(self) -> None:
        """Start the audio capture and processing."""
        if self._running:
            return
        
        try:
            # Initialize audio components
            self._audio = AudioCapture()
            self._vad = VoiceActivityDetector(
                sample_rate=self._audio.sample_rate,
                frame_duration_ms=self._audio.frame_duration_ms,
                aggressiveness=2,
                silence_threshold_ms=600,
                min_speech_ms=300,
                max_speech_ms=20000,
            )
            
            self._running = True
            self._audio.start()
            
            # Start processing thread
            self._processing_thread = threading.Thread(
                target=self._processing_loop,
                daemon=True,
                name="AudioProcessing"
            )
            self._processing_thread.start()
            
            print("🎤 Listening started")
            
        except Exception as e:
            print(f"Failed to start listening: {e}")
            GLib.idle_add(lambda: self._window.show_error(str(e)) or False)
            GLib.idle_add(lambda: self._window.stop_listening() or False)
        
    def _stop_listening(self) -> None:
        """Stop the audio capture and processing."""
        print("⏹ Stopping...")
        self._running = False
        
        # Stop audio capture
        if self._audio:
            try:
                self._audio.stop()
            except Exception as e:
                print(f"Error stopping audio: {e}")
            self._audio = None
        
        # Flush remaining audio from VAD
        if self._vad:
            remaining = self._vad.flush()
            if remaining and len(remaining) > 1000:  # Only transcribe if substantial
                self._transcriber.transcribe_async(remaining)
            self._vad = None
        
        print("✅ Stopped")
        
    def _processing_loop(self) -> None:
        """Main loop for processing audio frames."""
        print("Processing loop started")
        
        while self._running and self._audio and self._vad:
            try:
                # Get audio chunk with timeout
                chunk = self._audio.get_audio_chunk(timeout=0.1)
                if chunk is None:
                    continue
                
                # Process through VAD
                speech_segment = self._vad.process_frame(chunk)
                
                # Update status if speaking
                if self._vad.is_speaking:
                    duration_s = self._vad.current_duration_ms / 1000
                    GLib.idle_add(
                        lambda d=duration_s: self._window.set_status(
                            f"Speaking... ({d:.1f}s)", "active"
                        ) or False
                    )
                
                # Transcribe complete speech segments
                if speech_segment:
                    print(f"📝 Got speech segment: {len(speech_segment)} bytes")
                    GLib.idle_add(
                        lambda: self._window.set_status("Transcribing...", "active") or False
                    )
                    self._transcriber.transcribe_async(speech_segment)
                    
            except Exception as e:
                print(f"Processing error: {e}")
                time.sleep(0.1)
                
        print("Processing loop ended")
                
    def _on_transcription(self, text: str) -> None:
        """Handle successful transcription."""
        print(f"✅ Transcribed: {text}")
        if text and text.strip():
            GLib.idle_add(lambda t=text: self._window.append_text(t) or False)
            
        if self._running:
            GLib.idle_add(
                lambda: self._window.set_status("Listening...", "active") or False
            )
            
    def _on_transcription_error(self, error: Exception) -> None:
        """Handle transcription errors."""
        error_msg = str(error)
        print(f"❌ Transcription error: {error_msg}")
        
        # Truncate long error messages
        if len(error_msg) > 40:
            error_msg = error_msg[:37] + "..."
            
        GLib.idle_add(lambda e=error_msg: self._window.show_error(e) or False)
        
        # Resume listening status after a delay
        if self._running:
            GLib.timeout_add(
                3000,
                lambda: self._window.set_status("Listening...", "active") or False
            )
        
    def run(self) -> None:
        """Run the application."""
        # Handle Ctrl+C gracefully
        def signal_handler(sig, frame):
            print("\nShutting down...")
            self._stop_listening()
            GLib.idle_add(Gtk.main_quit)
            
        signal.signal(signal.SIGINT, signal_handler)
        
        # Show window and start main loop
        self._window.show_all()
        
        print("🎙 Voice Transcriber started")
        print("   Click 'Start Listening' to begin")
        
        Gtk.main()
        
        # Cleanup
        self._stop_listening()


def main():
    """Application entry point."""
    # Set up application ID for icon association
    GLib.set_prgname("voice-transcriber")
    GLib.set_application_name("Voice Transcriber")
    
    # Suppress ALSA warnings by redirecting stderr
    # This is a bit of a hack but cleans up the console output
    try:
        from ctypes import CDLL, CFUNCTYPE, c_char_p, c_int, c_void_p
        
        def py_error_handler(filename, line, function, err, fmt):
            pass
            
        ERROR_HANDLER_FUNC = CFUNCTYPE(None, c_char_p, c_int, c_char_p, c_int, c_char_p)
        c_error_handler = ERROR_HANDLER_FUNC(py_error_handler)
        
        asound = CDLL('libasound.so.2')
        asound.snd_lib_error_set_handler(c_error_handler)
    except:
        pass
    
    app = VoiceTranscriberApp()
    app.run()


if __name__ == "__main__":
    main()
