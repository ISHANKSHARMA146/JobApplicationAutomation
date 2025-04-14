"""
Logger Module

This module provides a custom logger for the application with appropriate formatting and configuration.
"""

import os
import sys
import logging
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from datetime import datetime
from typing import Optional

from loguru import logger as loguru_logger


# Default log format
DEFAULT_LOG_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
    "<level>{message}</level>"
)

# Global logger instance
_logger = None


def setup_logger(log_directory: str = "logs", log_level: str = "INFO") -> loguru_logger:
    """
    Set up and configure the logger.
    
    Args:
        log_directory: Directory to store log files
        log_level: Minimum log level to record (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Returns:
        loguru.logger: Configured logger instance
    """
    global _logger
    
    # Create log directory if it doesn't exist
    os.makedirs(log_directory, exist_ok=True)
    
    # Set up timestamp for log filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_directory, f"job_automation_{timestamp}.log")
    latest_log = os.path.join(log_directory, "latest.log")
    
    # Configure loguru logger
    loguru_logger.remove()  # Remove default handler
    
    # Add console handler
    loguru_logger.add(
        sys.stderr,
        format=DEFAULT_LOG_FORMAT,
        level=log_level,
        colorize=True
    )
    
    # Add file handler for the timestamped log
    loguru_logger.add(
        log_file,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level=log_level,
        rotation="10 MB",  # Rotate when file reaches 10 MB
        retention="1 month",  # Keep logs for 1 month
        compression="zip"  # Compress rotated logs
    )
    
    # Add file handler for the "latest.log" file
    loguru_logger.add(
        latest_log,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level=log_level,
        rotation="1 day",  # Rotate daily
        retention=3,  # Keep only last 3 days
    )
    
    # Set global logger
    _logger = loguru_logger
    
    _logger.info(f"Logger initialized. Log file: {log_file}")
    return _logger


def get_logger() -> loguru_logger:
    """
    Get the configured logger instance.
    If logger hasn't been set up yet, set it up with default parameters.
    
    Returns:
        loguru.logger: Logger instance
    """
    global _logger
    
    if _logger is None:
        _logger = setup_logger()
        
    return _logger


# Optional: Legacy-style logging adapter for compatibility with libraries expecting standard logging
class StandardLibraryLoggerAdapter:
    """
    Adapter that makes loguru work with libraries expecting standard library logger.
    """
    
    def __init__(self, logger):
        self.logger = logger
    
    def debug(self, msg, *args, **kwargs):
        self.logger.debug(msg, *args, **kwargs)
    
    def info(self, msg, *args, **kwargs):
        self.logger.info(msg, *args, **kwargs)
    
    def warning(self, msg, *args, **kwargs):
        self.logger.warning(msg, *args, **kwargs)
    
    def error(self, msg, *args, **kwargs):
        self.logger.error(msg, *args, **kwargs)
    
    def exception(self, msg, *args, **kwargs):
        self.logger.exception(msg, *args, **kwargs)
    
    def critical(self, msg, *args, **kwargs):
        self.logger.critical(msg, *args, **kwargs)


def get_standard_logger(name: str = "job_automation") -> logging.Logger:
    """
    Get a standard library compatible logger.
    
    Args:
        name: Logger name
    
    Returns:
        logging.Logger: Standard library compatible logger
    """
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    
    return logger 