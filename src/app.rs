//! Native egui desktop application for the Rust rewrite.

use std::time::{Duration, Instant};

use arboard::Clipboard;
use eframe::egui::{self, Color32, RichText, TextEdit, TextStyle};
use eframe::{App, CreationContext, Frame};
use rfd::FileDialog;

use crate::audio::{list_input_devices, AudioCapture, InputDevice};
use crate::config::{AppConfig, ConfigStore};
use crate::exports::{build_export, write_export, ExportFormat};
use crate::history::HistoryStore;
use crate::provider::{GroqProvider, GroqSettings, ProviderEvent, RequestState};
use crate::transcript::{SegmentStatus, Transcript};
use crate::vad::VoiceActivityDetector;

const BACKGROUND: Color32 = Color32::from_rgb(17, 25, 24);
const SURFACE: Color32 = Color32::from_rgb(27, 38, 36);
const SURFACE_MUTED: Color32 = Color32::from_rgb(35, 48, 45);
const ACCENT: Color32 = Color32::from_rgb(126, 211, 166);
const TEXT: Color32 = Color32::from_rgb(237, 244, 239);
const MUTED: Color32 = Color32::from_rgb(163, 184, 174);

pub struct VoiceTranscriberApp {
    config_store: ConfigStore,
    config: AppConfig,
    api_key_draft: String,
    provider: GroqProvider,
    transcript: Transcript,
    vad: VoiceActivityDetector,
    capture: Option<AudioCapture>,
    devices: Vec<InputDevice>,
    level: f32,
    test_mode: bool,
    show_settings: bool,
    status: String,
    error: Option<String>,
    last_saved: Option<Instant>,
}

impl VoiceTranscriberApp {
    pub fn new(cc: &CreationContext<'_>) -> Result<Self, String> {
        let config_store = ConfigStore::new().map_err(|error| error.to_string())?;
        let (mut config, load_warning) = match config_store.load() {
            Ok(config) => (config, None),
            Err(error) => (AppConfig::default(), Some(error.to_string())),
        };
        if config.validate().is_err() {
            config = AppConfig::default();
        }
        let provider =
            GroqProvider::new(settings_from_config(&config)).map_err(|error| error.to_string())?;
        let devices = list_input_devices().unwrap_or_default();
        let app = Self {
            config_store,
            api_key_draft: config.api_key.clone(),
            config,
            provider,
            transcript: Transcript::default(),
            vad: VoiceActivityDetector::new(16_000, 30, 2, 500, 300, 20_000)
                .map_err(|error| error.to_string())?,
            capture: None,
            devices,
            level: 0.0,
            test_mode: false,
            show_settings: false,
            status: "Ready for a local microphone".into(),
            error: load_warning,
            last_saved: None,
        };
        app.apply_style(cc);
        Ok(app)
    }

    fn apply_style(&self, cc: &CreationContext<'_>) {
        cc.egui_ctx.set_visuals(egui::Visuals {
            dark_mode: true,
            override_text_color: Some(TEXT),
            panel_fill: BACKGROUND,
            window_fill: SURFACE,
            faint_bg_color: SURFACE_MUTED,
            extreme_bg_color: Color32::from_rgb(12, 18, 17),
            ..egui::Visuals::dark()
        });
        let mut style = (*cc.egui_ctx.style_of(egui::Theme::Dark)).clone();
        style.spacing.item_spacing = egui::vec2(10.0, 8.0);
        style.spacing.button_padding = egui::vec2(14.0, 8.0);
        style.text_styles.insert(
            TextStyle::Body,
            egui::FontId::proportional(self.config.font_size as f32),
        );
        style.text_styles.insert(
            TextStyle::Button,
            egui::FontId::proportional(self.config.font_size as f32),
        );
        cc.egui_ctx.set_style_of(egui::Theme::Dark, style);
    }

    fn sync_provider(&self) {
        self.provider
            .update_settings(settings_from_config(&self.config));
    }

