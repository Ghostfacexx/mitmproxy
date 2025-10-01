"""
Configuration management for the NFC proxy system.
"""
import json
import os
from typing import Dict, Any, Optional
from ..utils.logger import Logger

logger = Logger("Config")


def load_config(config_path: str) -> Dict[str, Any]:
    """
    Load configuration from a JSON file.
    
    Args:
        config_path: Path to the configuration file
        
    Returns:
        Configuration dictionary
    """
    logger.info(f"Loading config from {config_path}")
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            logger.info(f"Config loaded successfully: {json.dumps(config, indent=2)}")
            return config
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        # Return default configuration
        return get_default_config()


def get_default_config() -> Dict[str, Any]:
    """Return default configuration if file loading fails."""
    return {
        "tcp_port": 8081,
        "http_port": 8082,
        "block_all": False,
        "bypass_pin": True,
        "log_level": "INFO",
        "keys_directory": "keys",
        "logs_directory": "logs"
    }


def save_config(config: Dict[str, Any], config_path: str) -> None:
    """
    Save configuration to a JSON file.
    
    Args:
        config: Configuration dictionary
        config_path: Path to save the configuration
    """
    try:
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
        logger.info(f"Config saved to {config_path}")
    except Exception as e:
        logger.error(f"Error saving config: {e}")


class ConfigManager:
    """Centralized configuration manager."""
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = config_dir
        self.proxy_config = load_config(os.path.join(config_dir, "proxy_config.json"))
        self.mitm_config = load_config(os.path.join(config_dir, "mitm_config.json"))
    
    def get_proxy_config(self) -> Dict[str, Any]:
        """Get proxy configuration."""
        return self.proxy_config
    
    def get_mitm_config(self) -> Dict[str, Any]:
        """Get MITM configuration."""
        return self.mitm_config
    
    def update_proxy_config(self, updates: Dict[str, Any]) -> None:
        """Update proxy configuration."""
        self.proxy_config.update(updates)
        save_config(self.proxy_config, os.path.join(self.config_dir, "proxy_config.json"))
    
    def update_mitm_config(self, updates: Dict[str, Any]) -> None:
        """Update MITM configuration."""
        self.mitm_config.update(updates)
        save_config(self.mitm_config, os.path.join(self.config_dir, "mitm_config.json"))
