# 🎤 Real-Time Voice Transcriber

A lightweight Linux desktop application that continuously listens to microphone input and transcribes speech to text in real time using Groq's Whisper Large V3 Turbo model.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![GTK3](https://img.shields.io/badge/GTK-3.0-green.svg)
![Ubuntu](https://img.shields.io/badge/Ubuntu-20.04+-orange.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## ✨ Features

- **Real-time transcription** using Groq's ultra-fast Whisper Large V3 Turbo (216x real-time speed)
- **Voice Activity Detection** (VAD) to avoid transcribing silence
- **Always-on-top mode** (sticky window) for overlay use
- **Dark theme** with modern, minimal UI
- **Low latency** and **low CPU usage** optimized audio pipeline
- **Graceful error handling** with visual feedback

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Main Application                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │   Audio      │────│     VAD      │────│ Transcription│      │
│  │   Capture    │    │   (webrtcvad)│    │   (Groq)     │      │
│  │  (PyAudio)   │    │              │    │              │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│         │                                        │               │
│         │            ┌──────────────┐            │               │
│         └────────────│     UI       │────────────┘               │
│                      │   (GTK3)     │                            │
│                      └──────────────┘                            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Audio Pipeline

| Component | Technology | Purpose |
|-----------|------------|---------|
| Capture | PyAudio | Real-time microphone input |
| Format | 16kHz, Mono, 16-bit PCM | Optimal for Whisper |
| VAD | webrtcvad | Detect speech vs silence |
| Transcription | Groq Whisper API | Convert speech to text |
| UI | GTK3 | Display results |

### Threading Model

- **Main Thread**: GTK UI event loop
- **Audio Thread**: Continuous microphone capture
- **Processing Thread**: VAD and API calls

This design ensures the UI remains responsive while audio is being processed.

## 📋 Requirements

- **OS**: Ubuntu 20.04, 22.04, or 24.04 (or other Debian-based distros)
- **Python**: 3.8 or higher
- **Groq API Key**: Get one free at https://console.groq.com

## 🚀 Installation

### Quick Setup (Recommended)

```bash
# Clone or download this project
cd audio-capture

# Run the setup script
chmod +x setup.sh
./setup.sh

# Add your Groq API key
nano .env  # or use your favorite editor

# Run the application
source venv/bin/activate
python main.py
```

### Manual Setup

1. **Install system dependencies:**

```bash
sudo apt update
sudo apt install -y \
    python3 python3-pip python3-venv \
    python3-gi python3-gi-cairo \
    gir1.2-gtk-3.0 \
    portaudio19-dev python3-pyaudio \
    libcairo2-dev libgirepository1.0-dev pkg-config
```

2. **Create and activate virtual environment:**

```bash
python3 -m venv venv --system-site-packages
source venv/bin/activate
```

3. **Install Python dependencies:**

```bash
pip install -r requirements.txt
```

4. **Set up your API key:**

```bash
# Option 1: Create .env file
echo "GROQ_API_KEY=your_api_key_here" > .env

# Option 2: Export environment variable
export GROQ_API_KEY=your_api_key_here
```

5. **Run the application:**

```bash
python main.py
```

## 🎮 Usage

1. **Start the application** with `python main.py`
2. **Click "▶ Start Listening"** to begin capturing audio
3. **Speak into your microphone** - transcription appears in real-time
4. **Toggle "📌 Sticky"** to keep the window on top of others
5. **Click "⏹ Stop Listening"** to pause
6. **Click "🗑 Clear"** to clear the transcript

### Status Indicators

| Status | Meaning |
|--------|---------|
| Ready | App is ready, not listening |
| 🎤 Listening... | Capturing audio, waiting for speech |
| 🗣 Speaking... (Xs) | Speech detected, buffering |
| ⏳ Transcribing... | Sending audio to Groq API |
| ❌ Error message | Something went wrong |

## ⚙️ Configuration

### VAD Settings

Edit `main.py` to adjust voice activity detection:

```python
self._vad = VoiceActivityDetector(
    aggressiveness=2,        # 0-3, higher = more aggressive filtering
    silence_threshold_ms=500, # Silence duration to end segment
    min_speech_ms=250,       # Minimum speech duration
    max_speech_ms=25000,     # Maximum segment length (25s)
)
```

### Language

To transcribe a specific language, add the language parameter:

```python
self._transcriber = GroqTranscriptionService(
    language="en",  # "en", "es", "fr", "de", "ja", etc.
)
```

## 🐛 Troubleshooting

### "No audio input device found"

- Check your microphone is connected
- Run `arecord -l` to list audio devices
- Check PulseAudio/PipeWire settings

### "API connection failed"

- Verify your GROQ_API_KEY is correct
- Check your internet connection
- Ensure you have API credits at https://console.groq.com

### GTK warnings on Wayland

The always-on-top feature works best on X11. On Wayland, you may need to:
- Right-click the window title bar → "Always on Top"
- Install `gnome-shell-extension-always-on-top` for GNOME

### PyAudio installation fails

```bash
# Install PortAudio development files first
sudo apt install portaudio19-dev
pip install pyaudio
```

## 📁 Project Structure

```
audio-capture/
├── main.py                 # Application entry point
├── audio/
│   ├── __init__.py
│   ├── capture.py          # PyAudio microphone capture
│   └── vad.py              # Voice activity detection
├── transcription/
│   ├── __init__.py
│   └── groq_service.py     # Groq Whisper API integration
├── ui/
│   ├── __init__.py
│   └── main_window.py      # GTK3 main window
├── requirements.txt        # Python dependencies
├── setup.sh                # Ubuntu setup script
└── README.md               # This file
```

## 📄 License

MIT License - feel free to use this in your own projects!

## 🙏 Acknowledgments

- [Groq](https://groq.com) for the lightning-fast Whisper API
- [webrtcvad](https://github.com/wiseman/py-webrtcvad) for voice activity detection
- [PyAudio](https://people.csail.mit.edu/hubert/pyaudio/) for audio capture