    fn save_settings(&mut self) {
        self.config.api_key = self.api_key_draft.trim().to_owned();
        match self
            .config
            .validate()
            .and_then(|_| self.config_store.save(&self.config))
        {
            Ok(()) => {
                self.sync_provider();
                self.last_saved = Some(Instant::now());
                self.error = None;
                self.status = "Settings saved locally".into();
            }
            Err(error) => self.error = Some(error.to_string()),
        }
    }

    fn refresh_devices(&mut self) {
        match list_input_devices() {
            Ok(devices) => {
                self.devices = devices;
                self.status = format!("{} input device(s) detected", self.devices.len());
                self.error = None;
            }
            Err(error) => self.error = Some(error.to_string()),
        }
    }

    fn begin_capture(&mut self, test_mode: bool) {
        if !test_mode && !self.provider.configured() {
            self.error = Some(
                "Configure a Groq key and confirm the cloud boundary before recording.".into(),
            );
            self.show_settings = true;
            return;
        }
        if self.capture.is_some() {
            return;
        }
        let identity = (!self.config.input_device_identity.is_empty())
            .then_some(self.config.input_device_identity.as_str());
        match AudioCapture::open(self.config.input_device_index, identity) {
            Ok(capture) => {
                self.config.input_device_index = Some(capture.device().index);
                self.config.input_device_identity = capture.device().identity.clone();
                self.test_mode = test_mode;
                self.vad = VoiceActivityDetector::new(16_000, 30, 2, 500, 300, 20_000)
                    .expect("static VAD configuration is valid");
                self.capture = Some(capture);
                self.level = 0.0;
                self.error = None;
                self.status = if test_mode {
                    "Microphone test is running — speak, then stop".into()
                } else {
                    "Listening — speak naturally, then stop".into()
                };
            }
            Err(error) => self.error = Some(error.to_string()),
        }
    }

    fn stop_capture(&mut self) {
        if let Some(mut capture) = self.capture.take() {
            capture.stop();
        }
        if !self.test_mode {
            if let Some(segment) = self.vad.flush() {
                self.submit_segment(segment);
            }
        } else {
            self.vad.flush();
        }
        self.level = 0.0;
        self.status = "Capture stopped — review the transcript before sharing".into();
        self.test_mode = false;
    }

    fn poll_audio(&mut self) {
        let mut frames = Vec::new();
        if let Some(capture) = self.capture.as_ref() {
            if let Some(level) = capture.try_recv_level() {
                self.level = level;
            }
            while let Some(frame) = capture.try_recv_frame() {
                frames.push(frame);
            }
            if let Some(error) = capture.try_recv_error() {
                self.error = Some(format!("Audio stream stopped: {error}"));
            }
        }
        for frame in frames {
            if let Some(segment) = self.vad.process_frame(&frame) {
                if !self.test_mode {
                    self.submit_segment(segment);
                }
            }
        }
    }

    fn submit_segment(&mut self, segment: Vec<u8>) {
        match self.provider.submit(segment) {
            Ok(request_id) => {
                self.status = format!("Speech segment {request_id} queued for transcription");
                self.error = None;
            }
            Err(error) => self.error = Some(error.to_string()),
        }
    }

    fn poll_provider(&mut self) {
        for event in self.provider.drain_events() {
            self.apply_provider_event(event);
        }
    }

    fn apply_provider_event(&mut self, event: ProviderEvent) {
        let text = event.text.clone().unwrap_or_default();
        let status = match event.state {
            RequestState::Pending => SegmentStatus::Pending,
            RequestState::Transcribing => SegmentStatus::Transcribing,
            RequestState::Complete => SegmentStatus::Complete,
            RequestState::Error => SegmentStatus::Error,
            RequestState::Cancelled => SegmentStatus::Cancelled,
        };
        self.transcript.update_segment(
            event.sequence,
            status,
            text.clone(),
            Some(event.detail.clone()),
        );
        match event.state {
            RequestState::Complete => {
                self.status = event.detail;
                self.error = None;
                if self.config.copy_on_final && !text.is_empty() {
                    let _ = copy_text(&text);
                }
            }
            RequestState::Error => self.error = Some(event.detail),
            RequestState::Cancelled => self.status = event.detail,
            RequestState::Pending | RequestState::Transcribing => self.status = event.detail,
        }
    }

