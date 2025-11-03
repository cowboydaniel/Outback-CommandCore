"""
Configuration settings for the CommandCore Launcher.
"""
import os
import json
from pathlib import Path


class Config:
    """Application configuration manager."""
    
    def __init__(self):
        """Initialize configuration with default values."""
        self.app_name = "CommandCore Launcher"
        self.version = "1.0.0"
        self.organization = "Outback Electronics"
        
        # Application paths
        self.app_dir = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.config_dir = self.app_dir / "config"
        self.data_dir = self.app_dir / "data"
        self.logs_dir = self.app_dir / "logs"
        
        # Create necessary directories
        self._ensure_directories()
        
        # UI Configuration
        self.ui = {
            "theme": "dark",
            "font_family": "Segoe UI",
            "font_size": 10,
            "window_width": 1024,
            "window_height": 768,
            "animation_enabled": True,
            "animation_duration": 200  # ms
        }
        
        # Load user settings if they exist
        self.load_settings()
    
    def _ensure_directories(self):
        """Ensure all required directories exist."""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
    
    def get_settings_path(self):
        """Get the path to the settings file."""
        return self.config_dir / "settings.json"
    
    def load_settings(self):
        """Load user settings from file."""
        settings_path = self.get_settings_path()
        if settings_path.exists():
            try:
                with open(settings_path, 'r') as f:
                    settings = json.load(f)
                    self.ui.update(settings.get('ui', {}))
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading settings: {e}")
    
    def save_settings(self):
        """Save current settings to file."""
        settings_path = self.get_settings_path()
        try:
            with open(settings_path, 'w') as f:
                json.dump({
                    'ui': self.ui
                }, f, indent=4)
        except IOError as e:
            print(f"Error saving settings: {e}")
