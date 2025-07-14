"""
Logging configuration module
"""
import logging
import sys
from pathlib import Path
from typing import Optional

from ..config.settings import settings


def setup_logger(
    name: str,
    level: str = None,
    log_file: Optional[str] = None,
    format_string: Optional[str] = None
) -> logging.Logger:
    """Setup logger configuration"""
    logger = logging.getLogger(name)
    
    # Avoid duplicate setup
    if logger.handlers:
        return logger
    
    # Set log level
    log_level = level or settings.log_level
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Set log format
    log_format = format_string or settings.log_format
    formatter = logging.Formatter(log_format)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler
    file_path = log_file or settings.log_file
    if file_path:
        log_dir = Path(file_path).parent
        log_dir.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(file_path)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """Get logger instance"""
    return setup_logger(name)


# Default logger instance
default_logger = get_logger("price_cage")