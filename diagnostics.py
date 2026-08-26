"""Privacy-safe, non-destructive environment diagnostics."""

from __future__ import annotations

import json
import os
import platform
import urllib.error
import urllib.request
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any, Optional

from config import ConfigManager
from transcription.local_whisper import local_mode_enabled

SCHEMA_VERSION = 1
SUPPORTED_DISTRIBUTIONS = {"debian", "ubuntu"}
GROQ_MODELS_URL = "https://api.groq.com/openai/v1/models"

Check = dict[str, Any]


def _check(status: str, summary: str, **details: Any) -> Check:
    return {"status": status, "summary": summary, **details}


def _os_release(path: Path = Path("/etc/os-release")) -> dict[str, str]:
    """Read public operating-system identity fields without invoking a shell."""
    values: dict[str, str] = {}
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            values[key] = value.strip().strip('"')
    except OSError:
        return {}
    return values


def _gtk_probe() -> str:
    import gi

    gi.require_version("Gtk", "3.0")
    from gi.repository import Gtk

    return f"{Gtk.get_major_version()}.{Gtk.get_minor_version()}.{Gtk.get_micro_version()}"


def _device_probe() -> list[Any]:
    from audio import list_input_devices

    return list_input_devices()


def _groq_probe(api_key: str, *, timeout_seconds: float = 5.0) -> tuple[str, str]:
    """Probe the configured account only after the CLI user explicitly opts in."""
    request = urllib.request.Request(
        GROQ_MODELS_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
            "User-Agent": "voice-transcriber-doctor/1",
        },
        method="GET",
    )
    try:
        # URL is a module constant with an HTTPS scheme; user input cannot select a scheme/path.
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:  # nosec B310
            status_code = int(getattr(response, "status", 200))
    except urllib.error.HTTPError as error:
        if error.code in {401, 403}:
            return "fail", "Groq is reachable but rejected the configured credential."
        if error.code == 429:
            return "warn", "Groq is reachable but the account is currently rate limited."
        return "fail", f"Groq returned HTTP {error.code}."
    except (urllib.error.URLError, TimeoutError, OSError):
        return "fail", "Groq could not be reached within the diagnostic timeout."
    if 200 <= status_code < 300:
        return "pass", "Groq is reachable and accepted the configured credential."
    return "fail", f"Groq returned HTTP {status_code}."


