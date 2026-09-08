//! Explicit Groq transcription boundary.
//!
//! Only completed PCM speech segments cross this boundary. The worker keeps
//! the API key and HTTP details away from the UI, never includes credentials in
//! events or errors, and limits queued audio to a small in-memory backlog.

use std::io::Write;
use std::sync::{
    atomic::{AtomicBool, Ordering},
    Arc, Mutex,
};
use std::thread::{self, JoinHandle};
use std::time::Duration;

use crossbeam_channel::{bounded, unbounded, Receiver, Sender, TrySendError};
use reqwest::blocking::{multipart, Client};
use serde::Deserialize;
use thiserror::Error;

const GROQ_BASE_URL: &str = "https://api.groq.com/openai/v1/audio";
const TRANSCRIPTION_MODEL: &str = "whisper-large-v3-turbo";
const TRANSLATION_MODEL: &str = "whisper-large-v3";
const MAX_AUDIO_BYTES: usize = 5_120_000;
const MAX_RESPONSE_BYTES: usize = 1_000_000;
const MAX_PENDING_REQUESTS: usize = 4;

#[derive(Debug, Error, Clone, PartialEq, Eq)]
pub enum ProviderError {
    #[error("no Groq API key is configured")]
    NotConfigured,
    #[error("cloud transcription requires explicit consent in Settings")]
    ConsentRequired,
    #[error("captured speech audio is empty or malformed")]
    InvalidAudio,
    #[error("captured speech segment is too long")]
    AudioTooLarge,
    #[error("transcription queue is full; wait for a result before recording again")]
    QueueFull,
    #[error("the transcription provider is shutting down")]
    Closed,
    #[error("Groq rejected the configured API key")]
    Authentication,
    #[error("Groq is rate limiting requests; wait a moment and retry")]
    RateLimited,
    #[error("Groq returned HTTP status {0}")]
    HttpStatus(u16),
    #[error("could not reach Groq before the request timeout")]
    Network,
    #[error("Groq returned an unreadable response")]
    InvalidResponse,
    #[error("could not start the transcription worker: {0}")]
    WorkerStart(String),
}

#[derive(Clone, Debug, Default, PartialEq, Eq)]
pub struct GroqSettings {
    pub api_key: String,
    pub cloud_boundary_confirmed: bool,
    /// `None` means automatic language detection.
    pub language: Option<String>,
    pub translate_to_english: bool,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum RequestState {
    Pending,
    Transcribing,
    Complete,
    Error,
    Cancelled,
}

impl RequestState {
    pub fn label(self) -> &'static str {
        match self {
            Self::Pending => "Pending",
            Self::Transcribing => "Transcribing",
            Self::Complete => "Complete",
            Self::Error => "Error",
            Self::Cancelled => "Cancelled",
        }
    }
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct ProviderEvent {
    pub request_id: u64,
    /// Session generation selected by the UI. Late events from an invalidated
    /// session can be discarded without touching the current transcript.
    pub session_generation: u64,
    /// Monotonic submission order used by the transcript reducer.
    pub sequence: u64,
    pub state: RequestState,
    pub text: Option<String>,
    pub detail: String,
}

struct TranscriptionJob {
    request_id: u64,
    session_generation: u64,
    sequence: u64,
    audio: Vec<u8>,
    settings: GroqSettings,
}

pub struct GroqProvider {
    settings: Arc<Mutex<GroqSettings>>,
    jobs: Option<Sender<TranscriptionJob>>,
    event_sender: Sender<ProviderEvent>,
    events: Receiver<ProviderEvent>,
    closed: Arc<AtomicBool>,
    next_request_id: u64,
    worker: Option<JoinHandle<()>>,
}

impl GroqProvider {
    pub fn new(settings: GroqSettings) -> Result<Self, ProviderError> {
        let (job_tx, job_rx) = bounded::<TranscriptionJob>(MAX_PENDING_REQUESTS);
        let (event_tx, event_rx) = unbounded::<ProviderEvent>();
        let closed = Arc::new(AtomicBool::new(false));
        let worker_closed = Arc::clone(&closed);
        let worker_events = event_tx.clone();
        let worker = thread::Builder::new()
            .name("voice-transcriber-groq".into())
            .spawn(move || worker_loop(job_rx, worker_events, worker_closed))
            .map_err(|error| ProviderError::WorkerStart(error.to_string()))?;

        Ok(Self {
            settings: Arc::new(Mutex::new(settings)),
            jobs: Some(job_tx),
            event_sender: event_tx,
            events: event_rx,
            closed,
            next_request_id: 1,
            worker: Some(worker),
        })
    }

