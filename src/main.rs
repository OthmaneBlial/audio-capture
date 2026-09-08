use clap::Parser;
use eframe::egui;
use std::time::{Duration, Instant};

#[derive(Debug, Parser)]
#[command(
    name = "voice-transcriber",
    version,
    about = "Review-first cross-platform desktop dictation"
)]
struct Cli {
    /// Print the current input devices and exit.
    #[arg(long)]
    list_devices: bool,
    /// Print a non-network diagnostic report and exit.
    #[arg(long)]
    doctor: bool,
    /// Validate the local configuration and exit.
    #[arg(long)]
    check_config: bool,
    /// Open the selected/default microphone for a short real capture test.
    #[arg(long)]
    test_microphone: bool,
    /// Emit machine-readable JSON for a diagnostic command.
    #[arg(long)]
    json: bool,
}

fn main() -> eframe::Result {
    let cli = Cli::parse();
    if cli.list_devices || cli.doctor || cli.check_config || cli.test_microphone {
        let success = run_diagnostic(&cli);
        if !success {
            std::process::exit(1);
        }
        return Ok(());
    }

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

fn run_diagnostic(cli: &Cli) -> bool {
    if cli.test_microphone {
        return test_microphone(cli.json);
    }
    if cli.list_devices {
        return print_devices(cli.json);
    }

    let store = match voice_transcriber::config::ConfigStore::new() {
        Ok(store) => store,
        Err(error) => {
            if cli.json {
                println!(
                    "{{\"ok\":false,\"error\":{}}}",
                    json_string(&error.to_string())
                );
            } else {
                eprintln!("Configuration directory unavailable: {error}");
            }
            return false;
        }
    };
    let loaded = store.load();
    let config_ok = loaded.is_ok();
    let (provider_configured, config_error) = match loaded {
        Ok(config) => {
            let environment = std::env::vars().collect();
            (
                config.has_api_key(&environment) && config.cloud_boundary_confirmed,
                None,
            )
        }
        Err(error) => (false, Some(error.to_string())),
    };
    if cli.check_config {
        if cli.json {
            println!(
                "{{\"ok\":{},\"provider_configured\":{},\"path\":{}}}",
                config_ok,
                provider_configured,
                json_string(&store.path().display().to_string())
            );
        } else if config_ok {
            println!(
                "Configuration is valid: {} (provider ready: {})",
                store.path().display(),
                if provider_configured {
                    "yes"
                } else {
                    "no — key or consent missing"
                }
            );
        } else {
            eprintln!(
                "Configuration is invalid: {}",
                config_error.as_deref().unwrap_or("unknown error")
            );
        }
        return config_ok;
    }

    let devices = voice_transcriber::audio::list_input_devices();
    let devices_ok = devices.is_ok();
    if cli.json {
        let device_count = devices.as_ref().map(Vec::len).unwrap_or(0);
        println!(
            "{{\"ok\":{},\"config_ok\":{},\"provider_configured\":{},\"input_devices\":{},\"version\":{}}}",
            config_ok && devices_ok,
            config_ok,
            provider_configured,
            device_count,
            json_string(voice_transcriber::VERSION)
        );
    } else {
        println!("Voice Transcriber {}", voice_transcriber::VERSION);
        println!("Config: {}", if config_ok { "valid" } else { "invalid" });
        println!(
            "Provider: {}",
            if provider_configured {
                "ready (consent + key)"
            } else {
                "not ready (consent or key missing)"
            }
        );
        match devices {
            Ok(devices) => println!("Input devices: {}", devices.len()),
            Err(error) => println!("Input devices: unavailable ({error})"),
        }
    }
    config_ok && devices_ok
}

fn test_microphone(json: bool) -> bool {
    let mut capture = match voice_transcriber::audio::AudioCapture::open(None, None) {
        Ok(capture) => capture,
        Err(error) => {
            if json {
                println!(
                    "{{\"ok\":false,\"error\":{}}}",
                    json_string(&error.to_string())
                );
            } else {
                eprintln!("Could not open the microphone: {error}");
            }
            return false;
        }
    };
    let started = Instant::now();
    let mut frames = 0_usize;
    let mut peak_level = 0.0_f32;
    let mut stream_error = None;
    while started.elapsed() < Duration::from_secs(3) {
        if capture.recv_frame(Duration::from_millis(100)).is_some() {
            frames += 1;
        }
        if let Some(level) = capture.try_recv_level() {
            peak_level = peak_level.max(level);
        }
        if let Some(error) = capture.try_recv_error() {
            stream_error = Some(error);
            break;
        }
    }
    let device = capture.device().clone();
    capture.stop();
    let ok = stream_error.is_none();
    if json {
        println!(
            "{{\"ok\":{},\"device\":{},\"frames\":{},\"peak_level\":{:.4},\"stream_error\":{}}}",
            ok,
            json_string(&device.name),
            frames,
            peak_level,
            stream_error
                .as_deref()
                .map(json_string)
                .unwrap_or_else(|| "null".into())
        );
    } else {
        println!(
            "Microphone test: {} — {} ({frames} frame(s), peak level {:.2})",
            if ok { "ok" } else { "failed" },
            device.name,
            peak_level
        );
        if let Some(error) = stream_error {
            eprintln!("Stream error: {error}");
        }
    }
    ok
}

fn print_devices(json: bool) -> bool {
    match voice_transcriber::audio::list_input_devices() {
        Ok(devices) => {
            if json {
                let encoded = devices
                    .iter()
                    .map(|device| {
                        format!(
                            "{{\"index\":{},\"name\":{},\"identity\":{},\"default\":{},\"channels\":{},\"sample_rate\":{},\"sample_format\":{}}}",
                            device.index,
                            json_string(&device.name),
                            json_string(&device.identity),
                            device.is_default,
                            device.channels,
                            device.sample_rate,
                            json_string(&device.sample_format)
                        )
                    })
                    .collect::<Vec<_>>()
                    .join(",");
                println!("[{encoded}]");
            } else {
                for device in devices {
                    println!(
                        "[{}] {}{} — {} Hz, {} channel(s), {}",
                        device.index,
                        device.name,
                        if device.is_default { " (default)" } else { "" },
                        device.sample_rate,
                        device.channels,
                        device.sample_format
                    );
                }
            }
            true
        }
        Err(error) => {
            if json {
                println!(
                    "{{\"ok\":false,\"error\":{}}}",
                    json_string(&error.to_string())
                );
            } else {
                eprintln!("Could not list input devices: {error}");
            }
            false
        }
    }
}

fn json_string(value: &str) -> String {
    serde_json::to_string(value).unwrap_or_else(|_| "\"unavailable\"".into())
}