def collect_diagnostics(
    config: ConfigManager,
    *,
    app_version: str,
    probe_provider: bool = False,
    environ: Optional[Mapping[str, str]] = None,
    system_name: Optional[str] = None,
    release_info: Optional[Mapping[str, str]] = None,
    gtk_probe: Callable[[], str] = _gtk_probe,
    device_probe: Callable[[], list[Any]] = _device_probe,
    provider_probe: Callable[[str], tuple[str, str]] = _groq_probe,
) -> dict[str, Any]:
    """Collect actionable checks without exposing secrets or contacting Groq by default."""
    current_environ = environ if environ is not None else os.environ
    current_system = system_name or platform.system()
    current_release = dict(release_info) if release_info is not None else _os_release()
    distribution_id = current_release.get("ID", "unknown").lower()
    distribution_name = current_release.get("PRETTY_NAME", distribution_id or "unknown")
    checks: dict[str, Check] = {}
    next_actions: list[str] = []

    if current_system == "Linux" and distribution_id in SUPPORTED_DISTRIBUTIONS:
        checks["platform"] = _check(
            "pass",
            f"{distribution_name} is in the declared source-install support boundary.",
            system=current_system,
            distribution=distribution_id,
        )
    elif current_system == "Linux":
        checks["platform"] = _check(
            "warn",
            f"{distribution_name} is Linux but is not yet in the proven support matrix.",
            system=current_system,
            distribution=distribution_id,
        )
        next_actions.append("Compare this distribution with docs/SUPPORT.md before reporting it as supported.")
    else:
        checks["platform"] = _check(
            "fail",
            f"{current_system} is not supported; Voice Transcriber currently targets Linux desktops.",
            system=current_system,
            distribution=distribution_id,
        )
        next_actions.append("Use a supported Debian/Ubuntu Linux desktop.")

    session_type = current_environ.get("XDG_SESSION_TYPE", "").strip().lower()
    if session_type in {"x11", "wayland"}:
        checks["desktop_session"] = _check(
            "pass", f"The declared desktop session is {session_type}.", session_type=session_type
        )
    else:
        inferred_session = "wayland" if current_environ.get("WAYLAND_DISPLAY") else (
            "x11" if current_environ.get("DISPLAY") else "unknown"
        )
        checks["desktop_session"] = _check(
            "warn",
            "The desktop session could not be confirmed from XDG_SESSION_TYPE.",
            session_type=inferred_session,
        )
        next_actions.append("Run the app inside a graphical X11 or Wayland desktop session.")

    try:
        gtk_version = gtk_probe()
        checks["gtk"] = _check("pass", f"GTK 3 is importable ({gtk_version}).", version=gtk_version)
    except Exception as error:
        checks["gtk"] = _check(
            "fail",
            "GTK 3 could not be imported.",
            error_type=type(error).__name__,
        )
        next_actions.append("Install the GTK 3 system prerequisites documented in README.md.")

    devices: list[Any] = []
    try:
        devices = device_probe()
        if devices:
            checks["microphones"] = _check(
                "pass",
                f"Found {len(devices)} microphone input{'s' if len(devices) != 1 else ''}.",
                count=len(devices),
                indexes=[int(device.index) for device in devices],
                default_indexes=[int(device.index) for device in devices if device.is_default],
            )
        else:
            checks["microphones"] = _check("fail", "No microphone inputs were found.", count=0, indexes=[])
            next_actions.append("Connect or enable a microphone, then run --list-devices.")
    except Exception as error:
        checks["microphones"] = _check(
            "fail",
            "Microphone discovery could not run.",
            count=0,
            indexes=[],
            error_type=type(error).__name__,
        )
        next_actions.append("Install PortAudio/PyAudio and verify desktop microphone permission.")

    selected_index = config.get("input_device_index")
    available_indexes = {int(device.index) for device in devices}
    if selected_index is None:
        checks["selected_microphone"] = _check(
            "pass", "The system default microphone will be used.", selected_index=None
        )
    elif selected_index in available_indexes:
        checks["selected_microphone"] = _check(
            "pass", f"Saved microphone index {selected_index} is available.", selected_index=selected_index
        )
    else:
        checks["selected_microphone"] = _check(
            "fail", f"Saved microphone index {selected_index} is unavailable.", selected_index=selected_index
        )
        next_actions.append("Choose an available microphone in Settings or clear the saved selection.")

    provider_mode = config.get("provider_mode")
    has_api_key = config.has_api_key()
    local_binary = Path(config.get("local_binary_path")).expanduser()
    local_model = Path(config.get("local_model_path")).expanduser()
    local_enabled = local_mode_enabled(current_environ)
    local_binary_ready = local_binary.is_file() and os.access(local_binary, os.X_OK)
    local_model_ready = local_model.is_file()
    if provider_mode == "local_whisper_cpp":
        local_ready = local_enabled and local_binary_ready and local_model_ready
        checks["configuration"] = _check(
            "pass" if local_ready else "fail",
            (
                "The experimental local runtime and model are configured."
                if local_ready
                else "The experimental local provider is missing its feature flag, executable, or model."
            ),
            provider=provider_mode,
            experimental_flag_enabled=local_enabled,
            binary_executable=local_binary_ready,
            model_present=local_model_ready,
            api_key_present=has_api_key,
        )
        if not local_ready:
            next_actions.append(
                "For a source install, set VOICE_TRANSCRIBER_EXPERIMENTAL_LOCAL=1 and select an executable whisper-cli plus GGML model."
            )
    elif has_api_key:
        checks["configuration"] = _check(
            "pass",
            "A plausible Groq credential is configured.",
            provider=provider_mode,
            api_key_present=True,
            api_key_source=config.source_for("api_key"),
        )
    else:
        checks["configuration"] = _check(
            "fail",
            "No plausible Groq credential is configured.",
            provider=provider_mode,
            api_key_present=False,
            api_key_source=config.source_for("api_key"),
        )
        next_actions.append("Set GROQ_API_KEY or save a key in Settings before transcribing.")

    if provider_mode == "local_whisper_cpp":
        checks["provider"] = _check(
            "pass" if local_enabled and local_binary_ready and local_model_ready else "fail",
            (
                "Local provider files are ready; no provider network request was made."
                if local_enabled and local_binary_ready and local_model_ready
                else "Local provider readiness failed; no provider network request was made."
            ),
            contacted=False,
            provider=provider_mode,
            probe_note="Diagnostics validate files only and never send microphone audio.",
        )
    elif not probe_provider:
        checks["provider"] = _check(
            "skip",
            "Provider reachability was not tested; add --probe-provider to opt in.",
            contacted=False,
            provider="groq",
        )
    elif not has_api_key:
        checks["provider"] = _check(
            "fail",
            "Provider reachability cannot be tested without a configured credential.",
            contacted=False,
            provider="groq",
        )
    else:
        provider_status, provider_summary = provider_probe(config.get("api_key"))
        checks["provider"] = _check(
            provider_status,
            provider_summary,
            contacted=True,
            provider="groq",
        )
        if provider_status == "fail":
            next_actions.append("Check the network, Groq account, and configured key, then retry explicitly.")

    required_checks = ["platform", "gtk", "microphones", "selected_microphone", "configuration"]
    if probe_provider and provider_mode == "groq":
        required_checks.append("provider")
    ready = all(checks[name]["status"] != "fail" for name in required_checks)
    return {
        "schema_version": SCHEMA_VERSION,
        "app_version": app_version,
        "ready": ready,
        "provider_probe_requested": probe_provider,
        "checks": checks,
        "next_actions": list(dict.fromkeys(next_actions)),
    }


def format_diagnostics(report: Mapping[str, Any]) -> str:
    """Format the stable report for a person while keeping JSON available for tools."""
    lines = [
        f"Voice Transcriber doctor · schema {report['schema_version']} · app {report['app_version']}",
        "",
    ]
    for name, check in report["checks"].items():
        marker = {"pass": "PASS", "warn": "WARN", "fail": "FAIL", "skip": "SKIP"}[check["status"]]
        lines.append(f"[{marker}] {name.replace('_', ' ')}: {check['summary']}")
    actions = report.get("next_actions", [])
    if actions:
        lines.extend(["", "Next actions:"])
        lines.extend(f"- {action}" for action in actions)
    lines.extend(["", f"Ready to transcribe: {'yes' if report['ready'] else 'no'}"])
    return "\n".join(lines)


def diagnostics_json(report: Mapping[str, Any]) -> str:
    return json.dumps(report, indent=2, sort_keys=True)