    fn copy_transcript(&mut self) {
        match copy_text(self.transcript.text()) {
            Ok(()) => {
                self.status = "Transcript copied to the system clipboard".into();
                self.error = None;
            }
            Err(error) => self.error = Some(error),
        }
    }

    fn export_transcript(&mut self, format: ExportFormat) {
        let Ok(document) = build_export(self.transcript.text(), format) else {
            self.error = Some("Could not build the export document".into());
            return;
        };
        let Some(path) = FileDialog::new()
            .set_file_name(document.suggested_name.clone())
            .save_file()
        else {
            return;
        };
        match write_export(&path, &document) {
            Ok(()) => {
                self.status = format!("Exported transcript to {}", path.display());
                self.error = None;
            }
            Err(error) => self.error = Some(error.to_string()),
        }
    }

    fn save_history(&mut self) {
        if !self.config.history_enabled {
            self.error = Some("Enable text-only history in Settings first".into());
            return;
        }
        let Some(parent) = self.config_store.path().parent() else {
            self.error = Some("Could not locate the app data directory".into());
            return;
        };
        let store = HistoryStore::at(parent.join("history"));
        match store.add(self.transcript.text(), self.config.history_retention_days) {
            Ok(_) => {
                self.status = "Saved a text-only copy to local history".into();
                self.error = None;
            }
            Err(error) => self.error = Some(error.to_string()),
        }
    }

    fn render_header(&mut self, ui: &mut egui::Ui) {
        ui.horizontal(|ui| {
            ui.heading(RichText::new("Voice Transcriber").color(ACCENT).strong());
            ui.label(RichText::new("review-first desktop dictation").color(MUTED));
            ui.with_layout(egui::Layout::right_to_left(egui::Align::Center), |ui| {
                ui.label(RichText::new(format!("v{}", crate::VERSION)).color(MUTED));
            });
        });
        ui.add_space(4.0);
        ui.label(
            RichText::new(
                "Capture locally, inspect the ordered result, then decide what to copy or export.",
            )
            .color(MUTED),
        );
    }

    fn render_capture_card(&mut self, ui: &mut egui::Ui) {
        egui::Frame::group(ui.style())
            .fill(SURFACE)
            .corner_radius(egui::CornerRadius::same(12))
            .inner_margin(egui::Margin::same(16))
            .show(ui, |ui| {
                ui.horizontal(|ui| {
                    let is_recording = self.capture.is_some();
                    let start_label = if is_recording {
                        "Listening…"
                    } else {
                        "Start listening"
                    };
                    if ui
                        .add_enabled(
                            !is_recording,
                            egui::Button::new(RichText::new(start_label).strong()),
                        )
                        .clicked()
                    {
                        self.begin_capture(false);
                    }
                    if ui
                        .add_enabled(is_recording, egui::Button::new("Stop"))
                        .clicked()
                    {
                        self.stop_capture();
                    }
                    if ui
                        .add_enabled(!is_recording, egui::Button::new("Test microphone"))
                        .clicked()
                    {
                        self.begin_capture(true);
                    }
                    ui.separator();
                    ui.label(RichText::new(&self.status).color(MUTED));
                });
                ui.add_space(10.0);
                ui.horizontal(|ui| {
                    ui.label("Input level");
                    let meter = egui::ProgressBar::new(self.level)
                        .desired_width(220.0)
                        .show_percentage();
                    ui.add(meter);
                    if let Some(capture) = self.capture.as_ref() {
                        ui.label(
                            RichText::new(format!(
                                "{} · {} Hz · {} channel(s)",
                                capture.device().name,
                                capture.device().sample_rate,
                                capture.device().channels
                            ))
                            .color(MUTED),
                        );
                    }
                });
            });
    }

