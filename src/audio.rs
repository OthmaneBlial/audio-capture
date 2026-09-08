//! Cross-platform microphone capture built on CPAL.
//!
//! The audio backend deliberately exposes 16 kHz, mono, signed 16-bit PCM to
//! the rest of the application. Device-specific sample formats, channel
//! layouts and sample rates are converted inside the callback before frames
//! enter a bounded queue. This keeps the VAD and provider code independent of
//! CoreAudio, WASAPI and ALSA details.

use std::collections::VecDeque;
use std::sync::{
    atomic::{AtomicBool, AtomicUsize, Ordering},
    Arc, Mutex,
};
use std::time::Duration;

use cpal::traits::{DeviceTrait, HostTrait, StreamTrait};
use cpal::{SampleFormat, StreamConfig};
use crossbeam_channel::{bounded, Receiver, Sender, TryRecvError, TrySendError};
use sha2::{Digest, Sha256};
use thiserror::Error;

/// PCM sample rate delivered to the VAD and transcription provider.
pub const TARGET_SAMPLE_RATE: u32 = 16_000;
/// Number of PCM samples in one 30 ms frame at [`TARGET_SAMPLE_RATE`].
pub const TARGET_FRAME_SAMPLES: usize = 480;
/// Maximum number of complete frames retained while the consumer is busy.
pub const MAX_QUEUED_FRAMES: usize = 64;

#[derive(Debug, Error)]
pub enum AudioError {
    #[error("no input audio device is available")]
    NoInputDevice,
    #[error("audio backend error: {0}")]
    Backend(#[from] cpal::Error),
    #[error("could not inspect input device {index}: {message}")]
    DeviceInspection { index: usize, message: String },
    #[error("input device index {0} is unavailable")]
    DeviceIndex(usize),
    #[error("saved input device identity {0} was not found")]
    IdentityNotFound(String),
    #[error("input device exposes unsupported sample format {0:?}")]
    UnsupportedSampleFormat(SampleFormat),
    #[error("audio stream is already running")]
    AlreadyRunning,
    #[error("audio stream is not running")]
    NotRunning,
}

/// A user-facing description of an input device.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct InputDevice {
    /// Index in the current CPAL enumeration. It is only valid for this run.
    pub index: usize,
    /// Human-readable name shown in settings.
    pub name: String,
    /// Opaque, stable identity suitable for persistence.
    pub identity: String,
    /// Whether CPAL reports this device as the current default input.
    pub is_default: bool,
    pub channels: u16,
    pub sample_rate: u32,
    pub sample_format: String,
}

/// List the input devices visible to the current host.
pub fn list_input_devices() -> Result<Vec<InputDevice>, AudioError> {
    enumerate_devices().map(|devices| {
        devices
            .into_iter()
            .map(|(_, description)| description)
            .collect()
    })
}

/// Hash a backend identifier into the 24-character format accepted by the
/// persisted application configuration. Names and channel count are included
/// as a fallback signal because a few backends expose an empty identifier.
pub fn stable_device_identity(backend_id: &str, name: &str, channels: u16) -> String {
    let mut hasher = Sha256::new();
    hasher.update(backend_id.trim().as_bytes());
    hasher.update([0]);
    hasher.update(name.trim().as_bytes());
    hasher.update([0]);
    hasher.update(channels.to_le_bytes());
    let digest = hasher.finalize();
    digest[..12]
        .iter()
        .map(|byte| format!("{byte:02x}"))
        .collect()
}

/// A running microphone stream.
pub struct AudioCapture {
    stream: Option<cpal::Stream>,
    frames: Receiver<Vec<u8>>,
    errors: Receiver<String>,
    levels: Receiver<f32>,
    running: Arc<AtomicBool>,
    dropped_frames: Arc<AtomicUsize>,
    device: InputDevice,
}

