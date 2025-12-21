#!/bin/bash

# Voice Transcriber Installer
# Creates a Desktop Entry for launch from application menu

# Get the absolute path of the project directory
PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
ICON_PATH="$PROJECT_DIR/resources/icon.svg"
EXEC_PATH="$PROJECT_DIR/venv/bin/python $PROJECT_DIR/main.py"
DESKTOP_FILE="$HOME/.local/share/applications/voice-transcriber.desktop"

# Ensure venv exists
if [ ! -d "$PROJECT_DIR/venv" ]; then
    echo "❌ Virtual environment not found. Please run ./setup.sh first."
    exit 1
fi

echo "Installing Voice Transcriber..."

# Create the .desktop file
cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Voice Transcriber
Comment=Real-time speech-to-text with Groq Whisper
Exec=$EXEC_PATH
Icon=$ICON_PATH
Terminal=false
Categories=Utility;Audio;
StartupWMClass=voice-transcriber
EOF

# Make executable (optional for .desktop, but good practice)
chmod +x "$DESKTOP_FILE"

echo "✅ Installed successfully!"
echo "   Icon: $ICON_PATH"
echo "   Exec: $EXEC_PATH"
echo ""
echo "🎉 You can now find 'Voice Transcriber' in your applications menu."
