"""
Logging utilities for the NFC proxy system.
"""
import time
import os
from typing import Optional


def setup_logger(log_directory: str = "logs") -> None:
    """Ensure log directory exists."""
    os.makedirs(log_directory, exist_ok=True)


def log(message: str, level: str = "INFO", log_file: Optional[str] = None) -> None:
    """
    Log a message with timestamp to both console and file.
    
    Args:
        message: Message to log
        level: Log level (INFO, ERROR, DEBUG, WARNING)
        log_file: Optional specific log file path
    """
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    formatted_message = f"[{timestamp}] [{level}] {message}"
    
    # Print to console
    print(formatted_message)
    
    # Write to file
    try:
        default_log = os.path.join("logs", "nfcgate_proxy.log")
        target_log = log_file or default_log
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(target_log), exist_ok=True)
        
        with open(target_log, 'a', encoding='utf-8') as f:
            f.write(f"{formatted_message}\n")
    except Exception as e:
        print(f"Failed to write log: {e}")


class Logger:
    """Logger class for consistent logging across the application."""
    
    def __init__(self, component_name: str, log_file: Optional[str] = None):
        self.component_name = component_name
        self.log_file = log_file
    
    def info(self, message: str) -> None:
        """Log info message."""
        log(f"[{self.component_name}] {message}", "INFO", self.log_file)
    
    def error(self, message: str) -> None:
        """Log error message."""
        log(f"[{self.component_name}] {message}", "ERROR", self.log_file)
    
    def debug(self, message: str) -> None:
        """Log debug message."""
        log(f"[{self.component_name}] {message}", "DEBUG", self.log_file)
    
    def warning(self, message: str) -> None:
        """Log warning message."""
        log(f"[{self.component_name}] {message}", "WARNING", self.log_file)