impl AudioCapture {
    /// Open and start the selected device. If no device index or saved identity
    /// is provided, the system default input is preferred.
    pub fn open(
        device_index: Option<usize>,
        expected_identity: Option<&str>,
    ) -> Result<Self, AudioError> {
        let devices = enumerate_devices()?;
        let (device, description) = if let Some(identity) = expected_identity {
            devices
                .into_iter()
                .find(|(_, description)| description.identity == identity)
                .ok_or_else(|| AudioError::IdentityNotFound(identity.to_owned()))?
        } else if let Some(index) = device_index {
            devices
                .into_iter()
                .find(|(_, description)| description.index == index)
                .ok_or(AudioError::DeviceIndex(index))?
        } else {
            devices
                .into_iter()
                .find(|(_, description)| description.is_default)
                .or_else(|| enumerate_devices().ok()?.into_iter().next())
                .ok_or(AudioError::NoInputDevice)?
        };

        let supported = device.default_input_config()?;
        let channels = supported.channels();
        let sample_rate = supported.sample_rate();
        let sample_format = supported.sample_format();
        ensure_supported_sample_format(sample_format)?;

        let (frame_tx, frame_rx) = bounded::<Vec<u8>>(MAX_QUEUED_FRAMES);
        let (error_tx, error_rx) = bounded::<String>(8);
        let (level_tx, level_rx) = bounded::<f32>(8);
        let running = Arc::new(AtomicBool::new(true));
        let dropped_frames = Arc::new(AtomicUsize::new(0));
        let callback_context = StreamContext {
            assembler: Arc::new(Mutex::new(FrameAssembler::new(channels, sample_rate))),
            frames: frame_tx.clone(),
            frame_receiver: frame_rx.clone(),
            dropped_frames: Arc::clone(&dropped_frames),
            levels: level_tx.clone(),
        };
        let callback_running = Arc::clone(&running);
        let callback_errors = error_tx.clone();
        let error_callback = move |error: cpal::Error| {
            callback_running.store(false, Ordering::Release);
            let _ = callback_errors.try_send(error.to_string());
        };

        let config: StreamConfig = supported.config();
        let stream = match sample_format {
            SampleFormat::F32 => {
                build_stream::<f32>(&device, config, callback_context, error_callback)?
            }
            SampleFormat::I16 => {
                build_stream::<i16>(&device, config, callback_context, error_callback)?
            }
            SampleFormat::U16 => {
                build_stream::<u16>(&device, config, callback_context, error_callback)?
            }
            SampleFormat::I8 => {
                build_stream::<i8>(&device, config, callback_context, error_callback)?
            }
            SampleFormat::U8 => {
                build_stream::<u8>(&device, config, callback_context, error_callback)?
            }
            SampleFormat::I32 => {
                build_stream::<i32>(&device, config, callback_context, error_callback)?
            }
            SampleFormat::U32 => {
                build_stream::<u32>(&device, config, callback_context, error_callback)?
            }
            SampleFormat::I64 => {
                build_stream::<i64>(&device, config, callback_context, error_callback)?
            }
            SampleFormat::U64 => {
                build_stream::<u64>(&device, config, callback_context, error_callback)?
            }
            SampleFormat::F64 => {
                build_stream::<f64>(&device, config, callback_context, error_callback)?
            }
            other => return Err(AudioError::UnsupportedSampleFormat(other)),
        };

        stream.play()?;
        Ok(Self {
            stream: Some(stream),
            frames: frame_rx,
            errors: error_rx,
            levels: level_rx,
            running,
            dropped_frames,
            device: InputDevice {
                sample_format: format!("{sample_format:?}"),
                channels,
                sample_rate,
                ..description
            },
        })
    }

    pub fn device(&self) -> &InputDevice {
        &self.device
    }

    pub fn try_recv_frame(&self) -> Option<Vec<u8>> {
        self.frames.try_recv().ok()
    }

    pub fn recv_frame(&self, timeout: Duration) -> Option<Vec<u8>> {
        self.frames.recv_timeout(timeout).ok()
    }

    pub fn try_recv_level(&self) -> Option<f32> {
        self.levels.try_iter().last()
    }

    pub fn try_recv_error(&self) -> Option<String> {
        self.errors.try_recv().ok()
    }

    pub fn dropped_frames(&self) -> usize {
        self.dropped_frames.load(Ordering::Acquire)
    }

    pub fn is_running(&self) -> bool {
        self.running.load(Ordering::Acquire)
    }

    pub fn stop(&mut self) {
        self.running.store(false, Ordering::Release);
        self.stream.take();
    }
}

impl Drop for AudioCapture {
    fn drop(&mut self) {
        self.stop();
    }
}

fn enumerate_devices() -> Result<Vec<(cpal::Device, InputDevice)>, AudioError> {
    let host = cpal::default_host();
    let default_id = host
        .default_input_device()
        .and_then(|device| device.id().ok())
        .map(|id| id.to_string());
    let devices = host.input_devices()?;
    let mut result = Vec::new();
    for (index, device) in devices.enumerate() {
        let description = device
            .description()
            .map_err(|error| AudioError::DeviceInspection {
                index,
                message: error.to_string(),
            })?;
        let backend_id = device.id().map_err(|error| AudioError::DeviceInspection {
            index,
            message: error.to_string(),
        })?;
        let config =
            device
                .default_input_config()
                .map_err(|error| AudioError::DeviceInspection {
                    index,
                    message: error.to_string(),
                })?;
        let identity = stable_device_identity(
            &backend_id.to_string(),
            description.name(),
            config.channels(),
        );
        result.push((
            device,
            InputDevice {
                index,
                name: description.name().to_owned(),
                identity,
                is_default: default_id.as_deref() == Some(backend_id.to_string().as_str()),
                channels: config.channels(),
                sample_rate: config.sample_rate(),
                sample_format: format!("{:?}", config.sample_format()),
            },
        ));
    }
    if result.is_empty() {
        Err(AudioError::NoInputDevice)
    } else {
        Ok(result)
    }
}

