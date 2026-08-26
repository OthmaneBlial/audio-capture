#!/usr/bin/env bash
# Add a desktop-menu launcher for a completed local installation.

set -euo pipefail

project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python_path="$project_dir/venv/bin/python"
icon_path="$project_dir/resources/icon.svg"
desktop_dir="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
desktop_file="$desktop_dir/voice-transcriber.desktop"

if [[ ! -x "$python_path" ]]; then
  echo "Virtual environment not found. Run ./setup.sh first." >&2
  exit 1
fi
if [[ ! -f "$icon_path" ]]; then
  echo "Application icon is missing at $icon_path." >&2
  exit 1
fi

mkdir -p "$desktop_dir"
cat > "$desktop_file" <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Voice Transcriber
Comment=Live microphone transcription with Groq Whisper
Exec="$python_path" "$project_dir/main.py"
Icon=$icon_path
Terminal=false
Categories=Utility;AudioVideo;Audio;
Keywords=voice;transcription;speech-to-text;whisper;groq;
StartupWMClass=voice-transcriber
EOF
chmod 644 "$desktop_file"

echo "Installed launcher: $desktop_file"