    pub fn settings(&self) -> GroqSettings {
        self.settings
            .lock()
            .map(|settings| settings.clone())
            .unwrap_or_default()
    }

    pub fn update_settings(&self, settings: GroqSettings) {
        if let Ok(mut current) = self.settings.lock() {
            *current = settings;
        }
    }

    pub fn configured(&self) -> bool {
        let settings = self.settings();
        settings.cloud_boundary_confirmed && plausible_api_key(&settings.api_key)
    }

    /// Queue one completed PCM segment. The request receives a stable sequence
    /// number before any worker thread can emit a result.
    pub fn submit(&mut self, audio: Vec<u8>) -> Result<u64, ProviderError> {
        self.submit_for_generation(audio, 0)
    }

    /// Queue a segment associated with a UI session generation. The default
    /// [`Self::submit`] helper remains useful to library callers that do not
    /// need stale-result isolation.
    pub fn submit_for_generation(
        &mut self,
        audio: Vec<u8>,
        session_generation: u64,
    ) -> Result<u64, ProviderError> {
        if self.closed.load(Ordering::Acquire) {
            return Err(ProviderError::Closed);
        }
        validate_audio(&audio)?;
        let settings = self.settings();
        if !settings.cloud_boundary_confirmed {
            return Err(ProviderError::ConsentRequired);
        }
        if !plausible_api_key(&settings.api_key) {
            return Err(ProviderError::NotConfigured);
        }

        let request_id = self.next_request_id;
        self.next_request_id = self.next_request_id.saturating_add(1);
        let job = TranscriptionJob {
            request_id,
            session_generation,
            sequence: request_id,
            audio,
            settings,
        };
        let sender = self.jobs.as_ref().ok_or(ProviderError::Closed)?;
        match sender.try_send(job) {
            Ok(()) => {
                // The event channel is unbounded and only carries metadata; a
                // bounded job queue keeps raw audio memory under control.
                self.emit(ProviderEvent {
                    request_id,
                    session_generation,
                    sequence: request_id,
                    state: RequestState::Pending,
                    text: None,
                    detail: "Waiting for Groq".into(),
                });
                Ok(request_id)
            }
            Err(TrySendError::Full(_)) => Err(ProviderError::QueueFull),
            Err(TrySendError::Disconnected(_)) => Err(ProviderError::Closed),
        }
    }

    pub fn try_recv_event(&self) -> Option<ProviderEvent> {
        self.events.try_recv().ok()
    }

    pub fn drain_events(&self) -> Vec<ProviderEvent> {
        self.events.try_iter().collect()
    }

    pub fn close(&mut self, wait: bool) {
        if self.closed.swap(true, Ordering::AcqRel) {
            return;
        }
        self.jobs.take();
        if wait {
            if let Some(worker) = self.worker.take() {
                let _ = worker.join();
            }
        }
    }

