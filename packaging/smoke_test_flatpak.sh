#!/usr/bin/env bash
set -euo pipefail

app_id="io.github.othmaneblial.audio_capture"
bundle_path="${1:-voice-transcriber.flatpak}"

if [[ ! -f "$bundle_path" ]]; then
  echo "Flatpak bundle not found: $bundle_path" >&2
  exit 1
fi

cleanup() {
  flatpak uninstall --user --noninteractive --delete-data "$app_id" >/dev/null 2>&1 || true
}
trap cleanup EXIT

flatpak install --user --noninteractive --or-update "$bundle_path"
flatpak run --user --command=voice-transcriber "$app_id" --version | grep -Fx "voice-transcriber 0.2.0"
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
grep -F "shared=network;ipc;" <<<"$permissions"
grep -Eq 'sockets=.*wayland' <<<"$permissions"
grep -Eq 'sockets=.*(fallback-x11|x11)' <<<"$permissions"
grep -Eq 'sockets=.*pulseaudio' <<<"$permissions"
if grep -Eq 'filesystems=(host|home)' <<<"$permissions"; then
  echo "Unexpected broad filesystem permission" >&2
  exit 1
fi

flatpak run --user --command=sh "$app_id" -c '
  test -x /app/bin/voice-transcriber
  test -f /app/share/applications/io.github.othmaneblial.audio_capture.desktop
  test -f /app/share/metainfo/io.github.othmaneblial.audio_capture.metainfo.xml
  test -f /app/share/icons/hicolor/scalable/apps/io.github.othmaneblial.audio_capture.svg
'

if command -v xvfb-run >/dev/null 2>&1; then
  set +e
  timeout 5s xvfb-run -a flatpak run --user "$app_id" >/tmp/voice-transcriber-flatpak-ui.log 2>&1
  ui_exit=$?
  set -e
  if [[ "$ui_exit" -ne 124 ]]; then
    echo "Expected the GTK window to remain open until timeout; exit was $ui_exit" >&2
    cat /tmp/voice-transcriber-flatpak-ui.log >&2
    exit 1
  fi
  echo "Flatpak GTK launch smoke test passed under Xvfb."
else
  echo "xvfb-run is unavailable; GTK launch smoke test was skipped." >&2
fi

echo "Flatpak install, CLI, diagnostics, permissions, metadata, and removal smoke test passed."
