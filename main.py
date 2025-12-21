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
        
        # Check for API key
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            print("Error: GROQ_API_KEY environment variable not set")
            print("Please set it in a .env file or export it:")
            print("  export GROQ_API_KEY=your_api_key_here")
            sys.exit(1)
        
        # Initialize components
        self._audio = AudioCapture()
        self._vad = VoiceActivityDetector(
            sample_rate=self._audio.sample_rate,
            frame_duration_ms=self._audio.frame_duration_ms,
            aggressiveness=2,
            silence_threshold_ms=500,
            min_speech_ms=250,
            max_speech_ms=25000,
        )
        self._transcriber = GroqTranscriptionService(
            api_key=api_key,
            sample_rate=self._audio.sample_rate,
            on_transcription=self._on_transcription,
            on_error=self._on_transcription_error,
        )
        
        # Initialize UI
        self._window = MainWindow(
            on_start=self._start_listening,
            on_stop=self._stop_listening,
        )
        
        # Test API connection
        self._test_connection()
        
    def _test_connection(self) -> None:
        """Test the Groq API connection."""
        self._window.set_status("Testing API connection...", "")
        
        def do_test():
            if self._transcriber.test_connection():
                GLib.idle_add(
                    lambda: self._window.set_status("Ready", "") or False
                )
            else:
                GLib.idle_add(
                    lambda: self._window.show_error("API connection failed") or False
                )
        
        threading.Thread(target=do_test, daemon=True).start()
        
    def _start_listening(self) -> None:
        """Start the audio capture and processing."""
        if self._running:
            return
            
        self._running = True
        self._audio.start()
        
        # Start processing thread
        self._processing_thread = threading.Thread(
            target=self._processing_loop,
            daemon=True,
        )
        self._processing_thread.start()
        
    def _stop_listening(self) -> None:
        """Stop the audio capture and processing."""
        self._running = False
        self._audio.stop()
        
        # Flush any remaining audio
        remaining = self._vad.flush()
        if remaining:
            self._transcriber.transcribe_async(remaining)
        
    def _processing_loop(self) -> None:
        """Main loop for processing audio frames."""
        while self._running:
            # Get audio chunk
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
                        f"🗣 Speaking... ({d:.1f}s)", "listening"
                    ) or False
                )
            
            # Transcribe complete speech segments
            if speech_segment:
                GLib.idle_add(
                    lambda: self._window.set_status(
                        "⏳ Transcribing...", "listening"
                    ) or False
                )
                self._transcriber.transcribe_async(speech_segment)
                
    def _on_transcription(self, text: str) -> None:
        """Handle successful transcription."""
        if text:
            self._window.append_text(text)
            
        if self._running:
            self._window.set_status("🎤 Listening...", "listening")
            
    def _on_transcription_error(self, error: Exception) -> None:
        """Handle transcription errors."""
        error_msg = str(error)
        
        # Truncate long error messages
        if len(error_msg) > 50:
            error_msg = error_msg[:47] + "..."
            
        self._window.show_error(error_msg)
        print(f"Transcription error: {error}")
        
        # Resume listening status after a delay
        if self._running:
            GLib.timeout_add(
                2000,
                lambda: self._window.set_status("🎤 Listening...", "listening") or False
            )
        
    def run(self) -> None:
        """Run the application."""
        # Handle Ctrl+C gracefully
        def signal_handler(sig, frame):
            self._stop_listening()
            Gtk.main_quit()
            
        signal.signal(signal.SIGINT, signal_handler)
        
        # Show window and start main loop
        self._window.show_all()
        Gtk.main()
        
        # Cleanup
        self._stop_listening()


def main():
    """Application entry point."""
    app = VoiceTranscriberApp()
    app.run()


if __name__ == "__main__":
    main()
