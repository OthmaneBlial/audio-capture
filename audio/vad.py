"""Voice Activity Detection using webrtcvad."""

import collections
from typing import Optional

import webrtcvad


class VoiceActivityDetector:
    """
    Detects voice activity in audio streams using webrtcvad.
    
    Collects audio frames and yields complete speech segments
    when silence is detected.
    """
    
    def __init__(
        self,
        sample_rate: int = 16000,
        frame_duration_ms: int = 30,
        aggressiveness: int = 2,
        silence_threshold_ms: int = 500,
        min_speech_ms: int = 250,
        max_speech_ms: int = 25000,
    ):
        """
        Initialize the voice activity detector.
        
        Args:
            sample_rate: Audio sample rate (must be 8000, 16000, 32000, or 48000)
            frame_duration_ms: Frame duration in ms (must be 10, 20, or 30)
            aggressiveness: VAD aggressiveness (0-3, higher = more aggressive)
            silence_threshold_ms: Silence duration to end a speech segment
            min_speech_ms: Minimum speech duration to consider valid
            max_speech_ms: Maximum speech segment duration (force split)
        """
        if sample_rate not in (8000, 16000, 32000, 48000):
            raise ValueError(f"Invalid sample rate: {sample_rate}")
        if frame_duration_ms not in (10, 20, 30):
            raise ValueError(f"Invalid frame duration: {frame_duration_ms}")
        if not 0 <= aggressiveness <= 3:
            raise ValueError(f"Invalid aggressiveness: {aggressiveness}")
        if silence_threshold_ms < frame_duration_ms:
            raise ValueError("silence_threshold_ms must be at least one audio frame")
        if min_speech_ms < frame_duration_ms:
            raise ValueError("min_speech_ms must be at least one audio frame")
        if max_speech_ms < min_speech_ms:
            raise ValueError("max_speech_ms must be greater than min_speech_ms")
            
        self._sample_rate = sample_rate
        self._frame_duration_ms = frame_duration_ms
        self._aggressiveness = aggressiveness
        self._silence_threshold_ms = silence_threshold_ms
        self._min_speech_ms = min_speech_ms
        self._max_speech_ms = max_speech_ms
        
        # Calculate frame and threshold sizes
        self._frame_size = int(sample_rate * frame_duration_ms / 1000) * 2  # 2 bytes per sample
        self._silence_frames = silence_threshold_ms // frame_duration_ms
        self._min_speech_frames = min_speech_ms // frame_duration_ms
        self._max_speech_frames = max_speech_ms // frame_duration_ms
        
        # Initialize VAD
        self._vad = webrtcvad.Vad(aggressiveness)
        
        # Ring buffer for detecting speech end
        self._ring_buffer: collections.deque = collections.deque(maxlen=self._silence_frames)
        
        # Current speech segment
        self._speech_frames: list[bytes] = []
        self._is_speaking = False
        self._voiced_count = 0
        
    def process_frame(self, frame: bytes) -> Optional[bytes]:
        """
        Process a single audio frame.
        
        Args:
            frame: Raw audio bytes (must match expected frame size)
            
        Returns:
            Complete speech segment bytes if speech ended, None otherwise
        """
        if not isinstance(frame, bytes):
            raise TypeError("frame must be bytes")
        if len(frame) != self._frame_size:
            # Handle incorrect frame size by padding or truncating
            if len(frame) < self._frame_size:
                frame = frame + b'\x00' * (self._frame_size - len(frame))
            else:
                frame = frame[:self._frame_size]
        
        is_speech = self._vad.is_speech(frame, self._sample_rate)
        
        if not self._is_speaking:
            # Not currently in a speech segment
            self._ring_buffer.append((frame, is_speech))
            
            # Count voiced frames in ring buffer
            voiced_count = sum(1 for _, speech in self._ring_buffer if speech)
            
            # Start speech if enough voiced frames
            if voiced_count > 0.9 * self._ring_buffer.maxlen:
                self._is_speaking = True
                # Add all buffered frames to speech
                self._speech_frames = [f for f, _ in self._ring_buffer]
                self._ring_buffer.clear()
                
        else:
            # Currently in a speech segment
            self._speech_frames.append(frame)
            self._ring_buffer.append((frame, is_speech))
            
            # Count unvoiced frames in ring buffer
            unvoiced_count = sum(1 for _, speech in self._ring_buffer if not speech)
            
            # Check if we should end the speech segment
            segment_frames = len(self._speech_frames)
            should_end = (
                # Enough silence detected
                unvoiced_count > 0.9 * self._ring_buffer.maxlen or
                # Maximum duration reached
                segment_frames >= self._max_speech_frames
            )
            
            if should_end:
                # Check minimum duration
                if segment_frames >= self._min_speech_frames:
                    # Return the complete speech segment
                    segment = b''.join(self._speech_frames)
                    self._reset()
                    return segment
                else:
                    # Too short, discard
                    self._reset()
        
        return None
    
    def flush(self) -> Optional[bytes]:
        """
        Flush any remaining speech frames.
        
        Call this when stopping recording to get any pending audio.
        
        Returns:
            Remaining speech segment or None
        """
        if self._speech_frames and len(self._speech_frames) >= self._min_speech_frames:
            segment = b''.join(self._speech_frames)
            self._reset()
            return segment
        
        self._reset()
        return None
    
    def _reset(self) -> None:
        """Reset the detector state."""
        self._speech_frames = []
        self._is_speaking = False
        self._ring_buffer.clear()
    
    @property
    def is_speaking(self) -> bool:
        """Check if currently detecting speech."""
        return self._is_speaking
    
    @property
    def current_duration_ms(self) -> int:
        """Get the current speech segment duration in ms."""
        return len(self._speech_frames) * self._frame_duration_ms
