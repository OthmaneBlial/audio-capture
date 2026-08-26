#!/usr/bin/env python3
"""Desktop entry point for Voice Transcriber."""

from __future__ import annotations

import argparse
import json
import logging
import signal
import sys
import threading
from typing import Any, Optional

try:
    from dotenv import load_dotenv
except ImportError:
    # Diagnostics remain usable before optional/runtime Python packages are installed.
    def load_dotenv() -> bool:
        return False

from config import ConfigManager

__version__ = "0.6.0"
LOGGER = logging.getLogger(__name__)
Gtk: Any = None
GLib: Any = None
_ALSA_ERROR_CALLBACK: Any = None


class VoiceTranscriberApp:
    """Coordinate microphone capture, VAD, API work, and the GTK window."""

    def __init__(self, *, input_device_override: Optional[int] = None) -> None:
        from ui import MainWindow

        self._running = threading.Event()
        self._lifecycle_lock = threading.RLock()
        self._processing_thread: Optional[threading.Thread] = None
        self._audio: Any = None
        self._vad: Any = None
        self._input_device_override = input_device_override
        self._config = ConfigManager()
        self._transcriber = self._build_transcriber()
        self._window = MainWindow(
            config=self._config,
            on_start=self._start_listening,
            on_stop=self._stop_listening,
            on_settings_change=self._on_settings_change,
            on_list_input_devices=self._list_input_devices,
        )

    def _build_transcriber(self) -> Any:
        common = {
            "sample_rate": 16000,
            "language": self._config.get("language"),
            "on_transcription": self._on_transcription,
            "on_error": self._on_transcription_error,
            "on_request_state": self._on_request_state,
        }
        if self._config.get("provider_mode") == "local_whisper_cpp":
            from transcription.local_whisper import LocalWhisperTranscriptionService

            return LocalWhisperTranscriptionService(
                binary_path=self._config.get("local_binary_path"),
                model_path=self._config.get("local_model_path"),
                translate=self._config.get("translate_to_english"),
                **common,
            )
        from transcription import GroqTranscriptionService

        service = GroqTranscriptionService(api_key=self._config.get("api_key"), **common)
        service.update_config(translate=self._config.get("translate_to_english"))
        return service

    def _on_settings_change(self) -> None:
        """Apply preferences without exposing the API key in logs."""
        desired_provider = self._config.get("provider_mode")
        if self._transcriber.provider_id != desired_provider or desired_provider == "local_whisper_cpp":
            if self._running.is_set():
                self._stop_listening()
            previous = self._transcriber
            self._transcriber = self._build_transcriber()
            previous.close(wait=False)
        else:
            self._transcriber.update_config(
                api_key=self._config.get("api_key"),
                language=self._config.get("language"),
                translate=self._config.get("translate_to_english"),
            )
        self._window.refresh_provider_boundary()
        LOGGER.info("Transcription preferences updated")

    @staticmethod
    def _list_input_devices() -> list[Any]:
        """Load microphones on demand so opening the window never requires PyAudio first."""
        from audio import list_input_devices

        return list_input_devices()

    def _on_input_level(self, level: float) -> None:
        """Forward bounded capture telemetry to GTK without recording audio data."""
        self._window.set_input_level(level)

    def _start_listening(self) -> bool:
        """Start microphone capture. Returns false when UI should remain stopped."""
        from audio import AudioCapture, VoiceActivityDetector

        with self._lifecycle_lock:
            if self._running.is_set():
                return True
            if not self._transcriber.configured:
                if self._transcriber.provider_id == "groq":
                    message = "No Groq API key is configured. Open Settings or set GROQ_API_KEY, then try again."
                else:
                    message = (
                        "Experimental local mode is not ready. Enable its source-install flag and choose a compatible whisper-cli and GGML model."
                    )
                self._window.show_error(message)
                return False

            audio: Any = None
            try:
                device_index = (
                    self._input_device_override
                    if self._input_device_override is not None
                    else self._config.get("input_device_index")
                )
                audio = AudioCapture(device_index=device_index, on_level=self._on_input_level)
                vad = VoiceActivityDetector(
                    sample_rate=audio.sample_rate,
                    frame_duration_ms=audio.frame_duration_ms,
                    aggressiveness=2,
                    silence_threshold_ms=600,
                    min_speech_ms=300,
                    max_speech_ms=20_000,
                )
                audio.start()
                selected_device = audio.selected_device
                if selected_device is not None:
                    self._window.set_input_source(selected_device.name)
                self._audio = audio
                self._vad = vad
                self._running.set()
                self._processing_thread = threading.Thread(
                    target=self._processing_loop,
                    args=(audio, vad),
                    daemon=True,
                    name="AudioProcessing",
                )
                self._processing_thread.start()
            except Exception as error:
                if audio is not None:
                    audio.stop()
                LOGGER.exception("Could not start microphone capture")
                self._window.show_error(str(error))
                return False

        LOGGER.info("Listening started")
        return True

    def _stop_listening(self) -> None:
        """Stop capture deterministically, then flush an in-progress speech segment."""
        with self._lifecycle_lock:
            if not self._running.is_set() and self._audio is None:
                return
            self._running.clear()
            audio, vad, processing_thread = self._audio, self._vad, self._processing_thread
            self._audio = None
            self._vad = None
            self._processing_thread = None

        if audio is not None:
            audio.stop()
        self._window.set_input_level(0.0)
        if processing_thread and processing_thread.is_alive() and processing_thread is not threading.current_thread():
            processing_thread.join(timeout=1.5)
            if processing_thread.is_alive():
                LOGGER.warning("Audio processing did not finish before shutdown timeout")

        if vad is not None:
            remaining = vad.flush()
            if remaining:
                self._transcriber.transcribe_async(remaining)
        LOGGER.info("Listening stopped")

    def _processing_loop(self, audio: Any, vad: Any) -> None:
        """Run VAD outside GTK's main loop and hand bounded segments to the API pool."""
        while self._running.is_set():
            try:
                chunk = audio.get_audio_chunk(timeout=0.2)
                if chunk is None:
                    if not audio.is_running and self._running.is_set():
                        self._running.clear()
                        GLib.idle_add(
                            lambda: self._handle_capture_failure(
                                "Microphone capture stopped unexpectedly. Check the device and start again."
                            )
                            or False
                        )
                    continue

                speech_segment = vad.process_frame(chunk)
                if vad.is_speaking:
                    duration = vad.current_duration_ms / 1000
                    GLib.idle_add(
                        lambda value=duration: self._window.set_status(
                            f"Listening · speech detected ({value:.1f}s)", "active"
                        )
                        or False
                    )
                if speech_segment:
                    GLib.idle_add(lambda: self._window.set_status("Transcribing securely…", "active") or False)
                    self._transcriber.transcribe_async(speech_segment)
            except Exception:
                LOGGER.exception("Audio processing failed")
                self._running.clear()
                GLib.idle_add(
                    lambda: self._handle_capture_failure(
                        "Audio processing failed. Stop and start listening again."
                    )
                    or False
                )
                break

    def _handle_capture_failure(self, message: str) -> None:
        """Bring controller and visible record state back into sync after capture loss."""
        self._window.show_error(message)
        self._window.stop_listening()

    def _on_transcription(self, text: str) -> None:
        if text.strip():
            self._window.append_text(text)
            if self._config.get("copy_on_final"):
                self._window.copy_transcript_after_final()
        if self._running.is_set():
            self._window.set_status("Listening…", "active")

    def _on_request_state(self, request_id: str, state: str, detail: Optional[str]) -> None:
        self._window.update_segment_state(request_id, state, detail)

    def _on_transcription_error(self, error: Exception) -> None:
        # Service errors are normalized and never contain a credential.
        self._window.show_error(str(error))
        if self._running.is_set():
            GLib.timeout_add(4_000, lambda: self._window.set_status("Listening…", "active") or False)

    def run(self) -> None:
        """Open the desktop window and guarantee resource cleanup on exit."""
        def handle_signal(_signal_number: int, _frame: Any) -> None:
            LOGGER.info("Shutdown signal received")
            self._stop_listening()
            GLib.idle_add(Gtk.main_quit)

        signal.signal(signal.SIGINT, handle_signal)
        signal.signal(signal.SIGTERM, handle_signal)
        self._window.show_all()
        Gtk.main()
        self._stop_listening()
        self._transcriber.close(wait=False)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="voice-transcriber",
        description="Capture short speech segments and transcribe them through an explicit provider boundary.",
    )
    parser.add_argument("--version", action="version", version=f"voice-transcriber {__version__}")
    checks = parser.add_mutually_exclusive_group()
    checks.add_argument("--check-config", action="store_true", help="validate configuration without opening GTK")
    checks.add_argument("--list-devices", action="store_true", help="list available microphone inputs without opening GTK")
    checks.add_argument("--doctor", action="store_true", help="run privacy-safe environment diagnostics without opening GTK")
    parser.add_argument(
        "--device",
        type=_device_index_argument,
        metavar="INDEX",
        help="use a microphone index for this session (overrides the saved choice)",
    )
    parser.add_argument("--json", action="store_true", help="format --list-devices or --doctor output as JSON")
    parser.add_argument(
        "--probe-provider",
        action="store_true",
        help="with --doctor, explicitly contact Groq when it is the active provider",
    )
    parser.add_argument("--verbose", action="store_true", help="show diagnostic logs (never credentials)")
    return parser