fn ensure_supported_sample_format(format: SampleFormat) -> Result<(), AudioError> {
    match format {
        SampleFormat::F32
        | SampleFormat::I16
        | SampleFormat::U16
        | SampleFormat::I8
        | SampleFormat::U8
        | SampleFormat::I32
        | SampleFormat::U32
        | SampleFormat::I64
        | SampleFormat::U64
        | SampleFormat::F64 => Ok(()),
        other => Err(AudioError::UnsupportedSampleFormat(other)),
    }
}

trait AudioSample: Copy + Send + 'static {
    fn to_i16(self) -> i16;
}

fn float_to_i16(value: f64) -> i16 {
    let value = value.clamp(-1.0, 1.0);
    if value <= -1.0 {
        i16::MIN
    } else if value >= 1.0 {
        i16::MAX
    } else {
        (value * i16::MAX as f64).round() as i16
    }
}

impl AudioSample for f32 {
    fn to_i16(self) -> i16 {
        float_to_i16(self as f64)
    }
}

impl AudioSample for f64 {
    fn to_i16(self) -> i16 {
        float_to_i16(self)
    }
}

impl AudioSample for i8 {
    fn to_i16(self) -> i16 {
        (self as i16) << 8
    }
}

impl AudioSample for u8 {
    fn to_i16(self) -> i16 {
        ((self as i16) - 128) << 8
    }
}

impl AudioSample for i16 {
    fn to_i16(self) -> i16 {
        self
    }
}

impl AudioSample for u16 {
    fn to_i16(self) -> i16 {
        (self as i32 - 32_768).clamp(i16::MIN as i32, i16::MAX as i32) as i16
    }
}

impl AudioSample for i32 {
    fn to_i16(self) -> i16 {
        float_to_i16(self as f64 / i32::MAX as f64)
    }
}

impl AudioSample for u32 {
    fn to_i16(self) -> i16 {
        float_to_i16((self as f64 - 2_147_483_648.0) / 2_147_483_647.0)
    }
}

impl AudioSample for i64 {
    fn to_i16(self) -> i16 {
        float_to_i16(self as f64 / i64::MAX as f64)
    }
}

impl AudioSample for u64 {
    fn to_i16(self) -> i16 {
        float_to_i16((self as f64 - 9_223_372_036_854_775_808.0) / 9_223_372_036_854_775_807.0)
    }
}

struct StreamContext {
    assembler: Arc<Mutex<FrameAssembler>>,
    frames: Sender<Vec<u8>>,
    frame_receiver: Receiver<Vec<u8>>,
    dropped_frames: Arc<AtomicUsize>,
    levels: Sender<f32>,
}

fn build_stream<T: AudioSample + cpal::SizedSample>(
    device: &cpal::Device,
    config: StreamConfig,
    context: StreamContext,
    error_callback: impl FnMut(cpal::Error) + Send + 'static,
) -> Result<cpal::Stream, AudioError> {
    let channels = config.channels as usize;
    let StreamContext {
        assembler,
        frames: frame_tx,
        frame_receiver,
        dropped_frames,
        levels,
    } = context;
    Ok(device.build_input_stream::<T, _, _>(
        config,
        move |samples, _| {
            if samples.is_empty() || channels == 0 {
                return;
            }
            let mut converted = Vec::with_capacity(samples.len());
            let mut sum_squares = 0.0_f64;
            for sample in samples {
                let pcm = sample.to_i16();
                sum_squares += f64::from(pcm).powi(2);
                converted.push(pcm);
            }
            let rms = (sum_squares / converted.len() as f64).sqrt() / i16::MAX as f64;
            publish_level(&levels, rms as f32);

            let frames = assembler
                .lock()
                .map(|mut assembler| assembler.push_interleaved(&converted))
                .unwrap_or_default();
            for frame in frames {
                enqueue_frame(&frame_tx, &frame_receiver, frame, &dropped_frames);
            }
        },
        error_callback,
        None,
    )?)
}

fn publish_level(levels: &Sender<f32>, value: f32) {
    match levels.try_send(value.clamp(0.0, 1.0)) {
        Ok(()) => {}
        Err(TrySendError::Full(value)) => {
            let _ = levels.try_send(value);
        }
        Err(TrySendError::Disconnected(_)) => {}
    }
}

