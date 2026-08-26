#!/usr/bin/env bash
# Install Voice Transcriber on a Debian/Ubuntu desktop.

set -euo pipefail

if [[ ! -f "requirements.txt" || ! -f ".env.example" ]]; then
  echo "Run this script from the Voice Transcriber repository root." >&2
  exit 1
fi

if ! command -v apt >/dev/null 2>&1; then
  echo "This setup helper supports Debian/Ubuntu (apt) only. See README.md for manual prerequisites." >&2
  exit 1
fi

echo "Installing system dependencies…"
sudo apt update
sudo apt install -y \
  python3 python3-pip python3-venv python3-gi python3-gi-cairo gir1.2-gtk-3.0 \
  portaudio19-dev python3-pyaudio libcairo2-dev libgirepository1.0-dev pkg-config

if [[ ! -d "venv" ]]; then
  echo "Creating virtual environment…"
  python3 -m venv venv --system-site-packages
fi

# shellcheck disable=SC1091
source venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

if [[ ! -f ".env" ]]; then
  cp .env.example .env
  echo "Created .env from .env.example. Add your GROQ_API_KEY before starting."
fi

echo
echo "Setup complete. Next steps:"
echo "  1. Edit .env and set GROQ_API_KEY"
echo "  2. source venv/bin/activate"
echo "  3. python main.py --check-config"
echo "  4. python main.py"
