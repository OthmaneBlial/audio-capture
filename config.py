"""Configuration manager for Voice Transcriber."""

import os
import json
from typing import Any, Dict
from pathlib import Path

class ConfigManager:
    """Manages application settings persistence."""
    
    DEFAULT_CONFIG = {
        "api_key": "",
        "font_size": 17,
        "language": "auto",  # auto, en, fr, es, etc.
        "translate_to_english": False,
        "opacity": 1.0,
        "window_width": 480,
        "window_height": 400,
        "sticky_mode": False
    }
    
    def __init__(self):
        """Initialize config manager."""
        self._config_dir = Path.home() / ".config" / "voice-transcriber"
        self._config_file = self._config_dir / "config.json"
        self._config = self.DEFAULT_CONFIG.copy()
        
        # Load environment API key as fallback/initial default
        env_key = os.environ.get("GROQ_API_KEY")
        if env_key:
            self._config["api_key"] = env_key
            
        self.load()
        
    def load(self) -> None:
        """Load configuration from file."""
        try:
            if self._config_file.exists():
                with open(self._config_file, 'r') as f:
                    saved_config = json.load(f)
                    # Update defaults with saved values (preserves new default keys)
                    self._config.update(saved_config)
        except Exception as e:
            print(f"Error loading config: {e}")
            
    def save(self) -> None:
        """Save configuration to file."""
        try:
            self._config_dir.mkdir(parents=True, exist_ok=True)
            with open(self._config_file, 'w') as f:
                json.dump(self._config, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")
            
    def get(self, key: str) -> Any:
        """Get a configuration value."""
        return self._config.get(key, self.DEFAULT_CONFIG.get(key))
        
    def set(self, key: str, value: Any) -> None:
        """Set a configuration value and save."""
        self._config[key] = value
        self.save()