fn enqueue_frame(
    frames: &Sender<Vec<u8>>,
    receiver: &Receiver<Vec<u8>>,
    frame: Vec<u8>,
    dropped_frames: &AtomicUsize,
) {
    match frames.try_send(frame) {
        Ok(()) => {}
        Err(TrySendError::Full(frame)) => {
            if matches!(receiver.try_recv(), Ok(_) | Err(TryRecvError::Empty)) {
                dropped_frames.fetch_add(1, Ordering::Relaxed);
                let _ = frames.try_send(frame);
            } else {
                dropped_frames.fetch_add(1, Ordering::Relaxed);
            }
        }
        Err(TrySendError::Disconnected(_)) => {}
    }
}

struct FrameAssembler {
    channels: usize,
    input_rate: f64,
    source: VecDeque<i16>,
    source_position: f64,
    output: Vec<i16>,
}

impl FrameAssembler {
    fn new(channels: u16, sample_rate: u32) -> Self {
        Self {
            channels: usize::from(channels.max(1)),
            input_rate: f64::from(sample_rate.max(1)),
            source: VecDeque::new(),
            source_position: 0.0,
            output: Vec::with_capacity(TARGET_FRAME_SAMPLES * 2),
        }
    }

    fn push_interleaved(&mut self, samples: &[i16]) -> Vec<Vec<u8>> {
        if self.channels == 0 {
            return Vec::new();
        }
        for frame in samples.chunks_exact(self.channels) {
            let sum = frame.iter().map(|sample| i32::from(*sample)).sum::<i32>();
            self.source.push_back(
                (sum / self.channels as i32).clamp(i16::MIN as i32, i16::MAX as i32) as i16,
            );
        }

        if (self.input_rate - f64::from(TARGET_SAMPLE_RATE)).abs() < f64::EPSILON {
            self.output.extend(self.source.drain(..));
            return self.take_output_frames();
        }

        let step = self.input_rate / f64::from(TARGET_SAMPLE_RATE);
        while self.source_position + 1.0 < self.source.len() as f64 {
            let index = self.source_position.floor() as usize;
            let fraction = self.source_position - index as f64;
            let first = self.source[index] as f64;
            let second = self.source[index + 1] as f64;
            self.output
                .push((first + (second - first) * fraction).round() as i16);
            self.source_position += step;
        }

        let consumed = self.source_position.floor() as usize;
        if consumed > 0 {
            self.source.drain(..consumed);
            self.source_position -= consumed as f64;
        }

        self.take_output_frames()
    }

    fn take_output_frames(&mut self) -> Vec<Vec<u8>> {
        let mut frames = Vec::new();
        while self.output.len() >= TARGET_FRAME_SAMPLES {
            let samples = self.output.drain(..TARGET_FRAME_SAMPLES);
            let mut bytes = Vec::with_capacity(TARGET_FRAME_SAMPLES * 2);
            for sample in samples {
                bytes.extend_from_slice(&sample.to_le_bytes());
            }
            frames.push(bytes);
        }
        frames
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn identity_is_stable_and_config_compatible() {
        let first = stable_device_identity("coreaudio:42", "Built-in Microphone", 2);
        let second = stable_device_identity("coreaudio:42", "Built-in Microphone", 2);
        assert_eq!(first, second);
        assert_eq!(first.len(), 24);
        assert!(first.chars().all(|character| character.is_ascii_hexdigit()));
    }

    #[test]
    fn identity_changes_when_backend_identity_changes() {
        assert_ne!(
            stable_device_identity("coreaudio:42", "Mic", 1),
            stable_device_identity("coreaudio:43", "Mic", 1)
        );
    }

    #[test]
    fn frame_assembler_downmixes_resamples_and_chunks() {
        let mut assembler = FrameAssembler::new(2, 48_000);
        let input = [10_000_i16, 20_000_i16].repeat(1_440);
        let frames = assembler.push_interleaved(&input);
        assert_eq!(frames.len(), 1);
        assert_eq!(frames[0].len(), TARGET_FRAME_SAMPLES * 2);
        let first = i16::from_le_bytes([frames[0][0], frames[0][1]]);
        assert_eq!(first, 15_000);
    }

    #[test]
    fn frame_assembler_keeps_partial_frames() {
        let mut assembler = FrameAssembler::new(1, TARGET_SAMPLE_RATE);
        let first = assembler.push_interleaved(&vec![1_i16; 240]);
        assert!(first.is_empty());
        let second = assembler.push_interleaved(&vec![2_i16; 240]);
        assert_eq!(second.len(), 1);
        assert_eq!(second[0].len(), TARGET_FRAME_SAMPLES * 2);
    }
}