    fn emit(&self, event: ProviderEvent) {
        let _ = self.event_sender.send(event);
    }
}

impl Drop for GroqProvider {
    fn drop(&mut self) {
        self.close(false);
    }
}

fn worker_loop(
    jobs: Receiver<TranscriptionJob>,
    events: Sender<ProviderEvent>,
    closed: Arc<AtomicBool>,
) {
    let client = Client::builder()
        .timeout(Duration::from_secs(25))
        .user_agent("voice-transcriber/1")
        .build();
    while let Ok(job) = jobs.recv() {
        if closed.load(Ordering::Acquire) {
            let _ = events.send(ProviderEvent {
                request_id: job.request_id,
                session_generation: job.session_generation,
                sequence: job.sequence,
                state: RequestState::Cancelled,
                text: None,
                detail: "Provider is shutting down".into(),
            });
            continue;
        }
        let _ = events.send(ProviderEvent {
            request_id: job.request_id,
            session_generation: job.session_generation,
            sequence: job.sequence,
            state: RequestState::Transcribing,
            text: None,
            detail: "Sending completed speech to Groq".into(),
        });

        let result = match &client {
            Ok(client) => transcribe(client, &job),
            Err(_) => Err(ProviderError::Network),
        };
        let event = match result {
            Ok(text) if !text.is_empty() => ProviderEvent {
                request_id: job.request_id,
                session_generation: job.session_generation,
                sequence: job.sequence,
                state: RequestState::Complete,
                text: Some(text),
                detail: "Added to transcript".into(),
            },
            Ok(_) => ProviderEvent {
                request_id: job.request_id,
                session_generation: job.session_generation,
                sequence: job.sequence,
                state: RequestState::Error,
                text: None,
                detail: "Groq returned no transcript text".into(),
            },
            Err(error) => ProviderEvent {
                request_id: job.request_id,
                session_generation: job.session_generation,
                sequence: job.sequence,
                state: RequestState::Error,
                text: None,
                detail: error.to_string(),
            },
        };
        let _ = events.send(event);
    }
}

fn transcribe(client: &Client, job: &TranscriptionJob) -> Result<String, ProviderError> {
    let translate = job.settings.translate_to_english;
    let endpoint = if translate {
        "translations"
    } else {
        "transcriptions"
    };
    let model = if translate {
        TRANSLATION_MODEL
    } else {
        TRANSCRIPTION_MODEL
    };
    let wav = pcm_to_wav(&job.audio).map_err(|_| ProviderError::InvalidAudio)?;
    let file = multipart::Part::bytes(wav)
        .file_name("speech.wav")
        .mime_str("audio/wav")
        .map_err(|_| ProviderError::InvalidAudio)?;
    let mut form = multipart::Form::new()
        .part("file", file)
        .text("model", model)
        .text("response_format", "json");
    if !translate {
        if let Some(language) = job.settings.language.as_deref() {
            if !language.is_empty() && language != "auto" {
                form = form.text("language", language.to_owned());
            }
        }
    }
    let response = client
        .post(format!("{GROQ_BASE_URL}/{endpoint}"))
        .bearer_auth(&job.settings.api_key)
        .multipart(form)
        .send()
        .map_err(normalize_reqwest_error)?;
    let status = response.status();
    if status == reqwest::StatusCode::UNAUTHORIZED {
        return Err(ProviderError::Authentication);
    }
    if status == reqwest::StatusCode::TOO_MANY_REQUESTS {
        return Err(ProviderError::RateLimited);
    }
    if !status.is_success() {
        return Err(ProviderError::HttpStatus(status.as_u16()));
    }
    let bytes = response.bytes().map_err(|_| ProviderError::Network)?;
    if bytes.len() > MAX_RESPONSE_BYTES {
        return Err(ProviderError::InvalidResponse);
    }
    let payload: GroqResponse =
        serde_json::from_slice(&bytes).map_err(|_| ProviderError::InvalidResponse)?;
    Ok(payload.text.trim().to_owned())
}

#[derive(Deserialize)]
struct GroqResponse {
    text: String,
}

fn normalize_reqwest_error(error: reqwest::Error) -> ProviderError {
    if error.is_timeout() || error.is_connect() || error.is_request() {
        ProviderError::Network
    } else {
        ProviderError::InvalidResponse
    }
}

pub fn plausible_api_key(key: &str) -> bool {
    let key = key.trim();
    key.len() >= 10 && !key.to_ascii_lowercase().contains("your_api_key")
}

pub fn validate_audio(audio: &[u8]) -> Result<(), ProviderError> {
    if audio.is_empty() || audio.len() % 2 != 0 {
        return Err(ProviderError::InvalidAudio);
    }
    if audio.len() > MAX_AUDIO_BYTES {
        return Err(ProviderError::AudioTooLarge);
    }
    Ok(())
}

/// Wrap little-endian mono PCM16 in a minimal RIFF/WAVE container.
pub fn pcm_to_wav(pcm: &[u8]) -> Result<Vec<u8>, ProviderError> {
    validate_audio(pcm)?;
    let data_len = u32::try_from(pcm.len()).map_err(|_| ProviderError::AudioTooLarge)?;
    let riff_len = 36_u32
        .checked_add(data_len)
        .ok_or(ProviderError::AudioTooLarge)?;
    let mut wav = Vec::with_capacity(44 + pcm.len());
    wav.write_all(b"RIFF").expect("Vec cannot fail");
    wav.write_all(&riff_len.to_le_bytes())
        .expect("Vec cannot fail");
    wav.write_all(b"WAVEfmt ").expect("Vec cannot fail");
    wav.write_all(&16_u32.to_le_bytes())
        .expect("Vec cannot fail");
    wav.write_all(&1_u16.to_le_bytes())
        .expect("Vec cannot fail");
    wav.write_all(&1_u16.to_le_bytes())
        .expect("Vec cannot fail");
    wav.write_all(&16_000_u32.to_le_bytes())
        .expect("Vec cannot fail");
    wav.write_all(&32_000_u32.to_le_bytes())
        .expect("Vec cannot fail");
    wav.write_all(&2_u16.to_le_bytes())
        .expect("Vec cannot fail");
    wav.write_all(&16_u16.to_le_bytes())
        .expect("Vec cannot fail");
    wav.write_all(b"data").expect("Vec cannot fail");
    wav.write_all(&data_len.to_le_bytes())
        .expect("Vec cannot fail");
    wav.extend_from_slice(pcm);
    Ok(wav)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn keys_are_checked_without_logging_or_persisting_them() {
        assert!(!plausible_api_key("short"));
        assert!(!plausible_api_key("your_api_key_here"));
        assert!(plausible_api_key("gsk_test_key_123"));
    }

    #[test]
    fn wav_header_describes_target_pcm_contract() {
        let wav = pcm_to_wav(&[0, 0, 1, 0]).unwrap();
        assert_eq!(&wav[0..4], b"RIFF");
        assert_eq!(&wav[8..12], b"WAVE");
        assert_eq!(u32::from_le_bytes(wav[24..28].try_into().unwrap()), 16_000);
        assert_eq!(&wav[36..40], b"data");
        assert_eq!(&wav[44..], &[0, 0, 1, 0]);
    }

    #[test]
    fn invalid_audio_is_rejected_before_queueing() {
        assert_eq!(validate_audio(&[]), Err(ProviderError::InvalidAudio));
        assert_eq!(validate_audio(&[1]), Err(ProviderError::InvalidAudio));
    }

    #[test]
    fn provider_requires_consent_and_key() {
        let mut provider = GroqProvider::new(GroqSettings::default()).unwrap();
        assert_eq!(
            provider.submit(vec![0, 0]),
            Err(ProviderError::ConsentRequired)
        );
        provider.update_settings(GroqSettings {
            cloud_boundary_confirmed: true,
            ..GroqSettings::default()
        });
        assert_eq!(
            provider.submit(vec![0, 0]),
            Err(ProviderError::NotConfigured)
        );
        provider.close(true);
    }
}
