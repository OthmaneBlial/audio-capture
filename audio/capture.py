"""Real-time microphone audio capture using PyAudio."""

import pyaudio
import threading
import queue
from typing import Callable, Optional


class AudioCapture:
    """
    Captures audio from the default microphone in real-time.
    
    Optimized for speech recognition:
    - 16kHz sample rate (optimal for Whisper)
    - Mono channel
    - 16-bit PCM format
    - 30ms frames (compatible with webrtcvad)
    """
    
    # Audio parameters optimized for Whisper
    SAMPLE_RATE = 16000
    CHANNELS = 1
    FORMAT = pyaudio.paInt16
    BYTES_PER_SAMPLE = 2
    FRAME_DURATION_MS = 30
    FRAMES_PER_BUFFER = int(SAMPLE_RATE * FRAME_DURATION_MS / 1000)  # 480 samples
    
    def __init__(self, on_audio_chunk: Optional[Callable[[bytes], None]] = None):
        """
        Initialize the audio capture.
        
        Args:
            on_audio_chunk: Optional callback called with each audio chunk
        """
        self._pyaudio: Optional[pyaudio.PyAudio] = None
        self._stream: Optional[pyaudio.Stream] = None
        self._is_running = False
        self._lock = threading.Lock()
        self._audio_queue: queue.Queue[bytes] = queue.Queue()
        self._on_audio_chunk = on_audio_chunk
        self._capture_thread: Optional[threading.Thread] = None
        
    def start(self) -> None:
        """Start capturing audio from the microphone."""
        with self._lock:
            if self._is_running:
                return
                
            self._pyaudio = pyaudio.PyAudio()
            
            # Find the default input device
            try:
                default_device = self._pyaudio.get_default_input_device_info()
                print(f"Using audio device: {default_device['name']}")
            except IOError as e:
                raise RuntimeError(f"No audio input device found: {e}")
            
            self._stream = self._pyaudio.open(
                format=self.FORMAT,
                channels=self.CHANNELS,
                rate=self.SAMPLE_RATE,
                input=True,
                frames_per_buffer=self.FRAMES_PER_BUFFER,
            )
            
            self._is_running = True
            self._capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
            self._capture_thread.start()
    
    def _capture_loop(self) -> None:
        """Continuously read audio data from the stream."""
        while self._is_running:
            try:
                if self._stream is None:
                    break
                    
                # Read audio data (blocking)
                data = self._stream.read(self.FRAMES_PER_BUFFER, exception_on_overflow=False)
                
                # Put in queue for consumers
                self._audio_queue.put(data)
                
                # Call callback if provided
                if self._on_audio_chunk:
                    self._on_audio_chunk(data)
                    
            except Exception as e:
                if self._is_running:  # Only log if not intentionally stopped
                    print(f"Audio capture error: {e}")
                break
    
    def stop(self) -> None:
        """Stop capturing audio."""
        with self._lock:
            self._is_running = False
            
            if self._stream:
                self._stream.stop_stream()
                self._stream.close()
                self._stream = None
                
            if self._pyaudio:
                self._pyaudio.terminate()
                self._pyaudio = None
                
            # Clear the queue
            while not self._audio_queue.empty():
                try:
                    self._audio_queue.get_nowait()
                except queue.Empty:
                    break
    
    def get_audio_chunk(self, timeout: float = 0.1) -> Optional[bytes]:
        """
        Get the next audio chunk from the queue.
        
        Args:
            timeout: Maximum time to wait for a chunk
            
        Returns:
            Audio bytes or None if timeout
        """
        try:
            return self._audio_queue.get(timeout=timeout)
        except queue.Empty:
            return None
    
    @property
    def is_running(self) -> bool:
        """Check if audio capture is currently running."""
        return self._is_running
    
    @property
    def sample_rate(self) -> int:
        """Get the sample rate."""
        return self.SAMPLE_RATE
    
    @property
    def frame_duration_ms(self) -> int:
        """Get the frame duration in milliseconds."""
        return self.FRAME_DURATION_MS
    
    def __enter__(self):
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
        return False
