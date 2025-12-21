"""Groq Whisper API integration for speech-to-text transcription."""

import io
import wave
import threading
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
        
        Args:
            api_key: Groq API key (uses GROQ_API_KEY env var if not provided)
            sample_rate: Audio sample rate
            channels: Number of audio channels
            sample_width: Bytes per sample (2 for 16-bit)
            language: Optional language code (e.g., "en", "es", "fr")
            on_transcription: Callback for successful transcriptions
            on_error: Callback for errors
        """
        self._client = Groq(api_key=api_key)
        self._sample_rate = sample_rate
        self._channels = channels
        self._sample_width = sample_width
        self._language = language
        self._on_transcription = on_transcription
        self._on_error = on_error
        self._lock = threading.Lock()
        
    def transcribe(self, audio_data: bytes) -> Optional[str]:
        """
        Transcribe raw PCM audio data.
        
        Args:
            audio_data: Raw PCM audio bytes
            
        Returns:
            Transcribed text or None on error
        """
        try:
            # Convert raw PCM to WAV format
            wav_buffer = self._pcm_to_wav(audio_data)
            
            # Call Groq API
            with self._lock:
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
        """
        Transcribe audio data asynchronously.
        
        Args:
            audio_data: Raw PCM audio bytes
            
        Returns:
            Thread handle
        """
        thread = threading.Thread(
            target=self.transcribe,
            args=(audio_data,),
            daemon=True,
        )
        thread.start()
        return thread
    
    def _pcm_to_wav(self, pcm_data: bytes) -> io.BytesIO:
        """
        Convert raw PCM data to WAV format.
        
        Args:
            pcm_data: Raw PCM audio bytes
            
        Returns:
            BytesIO buffer containing WAV data
        """
        buffer = io.BytesIO()
        
        with wave.open(buffer, 'wb') as wav_file:
            wav_file.setnchannels(self._channels)
            wav_file.setsampwidth(self._sample_width)
            wav_file.setframerate(self._sample_rate)
            wav_file.writeframes(pcm_data)
        
        buffer.seek(0)
        return buffer
    
    def test_connection(self) -> bool:
        """
        Test the API connection with a minimal request.
        
        Returns:
            True if connection is successful
        """
        try:
            # Create a minimal silent audio sample (0.1 seconds)
            silent_samples = int(self._sample_rate * 0.1) * self._channels
            silent_data = b'\x00' * (silent_samples * self._sample_width)
            wav_buffer = self._pcm_to_wav(silent_data)
            
            # Try to transcribe (will return empty or minimal text)
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
