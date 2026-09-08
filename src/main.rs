use eframe::egui;

fn main() -> eframe::Result {
    let native_options = eframe::NativeOptions {
        viewport: egui::ViewportBuilder::default()
            .with_app_id(voice_transcriber::APP_ID)
            .with_title(voice_transcriber::APP_NAME)
            .with_inner_size([
                voice_transcriber::config::AppConfig::default().window_width as f32,
                voice_transcriber::config::AppConfig::default().window_height as f32,
            ])
            .with_min_inner_size([480.0, 360.0]),
        ..Default::default()
    };
    eframe::run_native(
        voice_transcriber::APP_NAME,
        native_options,
        Box::new(|cc| {
            voice_transcriber::app::VoiceTranscriberApp::new(cc)
                .map(|app| Box::new(app) as Box<dyn eframe::App>)
                .map_err(|error| error.into())
        }),
    )
}
