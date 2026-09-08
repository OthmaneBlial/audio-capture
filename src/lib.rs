//! Cross-platform Rust core for Voice Transcriber.
//!
//! The library deliberately keeps storage, transcript state, VAD, and provider
//! contracts independent from the desktop toolkit. The native UI and audio
//! backends are thin adapters around these contracts.

pub mod audio;
pub mod config;
pub mod exports;
pub mod history;
pub mod transcript;
pub mod vad;

pub const APP_ID: &str = "io.github.othmaneblial.audio_capture";
pub const APP_NAME: &str = "Voice Transcriber";
pub const VERSION: &str = env!("CARGO_PKG_VERSION");
