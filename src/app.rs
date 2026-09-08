//! Native egui desktop application for the Rust rewrite.

use std::time::{Duration, Instant};

use arboard::Clipboard;
use eframe::egui::{self, Color32, RichText, Stroke, TextEdit, TextStyle};
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
const ACCENT_STRONG: Color32 = Color32::from_rgb(47, 143, 105);
const WARNING: Color32 = Color32::from_rgb(244, 190, 102);
const DANGER: Color32 = Color32::from_rgb(255, 125, 116);
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
    session_generation: u64,
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
            session_generation: 1,
        };
        app.apply_style(cc);
        Ok(app)
    }

    fn apply_style(&self, cc: &CreationContext<'_>) {
        let mut visuals = egui::Visuals::dark();
        visuals.override_text_color = Some(TEXT);
        visuals.weak_text_color = Some(MUTED);
        visuals.panel_fill = BACKGROUND;
        visuals.window_fill = SURFACE;
        visuals.window_stroke = Stroke::new(1.0, Color32::from_rgb(72, 96, 87));
        visuals.faint_bg_color = SURFACE_MUTED;
        visuals.extreme_bg_color = Color32::from_rgb(12, 18, 17);
        visuals.text_edit_bg_color = Some(Color32::from_rgb(22, 31, 29));
        visuals.selection.bg_fill = Color32::from_rgb(50, 96, 76);
        visuals.selection.stroke = Stroke::new(1.0, ACCENT);
        visuals.widgets.noninteractive.bg_fill = SURFACE;
        visuals.widgets.noninteractive.fg_stroke = Stroke::new(1.0, TEXT);
        visuals.widgets.noninteractive.bg_stroke = Stroke::new(1.0, Color32::from_rgb(70, 96, 86));
        visuals.widgets.inactive.bg_fill = SURFACE_MUTED;
        visuals.widgets.inactive.weak_bg_fill = SURFACE_MUTED;
        visuals.widgets.inactive.fg_stroke = Stroke::new(1.0, TEXT);
        visuals.widgets.inactive.bg_stroke = Stroke::new(1.0, Color32::from_rgb(91, 119, 106));
        visuals.widgets.hovered.bg_fill = Color32::from_rgb(54, 76, 68);
        visuals.widgets.hovered.weak_bg_fill = Color32::from_rgb(54, 76, 68);
        visuals.widgets.hovered.fg_stroke = Stroke::new(1.0, TEXT);
        visuals.widgets.hovered.bg_stroke = Stroke::new(1.0, ACCENT);
        visuals.widgets.active.bg_fill = ACCENT_STRONG;
        visuals.widgets.active.weak_bg_fill = ACCENT_STRONG;
        visuals.widgets.active.fg_stroke = Stroke::new(1.0, TEXT);
        visuals.widgets.active.bg_stroke = Stroke::new(1.0, ACCENT);
        visuals.widgets.open.bg_fill = Color32::from_rgb(54, 76, 68);
        visuals.widgets.open.weak_bg_fill = Color32::from_rgb(54, 76, 68);
        visuals.widgets.open.fg_stroke = Stroke::new(1.0, TEXT);
        visuals.widgets.open.bg_stroke = Stroke::new(1.0, ACCENT);
        visuals.button_frame = true;
        visuals.collapsing_header_frame = false;

        // eframe follows the host appearance by default. Select the dark
        // palette explicitly so the configured visuals are applied on macOS,
        // Linux and Windows alike instead of falling back to a light editor.
        cc.egui_ctx.set_theme(egui::Theme::Dark);
        let mut style = (*cc.egui_ctx.style_of(egui::Theme::Dark)).clone();
        style.visuals = visuals;
        style.spacing.item_spacing = egui::vec2(10.0, 8.0);
        style.spacing.button_padding = egui::vec2(15.0, 9.0);
        style.spacing.interact_size = egui::vec2(40.0, 36.0);
        style.text_styles.insert(
            TextStyle::Body,
            egui::FontId::proportional(self.config.font_size as f32),
        );
        style.text_styles.insert(
            TextStyle::Button,
            egui::FontId::proportional(self.config.font_size as f32),
        );
        style.text_styles.insert(
            TextStyle::Heading,
            egui::FontId::proportional((self.config.font_size as f32 + 9.0).min(30.0)),
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
        self.invalidate_session();
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
        match self
            .provider
            .submit_for_generation(segment, self.session_generation)
        {
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
        if !event_is_current_generation(&event, self.session_generation) {
            return;
        }
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

    fn invalidate_session(&mut self) {
        self.session_generation = self.session_generation.saturating_add(1);
    }

    fn clear_transcript(&mut self) {
        self.invalidate_session();
        self.transcript.clear();
        self.status = "Transcript cleared".into();
        self.error = None;
    }

    fn status_color(&self) -> Color32 {
        if self.error.is_some() {
            DANGER
        } else if self.capture.is_some() {
            ACCENT
        } else {
            MUTED
        }
    }

    fn status_label(&self) -> &'static str {
        if self.error.is_some() {
            "ATTENTION"
        } else if self.capture.is_some() {
            if self.test_mode {
                "MIC CHECK"
            } else {
                "LISTENING"
            }
        } else {
            "READY"
        }
    }

    fn badge(ui: &mut egui::Ui, label: impl Into<String>, color: Color32) {
        egui::Frame::new()
            .fill(Color32::from_rgba_unmultiplied(
                color.r(),
                color.g(),
                color.b(),
                32,
            ))
            .stroke(Stroke::new(
                1.0,
                Color32::from_rgba_unmultiplied(color.r(), color.g(), color.b(), 110),
            ))
            .corner_radius(egui::CornerRadius::same(7))
            .inner_margin(egui::Margin::same(7))
            .show(ui, |ui| {
                ui.label(RichText::new(label.into()).size(11.0).color(color).strong());
            });
    }

    fn primary_button(ui: &mut egui::Ui, label: impl Into<String>) -> egui::Response {
        ui.add(
            egui::Button::new(RichText::new(label.into()).color(BACKGROUND).strong())
                .fill(ACCENT)
                .stroke(Stroke::new(1.0, ACCENT))
                .corner_radius(egui::CornerRadius::same(8)),
        )
    }

    fn draw_backdrop(ui: &egui::Ui) {
        let rect = ui.max_rect();
        let painter = ui.painter();
        painter.circle_filled(
            egui::pos2(rect.right() - 30.0, rect.top() + 28.0),
            185.0,
            Color32::from_rgba_unmultiplied(45, 125, 94, 18),
        );
        painter.circle_filled(
            egui::pos2(rect.left() + 35.0, rect.bottom() - 30.0),
            140.0,
            Color32::from_rgba_unmultiplied(30, 92, 93, 14),
        );
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
            egui::Frame::new()
                .fill(Color32::from_rgba_unmultiplied(126, 211, 166, 28))
                .stroke(Stroke::new(
                    1.0,
                    Color32::from_rgba_unmultiplied(126, 211, 166, 100),
                ))
                .corner_radius(egui::CornerRadius::same(12))
                .inner_margin(egui::Margin::same(11))
                .show(ui, |ui| {
                    ui.label(RichText::new("◌").size(25.0).color(ACCENT).strong());
                });
            ui.add_space(2.0);
            ui.vertical(|ui| {
                ui.label(
                    RichText::new("VOICE / TRANSCRIBER")
                        .size(11.0)
                        .color(ACCENT)
                        .strong(),
                );
                ui.label(
                    RichText::new("Speak. See it. Shape it.")
                        .size(27.0)
                        .color(TEXT)
                        .strong(),
                );
            });
            ui.with_layout(egui::Layout::right_to_left(egui::Align::Min), |ui| {
                ui.vertical(|ui| {
                    Self::badge(ui, self.status_label(), self.status_color());
                    ui.label(
                        RichText::new(format!("v{} · native desktop", crate::VERSION))
                            .size(11.0)
                            .color(MUTED),
                    );
                });
            });
        });
        ui.add_space(13.0);
        ui.label(
            RichText::new(
                "A calm place to dictate: your voice is captured locally, then each finished segment becomes an editable draft.",
            )
            .size(15.0)
            .color(MUTED),
        );
    }

    fn render_capture_card(&mut self, ui: &mut egui::Ui) {
        egui::Frame::group(ui.style())
            .fill(SURFACE)
            .stroke(Stroke::new(1.0, Color32::from_rgb(56, 78, 71)))
            .corner_radius(egui::CornerRadius::same(12))
            .inner_margin(egui::Margin::same(18))
            .show(ui, |ui| {
                ui.horizontal(|ui| {
                    ui.vertical(|ui| {
                        ui.label(
                            RichText::new("CAPTURE DESK")
                                .size(11.0)
                                .color(ACCENT)
                                .strong(),
                        );
                        ui.label(
                            RichText::new("Turn a thought into a draft")
                                .size(19.0)
                                .color(TEXT)
                                .strong(),
                        );
                    });
                    ui.with_layout(egui::Layout::right_to_left(egui::Align::Center), |ui| {
                        Self::badge(ui, self.status_label(), self.status_color());
                    });
                });
                ui.add_space(15.0);
                ui.horizontal_wrapped(|ui| {
                    let is_recording = self.capture.is_some();
                    if is_recording {
                        let stop = ui.add(
                            egui::Button::new(
                                RichText::new("■  Stop capture").color(TEXT).strong(),
                            )
                            .fill(Color32::from_rgb(113, 47, 46))
                            .stroke(Stroke::new(1.0, DANGER))
                            .corner_radius(egui::CornerRadius::same(8)),
                        );
                        if stop.clicked() {
                            self.stop_capture();
                        }
                    } else if Self::primary_button(ui, "●  Start listening").clicked() {
                        self.begin_capture(false);
                    }
                    if !is_recording
                        && ui
                            .add(
                                egui::Button::new(RichText::new("⌁  Test microphone").color(TEXT))
                                    .fill(SURFACE_MUTED)
                                    .stroke(Stroke::new(1.0, Color32::from_rgb(70, 98, 87)))
                                    .corner_radius(egui::CornerRadius::same(8)),
                            )
                            .clicked()
                    {
                        self.begin_capture(true);
                    }
                    ui.label(RichText::new(&self.status).size(13.0).color(MUTED));
                });
                ui.add_space(13.0);
                ui.horizontal(|ui| {
                    ui.label(RichText::new("SIGNAL").size(11.0).color(MUTED).strong());
                    let meter = egui::ProgressBar::new(self.level)
                        .desired_width((ui.available_width() * 0.42).clamp(150.0, 280.0))
                        .fill(if self.capture.is_some() {
                            ACCENT
                        } else {
                            SURFACE_MUTED
                        })
                        .text(format!("{:02}%", (self.level * 100.0).round() as u8));
                    ui.add(meter);
                    if let Some(capture) = self.capture.as_ref() {
                        ui.label(
                            RichText::new(format!(
                                "{}  ·  {} Hz  ·  {} ch",
                                capture.device().name,
                                capture.device().sample_rate,
                                capture.device().channels
                            ))
                            .color(MUTED),
                        );
                    } else {
                        ui.label(
                            RichText::new("No audio leaves this card until a segment is complete")
                                .size(12.0)
                                .color(MUTED),
                        );
                    }
                });
            });
    }

    fn render_transcript_card(&mut self, ui: &mut egui::Ui) {
        egui::Frame::group(ui.style())
            .fill(SURFACE)
            .stroke(Stroke::new(1.0, Color32::from_rgb(56, 78, 71)))
            .corner_radius(egui::CornerRadius::same(12))
            .inner_margin(egui::Margin::same(18))
            .show(ui, |ui| {
                ui.horizontal(|ui| {
                    ui.vertical(|ui| {
                        ui.label(
                            RichText::new("DRAFT TRANSCRIPT")
                                .size(11.0)
                                .color(ACCENT)
                                .strong(),
                        );
                        ui.label(
                            RichText::new("Review before you share")
                                .size(19.0)
                                .color(TEXT)
                                .strong(),
                        );
                    });
                    ui.with_layout(egui::Layout::right_to_left(egui::Align::Center), |ui| {
                        Self::badge(
                            ui,
                            format!("{} segment(s)", self.transcript.segments().len()),
                            MUTED,
                        );
                    });
                });
                ui.add_space(12.0);
                ui.horizontal(|ui| {
                    ui.with_layout(egui::Layout::right_to_left(egui::Align::Center), |ui| {
                        if ui
                            .add(
                                egui::Button::new("Redo")
                                    .corner_radius(egui::CornerRadius::same(7)),
                            )
                            .clicked()
                        {
                            self.transcript.redo();
                        }
                        if ui
                            .add(
                                egui::Button::new("Undo")
                                    .corner_radius(egui::CornerRadius::same(7)),
                            )
                            .clicked()
                        {
                            self.transcript.undo();
                        }
                        if ui
                            .add(
                                egui::Button::new("Clear")
                                    .corner_radius(egui::CornerRadius::same(7)),
                            )
                            .clicked()
                        {
                            self.clear_transcript();
                        }
                    });
                });
                ui.add_space(4.0);
                let mut edited = self.transcript.text().to_owned();
                let response = ui.add_sized(
                    [ui.available_width(), 220.0],
                    TextEdit::multiline(&mut edited)
                        .hint_text("Speak to create a draft, then edit it here…")
                        .desired_rows(8),
                );
                if response.changed() {
                    self.transcript.set_text(edited);
                }
                ui.add_space(8.0);
                ui.horizontal_wrapped(|ui| {
                    if Self::primary_button(ui, "Copy draft").clicked() {
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
        egui::CollapsingHeader::new(
            RichText::new(format!("{} captured segment(s)", segments.len()))
                .size(13.0)
                .color(MUTED)
                .strong(),
        )
        .default_open(false)
        .show(ui, |ui| {
            for segment in segments {
                egui::Frame::new()
                    .fill(Color32::from_rgba_unmultiplied(35, 48, 45, 155))
                    .corner_radius(egui::CornerRadius::same(8))
                    .inner_margin(egui::Margin::same(9))
                    .show(ui, |ui| {
                        ui.horizontal(|ui| {
                            Self::badge(ui, format!("#{:02}", segment.sequence), ACCENT);
                            Self::badge(
                                ui,
                                segment.status.label().to_ascii_uppercase(),
                                match segment.status {
                                    SegmentStatus::Complete => ACCENT,
                                    SegmentStatus::Error => DANGER,
                                    SegmentStatus::Pending | SegmentStatus::Transcribing => WARNING,
                                    SegmentStatus::Cancelled => MUTED,
                                },
                            );
                            if !segment.text.is_empty() {
                                ui.label(RichText::new(segment.text.clone()).color(TEXT));
                            } else if let Some(detail) = &segment.detail {
                                ui.label(RichText::new(detail).size(12.0).color(MUTED));
                            }
                        });
                    });
            }
        });
    }

    fn render_settings(&mut self, ui: &mut egui::Ui) {
        ui.add_space(12.0);
        let response = egui::CollapsingHeader::new(
            RichText::new("Settings & privacy")
                .size(14.0)
                .color(TEXT)
                .strong(),
        )
        .default_open(self.show_settings)
        .show(ui, |ui| {
            egui::Frame::group(ui.style())
                .fill(SURFACE_MUTED)
                .stroke(Stroke::new(1.0, Color32::from_rgb(56, 78, 71)))
                .corner_radius(egui::CornerRadius::same(10))
                .inner_margin(egui::Margin::same(16))
                .show(ui, |ui| {
                    ui.label(
                        RichText::new("PROVIDER BOUNDARY")
                            .size(11.0)
                            .color(ACCENT)
                            .strong(),
                    );
                    ui.label(
                        RichText::new("Groq cloud · HTTPS")
                            .size(17.0)
                            .color(TEXT)
                            .strong(),
                    );
                    ui.label(
                        RichText::new(
                            "Audio stays on this computer while you speak. Only a completed segment is sent, and only after you confirm below.",
                        )
                        .size(13.0)
                        .color(MUTED),
                    );
                    ui.add_space(6.0);
                    ui.checkbox(
                        &mut self.config.cloud_boundary_confirmed,
                        "I understand that completed speech is sent to Groq over HTTPS",
                    );
                    ui.add_space(5.0);
                    ui.label(RichText::new("Groq API key").size(12.0).color(MUTED).strong());
                    ui.add(
                        TextEdit::singleline(&mut self.api_key_draft)
                            .password(true)
                            .desired_width(ui.available_width())
                            .hint_text("Paste a key, or use GROQ_API_KEY"),
                    );
                    if std::env::var("GROQ_API_KEY")
                        .map(|value| !value.trim().is_empty())
                        .unwrap_or(false)
                    {
                        ui.label(
                            RichText::new("● environment key detected")
                                .size(12.0)
                                .color(ACCENT),
                        );
                    }
                    ui.separator();
                    ui.label(RichText::new("TRANSCRIPTION").size(11.0).color(ACCENT).strong());
                    ui.horizontal(|ui| {
                        ui.label(RichText::new("Language").size(12.0).color(MUTED).strong());
                        egui::ComboBox::from_id_salt("language")
                            .selected_text(self.config.language.clone())
                            .show_ui(ui, |ui| {
                                for language in ["auto", "en", "fr", "es", "de", "it", "pt", "ar", "zh"] {
                                    ui.selectable_value(&mut self.config.language, language.into(), language);
                                }
                        });
                        ui.checkbox(&mut self.config.translate_to_english, "Translate to English");
                    });
                    ui.checkbox(
                        &mut self.config.copy_on_final,
                        "Copy completed segments automatically",
                    );
                    ui.checkbox(
                        &mut self.config.history_enabled,
                        "Keep a bounded text-only local history",
                    );
                    ui.separator();
                    ui.label(RichText::new("MICROPHONE").size(11.0).color(ACCENT).strong());
                    ui.horizontal(|ui| {
                        ui.label(RichText::new("Input").size(12.0).color(MUTED).strong());
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
                    ui.label(
                        RichText::new(
                            "The selected device is remembered with an opaque identity so a replug cannot silently switch microphones.",
                        )
                        .size(12.0)
                        .color(MUTED),
                    );
                    ui.horizontal(|ui| {
                        if Self::primary_button(ui, "Save settings").clicked() {
                            self.save_settings();
                        }
                        if ui.button("Reset transcript").clicked() {
                            self.clear_transcript();
                        }
                        if let Some(saved) = self.last_saved {
                            ui.label(
                                RichText::new(format!("saved {}s ago", saved.elapsed().as_secs()))
                                    .size(12.0)
                                    .color(MUTED),
                            );
                        }
                    });
                });
        });
        self.show_settings = response.fully_open();
    }
}

impl App for VoiceTranscriberApp {
    fn ui(&mut self, ui: &mut egui::Ui, _frame: &mut Frame) {
        self.poll_audio();
        self.poll_provider();
        ui.ctx().request_repaint_after(Duration::from_millis(50));
        Self::draw_backdrop(ui);
        egui::CentralPanel::default()
            .frame(
                egui::Frame::central_panel(ui.style())
                    .fill(BACKGROUND)
                    .inner_margin(egui::Margin::same(22)),
            )
            .show(ui, |ui| {
                egui::ScrollArea::vertical()
                    .auto_shrink([false, false])
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
                            egui::Frame::new()
                                .fill(Color32::from_rgba_unmultiplied(128, 49, 48, 54))
                                .stroke(Stroke::new(
                                    1.0,
                                    Color32::from_rgba_unmultiplied(255, 125, 116, 130),
                                ))
                                .corner_radius(egui::CornerRadius::same(8))
                                .inner_margin(egui::Margin::same(10))
                                .show(ui, |ui| {
                                    ui.label(RichText::new(format!("!  {error}")).color(DANGER));
                                });
                        }
                    });
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

fn event_is_current_generation(event: &ProviderEvent, current_generation: u64) -> bool {
    event.session_generation == current_generation
}

fn copy_text(text: &str) -> Result<(), String> {
    let mut clipboard =
        Clipboard::new().map_err(|error| format!("Clipboard unavailable: {error}"))?;
    clipboard
        .set_text(text.to_owned())
        .map_err(|error| format!("Could not copy transcript: {error}"))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn stale_provider_events_are_rejected_after_session_reset() {
        let event = ProviderEvent {
            request_id: 7,
            session_generation: 3,
            sequence: 7,
            state: RequestState::Complete,
            text: Some("old result".into()),
            detail: "Added to transcript".into(),
        };
        assert!(!event_is_current_generation(&event, 4));
        assert!(event_is_current_generation(&event, 3));
    }
}