    fn render_transcript_card(&mut self, ui: &mut egui::Ui) {
        egui::Frame::group(ui.style())
            .fill(SURFACE)
            .corner_radius(egui::CornerRadius::same(12))
            .inner_margin(egui::Margin::same(16))
            .show(ui, |ui| {
                ui.horizontal(|ui| {
                    ui.heading("Transcript");
                    ui.label(RichText::new("Editable review").color(MUTED));
                    ui.with_layout(egui::Layout::right_to_left(egui::Align::Center), |ui| {
                        if ui.button("Redo").clicked() {
                            self.transcript.redo();
                        }
                        if ui.button("Undo").clicked() {
                            self.transcript.undo();
                        }
                        if ui.button("Clear").clicked() {
                            self.transcript.clear();
                        }
                    });
                });
                ui.add_space(8.0);
                let mut edited = self.transcript.text().to_owned();
                let response = ui.add_sized(
                    [ui.available_width(), 230.0],
                    TextEdit::multiline(&mut edited)
                        .hint_text("Your reviewed transcript will appear here…")
                        .desired_rows(9),
                );
                if response.changed() {
                    self.transcript.set_text(edited);
                }
                ui.add_space(8.0);
                ui.horizontal_wrapped(|ui| {
                    if ui.button("Copy transcript").clicked() {
                        self.copy_transcript();
                    }
                    if ui.button("Export .txt").clicked() {
                        self.export_transcript(ExportFormat::Text);
                    }
                    if ui.button("Export Markdown").clicked() {
                        self.export_transcript(ExportFormat::Markdown);
                    }
                    if ui
                        .add_enabled(
                            self.config.history_enabled,
                            egui::Button::new("Save to history"),
                        )
                        .clicked()
                    {
                        self.save_history();
                    }
                });
            });
    }

    fn render_segments(&self, ui: &mut egui::Ui) {
        let segments = self.transcript.segments();
        if segments.is_empty() {
            return;
        }
        ui.add_space(12.0);
        egui::CollapsingHeader::new(format!("{} speech segment(s)", segments.len()))
            .default_open(false)
            .show(ui, |ui| {
                for segment in segments {
                    ui.horizontal(|ui| {
                        ui.label(RichText::new(format!("#{:02}", segment.sequence)).color(ACCENT));
                        ui.label(segment.status.label());
                        if !segment.text.is_empty() {
                            ui.label(segment.text.clone());
                        } else if let Some(detail) = &segment.detail {
                            ui.label(RichText::new(detail).color(MUTED));
                        }
                    });
                }
            });
    }

