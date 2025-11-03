"""
Configuration management for Hack Attack.
Handles loading and validation of configuration settings.
"""
import os
from pathlib import Path
from typing import Dict, Any, Optional
import yaml
from dotenv import load_dotenv

class Config:
    """Central configuration management for Hack Attack."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        # Load environment variables from .env file if it exists
        load_dotenv()
        
        # Default configuration
        self._config = {
            "app": {
                "name": "Hack Attack",
                "version": "0.1.0",
                "environment": os.getenv("APP_ENV", "development"),
                "debug": os.getenv("DEBUG", "false").lower() == "true",
            },
            "security": {
                "max_scan_targets": int(os.getenv("MAX_SCAN_TARGETS", "10")),
                "rate_limit": int(os.getenv("RATE_LIMIT", "60")),  # requests per minute
            },
            "logging": {
                "level": os.getenv("LOG_LEVEL", "INFO"),
                "file": os.getenv("LOG_FILE", "hack_attack.log"),
            },
        }
        
        # Load additional config from YAML if exists
        config_path = Path("config/config.yaml")
        if config_path.exists():
            with open(config_path, 'r') as f:
                yaml_config = yaml.safe_load(f) or {}
                self._deep_update(self._config, yaml_config)
        
        self._initialized = True
    
    def _deep_update(self, original: Dict[Any, Any], update: Dict[Any, Any]) -> None:
        """Recursively update a dictionary."""
        for key, value in update.items():
            if key in original and isinstance(original[key], dict) and isinstance(value, dict):
                self._deep_update(original[key], value)
            else:
                original[key] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value by dot notation."""
        keys = key.split('.')
        value = self._config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def __getitem__(self, key: str) -> Any:
        return self.get(key)
    
    def to_dict(self) -> Dict[str, Any]:
        """Return a deep copy of the configuration as a dictionary."""
        import copy
        return copy.deepcopy(self._config)

# Global configuration instance
config = Config()