def _configure_logging(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def _device_index_argument(value: str) -> int:
    try:
        index = int(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("microphone index must be a non-negative integer") from error
    if index < 0:
        raise argparse.ArgumentTypeError("microphone index must be a non-negative integer")
    return index


def _run_config_check() -> int:
    config = ConfigManager()
    if config.get("provider_mode") == "local_whisper_cpp":
        from transcription.local_whisper import LocalWhisperTranscriptionService

        service = LocalWhisperTranscriptionService(
            binary_path=config.get("local_binary_path"),
            model_path=config.get("local_model_path"),
        )
        try:
            if not service.configured:
                print(
                    "Configuration incomplete: enable experimental local mode and select an executable whisper-cli plus GGML model.",
                    file=sys.stderr,
                )
                return 2
        finally:
            service.close(wait=False)
        print("Configuration looks valid. Active provider: experimental local whisper.cpp.")
        return 0
    if not config.has_api_key():
        print("Configuration incomplete: set GROQ_API_KEY or add a key in the app Settings.", file=sys.stderr)
        return 2
    print(f"Configuration looks valid. API key source: {config.source_for('api_key')}.")
    return 0


def _run_device_list(*, as_json: bool) -> int:
    """Print locally discovered microphones without starting GTK or contacting Groq."""
    try:
        from audio import list_input_devices

        devices = list_input_devices()
    except ImportError:
        print(
            "Could not list microphone inputs because PyAudio is unavailable. "
            "Install the Linux prerequisites from the README, then try again.",
            file=sys.stderr,
        )
        return 1
    except RuntimeError as error:
        print(str(error), file=sys.stderr)
        return 1

    if as_json:
        print(
            json.dumps(
                [
                    {
                        "index": device.index,
                        "name": device.name,
                        "max_input_channels": device.max_input_channels,
                        "is_default": device.is_default,
                    }
                    for device in devices
                ],
                indent=2,
            )
        )
        return 0
    if not devices:
        print("No microphone inputs were found. Connect or enable a microphone, then try again.")
        return 0

    print("Microphone inputs:")
    for device in devices:
        default = " (default)" if device.is_default else ""
        channels = "channel" if device.max_input_channels == 1 else "channels"
        print(f"  {device.index}: {device.name} — {device.max_input_channels} {channels}{default}")
    return 0


def _run_doctor(*, as_json: bool, probe_provider: bool) -> int:
    """Run diagnostics without opening GTK, transmitting audio, or exposing secrets."""
    from diagnostics import collect_diagnostics, diagnostics_json, format_diagnostics

    report = collect_diagnostics(
        ConfigManager(),
        app_version=__version__,
        probe_provider=probe_provider,
    )
    print(diagnostics_json(report) if as_json else format_diagnostics(report))
    return 0 if report["ready"] else 1


def _configure_alsa_errors() -> None:
    """Mute noisy ALSA diagnostics when the optional native library is present."""
    global _ALSA_ERROR_CALLBACK
    try:
        from ctypes import CDLL, CFUNCTYPE, c_char_p, c_int

        callback_type = CFUNCTYPE(None, c_char_p, c_int, c_char_p, c_int, c_char_p)
        callback = callback_type(lambda *_args: None)
        asound = CDLL("libasound.so.2")
        asound.snd_lib_error_set_handler(callback)
        # ctypes callbacks must stay alive for as long as the native library can call them.
        _ALSA_ERROR_CALLBACK = callback
    except (OSError, ImportError):
        LOGGER.debug("Could not install ALSA error handler", exc_info=True)


def main(argv: Optional[list[str]] = None) -> int:
    """Run the command-line entry point."""
    parser = _parser()
    args = parser.parse_args(argv)
    if args.probe_provider and not args.doctor:
        parser.error("--probe-provider requires --doctor")
    if args.json and not (args.list_devices or args.doctor):
        parser.error("--json requires --list-devices or --doctor")
    _configure_logging(args.verbose)
    load_dotenv()
    if args.list_devices or args.doctor:
        _configure_alsa_errors()
    if args.check_config:
        return _run_config_check()
    if args.list_devices:
        return _run_device_list(as_json=args.json)
    if args.doctor:
        return _run_doctor(as_json=args.json, probe_provider=args.probe_provider)

    global Gtk, GLib
    try:
        import gi

        gi.require_version("Gtk", "3.0")
        from gi.repository import GLib as gi_glib
        from gi.repository import Gtk as gi_gtk
    except (ImportError, ValueError):
        LOGGER.error(
            "GTK 3 is unavailable. Install the Linux system prerequisites in the README before launching the desktop app."
        )
        LOGGER.debug("GTK import failure", exc_info=True)
        return 1
    Gtk, GLib = gi_gtk, gi_glib
    _configure_alsa_errors()
    GLib.set_prgname("voice-transcriber")
    GLib.set_application_name("Voice Transcriber")
    VoiceTranscriberApp(input_device_override=args.device).run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