    fn render_settings(&mut self, ui: &mut egui::Ui) {
        ui.add_space(12.0);
        egui::CollapsingHeader::new("Settings and privacy").default_open(self.show_settings).show(ui, |ui| {
            self.show_settings = true;
            egui::Frame::group(ui.style())
                .fill(SURFACE_MUTED)
                .corner_radius(egui::CornerRadius::same(10))
                .inner_margin(egui::Margin::same(14))
                .show(ui, |ui| {
                    ui.label(RichText::new("Provider boundary").strong());
                    ui.label(
                        RichText::new(
                            "Only completed speech segments leave this computer, and only after this consent is enabled.",
                        )
                        .color(MUTED),
                    );
                    ui.checkbox(
                        &mut self.config.cloud_boundary_confirmed,
                        "I understand that completed speech is sent to Groq over HTTPS",
                    );
                    ui.horizontal(|ui| {
                        ui.label("Groq API key");
                        ui.add(
                            TextEdit::singleline(&mut self.api_key_draft)
                                .password(true)
                                .hint_text("GROQ_API_KEY or a saved key"),
                        );
                        if std::env::var("GROQ_API_KEY").map(|value| !value.trim().is_empty()).unwrap_or(false) {
                            ui.label(RichText::new("environment key detected").color(ACCENT));
                        }
                    });
                    ui.horizontal(|ui| {
                        ui.label("Language");
                        egui::ComboBox::from_id_salt("language")
                            .selected_text(self.config.language.clone())
                            .show_ui(ui, |ui| {
                                for language in ["auto", "en", "fr", "es", "de", "it", "pt", "ar", "zh"] {
                                    ui.selectable_value(&mut self.config.language, language.into(), language);
                                }
                            });
                        ui.checkbox(&mut self.config.translate_to_english, "Translate to English");
                    });
                    ui.checkbox(&mut self.config.copy_on_final, "Copy each completed segment automatically");
                    ui.checkbox(&mut self.config.history_enabled, "Enable bounded text-only local history");
                    ui.horizontal(|ui| {
                        ui.label("Input device");
                        let selected = self
                            .config
                            .input_device_index
                            .and_then(|index| self.devices.iter().find(|device| device.index == index))
                            .map(|device| device.name.clone())
                            .unwrap_or_else(|| "System default".into());
                        egui::ComboBox::from_id_salt("input-device")
                            .selected_text(selected)
                            .show_ui(ui, |ui| {
                                for device in &self.devices {
                                    if ui
                                        .selectable_value(
                                            &mut self.config.input_device_index,
                                            Some(device.index),
                                            format!("{}{}", device.name, if device.is_default { " (default)" } else { "" }),
                                        )
                                        .clicked()
                                    {
                                        self.config.input_device_identity = device.identity.clone();
                                    }
                                }
                            });
                        if ui.button("Refresh").clicked() {
                            self.refresh_devices();
                        }
                    });
                    ui.horizontal(|ui| {
                        if ui.button("Save settings").clicked() {
                            self.save_settings();
                        }
                        if ui.button("Reset transcript").clicked() {
                            self.transcript.clear();
                            self.status = "Transcript cleared".into();
                        }
                        if let Some(saved) = self.last_saved {
                            ui.label(RichText::new(format!("saved {}s ago", saved.elapsed().as_secs())).color(MUTED));
                        }
                    });
                });
        });
    }
}

impl App for VoiceTranscriberApp {
    fn ui(&mut self, ui: &mut egui::Ui, _frame: &mut Frame) {
        self.poll_audio();
        self.poll_provider();
        ui.ctx().request_repaint_after(Duration::from_millis(50));
        egui::CentralPanel::default()
            .frame(
                egui::Frame::central_panel(ui.style())
                    .fill(BACKGROUND)
                    .inner_margin(egui::Margin::same(22)),
            )
            .show(ui, |ui| {
                self.render_header(ui);
                ui.add_space(16.0);
                self.render_capture_card(ui);
                ui.add_space(14.0);
                self.render_transcript_card(ui);
                self.render_segments(ui);
                self.render_settings(ui);
                if let Some(error) = &self.error {
                    ui.add_space(10.0);
                    ui.label(RichText::new(error).color(Color32::from_rgb(255, 157, 145)));
                }
            });
    }

    fn on_exit(&mut self, _gl: Option<&eframe::glow::Context>) {
        if self.capture.is_some() {
            self.stop_capture();
        }
        self.save_settings();
        self.provider.close(true);
    }
}

fn settings_from_config(config: &AppConfig) -> GroqSettings {
    GroqSettings {
        api_key: config.effective_api_key(),
        cloud_boundary_confirmed: config.cloud_boundary_confirmed,
        language: (config.language != "auto").then_some(config.language.clone()),
        translate_to_english: config.translate_to_english,
    }
}

fn copy_text(text: &str) -> Result<(), String> {
    let mut clipboard =
        Clipboard::new().map_err(|error| format!("Clipboard unavailable: {error}"))?;
    clipboard
        .set_text(text.to_owned())
        .map_err(|error| format!("Could not copy transcript: {error}"))
}
