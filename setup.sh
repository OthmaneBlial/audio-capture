#!/bin/bash
# Ubuntu setup script for Real-Time Voice Transcriber
# Tested on Ubuntu 20.04, 22.04, and 24.04

set -e

echo "🎤 Real-Time Voice Transcriber Setup"
echo "======================================"

# Check if running on Ubuntu/Debian
if ! command -v apt &> /dev/null; then
    echo "❌ This script requires apt (Ubuntu/Debian). Please install dependencies manually."
    exit 1
fi

# Install system dependencies
echo ""
echo "📦 Installing system dependencies..."
sudo apt update
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-gi \
    python3-gi-cairo \
    gir1.2-gtk-3.0 \
    portaudio19-dev \
    python3-pyaudio \
    libcairo2-dev \
    libgirepository1.0-dev \
    pkg-config

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo ""
    echo "🐍 Creating Python virtual environment..."
    python3 -m venv venv --system-site-packages
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install Python dependencies
echo ""
echo "📥 Installing Python dependencies..."
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo ""
    echo "📝 Creating .env template..."
    cat > .env << 'EOF'
# Groq API Key
# Get yours at: https://console.groq.com
GROQ_API_KEY=your_api_key_here
EOF
    echo "⚠️  Please edit .env and add your Groq API key!"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Edit .env and add your Groq API key"
echo "  2. Activate the virtual environment: source venv/bin/activate"
echo "  3. Run the application: python main.py"
echo ""
