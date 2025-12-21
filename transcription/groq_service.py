"""Groq Whisper API integration for speech-to-text transcription."""

import io
import wave
import threading
import time
import random
from typing import Optional, Callable
from groq import Groq


class GroqTranscriptionService:
    """
    Transcription service using Groq's Whisper Large V3 Turbo model.
    
    Features:
    - Fast transcription with 216x real-time speed
    - Automatic WAV encoding from raw PCM
    - Thread-safe API calls
    - Error handling with callbacks
    - Dynamic configuration (language, task)
    """
    
    MODEL = "whisper-large-v3-turbo"
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        sample_rate: int = 16000,
        channels: int = 1,
        sample_width: int = 2,
        language: Optional[str] = None,
        on_transcription: Optional[Callable[[str], None]] = None,
        on_error: Optional[Callable[[Exception], None]] = None,
    ):
        """
        Initialize the transcription service.
        """
        self._sample_rate = sample_rate
        self._channels = channels
        self._sample_width = sample_width
        self._language = language
        self._on_transcription = on_transcription
        self._on_error = on_error
        self._lock = threading.Lock()
        
        self._task = "transcribe"
        self._is_mock = False
        self._client = None
        
        # Initialize client
        self.update_config(api_key=api_key, language=language)
        
    def update_config(self, api_key: Optional[str] = None, language: Optional[str] = None, translate: bool = False):
        """Update configuration dynamically."""
        with self._lock:
            if api_key is not None:
                if not api_key or "your_api_key" in api_key or len(api_key) < 10:
                    self._is_mock = True
                    self._client = None
                else:
                    self._is_mock = False
                    self._client = Groq(api_key=api_key)
            
            if language is not None:
                self._language = language if language != "auto" else None
                
            self._task = "translate" if translate else "transcribe"

    def transcribe(self, audio_data: bytes) -> Optional[str]:
        """
        Transcribe raw PCM audio data.
        """
        try:
            # Mock mode handling
            if self._is_mock:
                time.sleep(0.5)  # Simulate network latency
                
                phrases = [
                    "This is a demo transcription.",
                    "Settings updated successfully!",
                    "Translation simulation active.",
                    "Save to file feature is cool.",
                    "Voice activity detection is working!",
                    "Testing dynamic configuration."
                ]
                text = random.choice(phrases)
                
                if self._task == "translate":
                    text = "[Translated] " + text
                
                if self._on_transcription:
                    self._on_transcription(text)
                return text

            # Convert raw PCM to WAV format
            wav_buffer = self._pcm_to_wav(audio_data)
            
            # Call Groq API
            with self._lock:
                if not self._client:
                    raise RuntimeError("Groq client not initialized")

                if self._task == "translate":
                    # Translation endpoint
                    transcription = self._client.audio.translations.create(
                        file=("audio.wav", wav_buffer, "audio/wav"),
                        model=self.MODEL,
                        response_format="text",
                    )
                else:
                    # Transcription endpoint
                    transcription = self._client.audio.transcriptions.create(
                        file=("audio.wav", wav_buffer, "audio/wav"),
                        model=self.MODEL,
                        language=self._language,
                        response_format="text",
                    )
            
            # Get the transcribed text
            text = transcription.strip() if isinstance(transcription, str) else str(transcription).strip()
            
            if text and self._on_transcription:
                self._on_transcription(text)
                
            return text
            
        except Exception as e:
            if self._on_error:
                self._on_error(e)
            return None
    
    def transcribe_async(self, audio_data: bytes) -> threading.Thread:
        """Transcribe audio data asynchronously."""
        thread = threading.Thread(
            target=self.transcribe,
            args=(audio_data,),
            daemon=True,
        )
        thread.start()
        return thread
    
    def _pcm_to_wav(self, pcm_data: bytes) -> io.BytesIO:
        """Convert raw PCM data to WAV format."""
        buffer = io.BytesIO()
        
        with wave.open(buffer, 'wb') as wav_file:
            wav_file.setnchannels(self._channels)
            wav_file.setsampwidth(self._sample_width)
            wav_file.setframerate(self._sample_rate)
            wav_file.writeframes(pcm_data)
        
        buffer.seek(0)
        return buffer
    
    def test_connection(self) -> bool:
        """Test the API connection."""
        if self._is_mock:
            return True
            
        try:
            silent_samples = int(self._sample_rate * 0.1) * self._channels
            silent_data = b'\x00' * (silent_samples * self._sample_width)
            wav_buffer = self._pcm_to_wav(silent_data)
            
            with self._lock:
                if not self._client:
                    return False
                self._client.audio.transcriptions.create(
                    file=("test.wav", wav_buffer, "audio/wav"),
                    model=self.MODEL,
                    response_format="text",
                )
            return True
            
        except Exception as e:
            if self._on_error:
                self._on_error(e)
            return False
