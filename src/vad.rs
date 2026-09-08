//! Local WebRTC voice activity segmentation.

use std::collections::VecDeque;
use thiserror::Error;
use webrtc_vad::{SampleRate, Vad, VadMode};

#[derive(Debug, Error)]
pub enum VadError {
    #[error("sample rate must be 8000, 16000, 32000, or 48000 Hz")]
    InvalidSampleRate,
    #[error("frame duration must be 10, 20, or 30 ms")]
    InvalidFrameDuration,
    #[error("VAD aggressiveness must be between 0 and 3")]
    InvalidAggressiveness,
    #[error("silence threshold must contain at least one frame")]
    InvalidSilenceThreshold,
    #[error("minimum speech must contain at least one frame")]
    InvalidMinimumSpeech,
    #[error("maximum speech must be greater than minimum speech")]
    InvalidMaximumSpeech,
}

pub struct VoiceActivityDetector {
    sample_rate: i32,
    frame_duration_ms: u32,
    frame_bytes: usize,
    silence_frames: usize,
    minimum_frames: usize,
    maximum_frames: usize,
    start_frames: usize,
    vad: Vad,
    ring: VecDeque<(Vec<u8>, bool)>,
    speech: Vec<Vec<u8>>,
    speaking: bool,
}

impl VoiceActivityDetector {
    pub fn new(
        sample_rate: i32,
        frame_duration_ms: u32,
        aggressiveness: u8,
        silence_threshold_ms: u32,
        minimum_speech_ms: u32,
        maximum_speech_ms: u32,
    ) -> Result<Self, VadError> {
        let sample_rate_enum =
            SampleRate::try_from(sample_rate).map_err(|_| VadError::InvalidSampleRate)?;
        if !matches!(frame_duration_ms, 10 | 20 | 30) {
            return Err(VadError::InvalidFrameDuration);
        }
        if aggressiveness > 3 {
            return Err(VadError::InvalidAggressiveness);
        }
        let silence_frames = (silence_threshold_ms / frame_duration_ms) as usize;
        let minimum_frames = (minimum_speech_ms / frame_duration_ms) as usize;
        let maximum_frames = (maximum_speech_ms / frame_duration_ms) as usize;
        if silence_frames == 0 {
            return Err(VadError::InvalidSilenceThreshold);
        }
        if minimum_frames == 0 {
            return Err(VadError::InvalidMinimumSpeech);
        }
        if maximum_frames < minimum_frames {
            return Err(VadError::InvalidMaximumSpeech);
        }
        let mode = match aggressiveness {
            0 => VadMode::Quality,
            1 => VadMode::LowBitrate,
            2 => VadMode::Aggressive,
            _ => VadMode::VeryAggressive,
        };
        Ok(Self {
            sample_rate,
            frame_duration_ms,
            frame_bytes: (sample_rate as usize * frame_duration_ms as usize / 1000) * 2,
            silence_frames,
            minimum_frames,
            maximum_frames,
            start_frames: minimum_frames.min(silence_frames),
            vad: Vad::new_with_rate_and_mode(sample_rate_enum, mode),
            ring: VecDeque::with_capacity(silence_frames),
            speech: Vec::new(),
            speaking: false,
        })
    }

    pub fn process_frame(&mut self, input: &[u8]) -> Option<Vec<u8>> {
        let mut frame = input.to_vec();
        frame.resize(self.frame_bytes, 0);
        frame.truncate(self.frame_bytes);
        let samples = frame
            .chunks_exact(2)
            .map(|chunk| i16::from_le_bytes([chunk[0], chunk[1]]))
            .collect::<Vec<_>>();
        let voiced = self.vad.is_voice_segment(&samples).unwrap_or(false);

        if !self.speaking {
            self.ring.push_back((frame, voiced));
            while self.ring.len() > self.silence_frames {
                self.ring.pop_front();
            }
            let voiced_count = self.ring.iter().filter(|(_, is_voiced)| *is_voiced).count();
            if voiced_count >= self.start_frames {
                self.speaking = true;
                self.speech = self.ring.drain(..).map(|(bytes, _)| bytes).collect();
            }
            return None;
        }

        self.speech.push(frame.clone());
        self.ring.push_back((frame, voiced));
        while self.ring.len() > self.silence_frames {
            self.ring.pop_front();
        }
        let unvoiced_count = self
            .ring
            .iter()
            .filter(|(_, is_voiced)| !*is_voiced)
            .count();
        if unvoiced_count * 10 > self.silence_frames * 9 || self.speech.len() >= self.maximum_frames
        {
            if self.speech.len() >= self.minimum_frames {
                let segment = self.speech.iter().flatten().copied().collect();
                self.reset();
                return Some(segment);
            }
            self.reset();
        }
        None
    }

    pub fn flush(&mut self) -> Option<Vec<u8>> {
        if self.speech.len() >= self.minimum_frames {
            let segment = self.speech.iter().flatten().copied().collect();
            self.reset();
            return Some(segment);
        }
        self.reset();
        None
    }

    pub fn is_speaking(&self) -> bool {
        self.speaking
    }

    pub fn current_duration_ms(&self) -> u32 {
        self.speech.len() as u32 * self.frame_duration_ms
    }

    pub fn sample_rate(&self) -> i32 {
        self.sample_rate
    }

    fn reset(&mut self) {
        self.speech.clear();
        self.ring.clear();
        self.speaking = false;
        self.vad.reset();
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn validates_audio_contract() {
        assert!(VoiceActivityDetector::new(16_000, 30, 2, 500, 300, 20_000).is_ok());
        assert!(matches!(
            VoiceActivityDetector::new(11_025, 30, 2, 500, 300, 20_000),
            Err(VadError::InvalidSampleRate)
        ));
    }

    #[test]
    fn silence_never_creates_a_segment() {
        let mut detector = VoiceActivityDetector::new(16_000, 30, 2, 500, 300, 20_000).unwrap();
        let frame = vec![0_u8; 960];
        for _ in 0..30 {
            assert!(detector.process_frame(&frame).is_none());
        }
        assert!(detector.flush().is_none());
    }
}
