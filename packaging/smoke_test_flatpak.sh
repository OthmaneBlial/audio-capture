#!/usr/bin/env bash
set -euo pipefail

app_id="io.github.othmaneblial.audio_capture"
bundle_path="${1:-voice-transcriber.flatpak}"
expected_version="${2:-}"
installed=0

run_flatpak_with_session_bus() {
  # Flatpak's user installation service needs a session bus during cleanup.
  # The CI container has no desktop session, so autolaunch otherwise fails
  # after the Xvfb launch smoke has already finished.
  if [[ -n "${DBUS_SESSION_BUS_ADDRESS:-}" ]]; then
    flatpak "$@"
  elif command -v dbus-run-session >/dev/null 2>&1; then
    dbus-run-session -- flatpak "$@"
  elif command -v xvfb-run >/dev/null 2>&1; then
    xvfb-run -a flatpak "$@"
  else
    flatpak "$@"
  fi
}

if [[ ! -f "$bundle_path" ]]; then
  echo "Flatpak bundle not found: $bundle_path" >&2
  exit 1
fi
if [[ -z "$expected_version" || ! "$expected_version" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  echo "Usage: $0 BUNDLE_PATH VERSION (for example: $0 voice-transcriber.flatpak 1.0.0)" >&2
  exit 2
fi
if [[ ! -s /etc/machine-id && ! -s /var/lib/dbus/machine-id ]]; then
  echo "A D-Bus machine-id is required for the Flatpak install/uninstall smoke" >&2
  exit 1
fi

cleanup() {
  if [[ "$installed" -ne 1 ]]; then
    return 0
  fi
  # The launch smoke is intentionally killed by timeout; explicitly terminate
  # any remaining sandbox process before asking Flatpak to remove its data.
  run_flatpak_with_session_bus kill --user "$app_id" >/dev/null 2>&1 || true
  if ! run_flatpak_with_session_bus uninstall --user --noninteractive --delete-data "$app_id"; then
    echo "Flatpak uninstall with --delete-data failed" >&2
    run_flatpak_with_session_bus info --user "$app_id" >&2 || true
    flatpak ps >&2 || true
    return 1
  fi
}
trap cleanup EXIT

flatpak install --user --noninteractive --or-update "$bundle_path"
installed=1
flatpak run --user --command=voice-transcriber "$app_id" --version | grep -Fx "voice-transcriber $expected_version"
flatpak run --user --command=voice-transcriber "$app_id" --help | grep -F -- "--doctor"

doctor_report="$(mktemp)"
set +e
flatpak run --user --command=voice-transcriber "$app_id" --doctor --json >"$doctor_report"
doctor_exit=$?
set -e
if [[ "$doctor_exit" -ne 1 ]]; then
  echo "Expected headless doctor to return 1, got $doctor_exit" >&2
  exit 1
fi
python3 - "$doctor_report" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as report_file:
    report = json.load(report_file)
assert report["schema_version"] == 1
assert report["ready"] is False
assert report["checks"]["provider"]["contacted"] is False
serialized = json.dumps(report)
assert "gsk_" not in serialized and "Bearer " not in serialized
print("Flatpak doctor contract: passed")
PY

permissions="$(flatpak info --user --show-permissions "$app_id")"
grep -Eq 'shared=.*network' <<<"$permissions"
grep -Eq 'shared=.*ipc' <<<"$permissions"
grep -Eq 'sockets=.*wayland' <<<"$permissions"
grep -Eq 'sockets=.*(fallback-x11|x11)' <<<"$permissions"
grep -Eq 'sockets=.*pulseaudio' <<<"$permissions"
if grep -Eq 'filesystems=.*(host|home)' <<<"$permissions"; then
  echo "Unexpected broad filesystem permission" >&2
  exit 1
fi

flatpak run --user --command=sh "$app_id" -c '
  test -x /app/bin/voice-transcriber
  test -f /app/share/applications/io.github.othmaneblial.audio_capture.desktop
  test -f /app/share/metainfo/io.github.othmaneblial.audio_capture.metainfo.xml
  test -f /app/share/icons/hicolor/scalable/apps/io.github.othmaneblial.audio_capture.svg
'

if ! command -v xvfb-run >/dev/null 2>&1; then
  echo "xvfb-run is required for the GTK launch smoke test" >&2
  exit 1
else
  # GitHub's container has no Flatpak portal for Glycin's second-level image
  # sandbox. Disable only that nested loader sandbox for these Xvfb launches;
  # the application itself still runs in its installed Flatpak sandbox.
  xvfb-run -a flatpak run --user \
    --env=GLYCIN_DISABLE_SANDBOX=i-know-the-risks --command=python3 "$app_id" \
    /app/share/voice-transcriber/tests/gtk_accessibility_smoke.py
  set +e
  timeout 5s xvfb-run -a flatpak run --user \
    --env=GLYCIN_DISABLE_SANDBOX=i-know-the-risks "$app_id" \
    >/tmp/voice-transcriber-flatpak-ui.log 2>&1
  ui_exit=$?
  set -e
  if [[ "$ui_exit" -ne 124 ]]; then
    echo "Expected the GTK window to remain open until timeout; exit was $ui_exit" >&2
    cat /tmp/voice-transcriber-flatpak-ui.log >&2
    exit 1
  fi
  echo "Flatpak GTK launch smoke test passed under Xvfb."
fi

echo "Flatpak install, CLI, diagnostics, permissions, metadata, and removal smoke test passed."
