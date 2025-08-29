"""Logging configuration for ChatAgent."""

import logging
import logging.handlers
from pathlib import Path
from typing import Optional

from .config import LoggingSettings


def setup_logging(logging_config: LoggingSettings) -> None:
    """Setup application logging."""
    
    # Create logs directory if it doesn't exist
    log_file = Path(logging_config.file)
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, logging_config.level.upper()))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(logging_config.format)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        filename=logging_config.file,
        maxBytes=logging_config.max_bytes,
        backupCount=logging_config.backup_count,
        encoding="utf-8"
    )
    file_handler.setLevel(getattr(logging, logging_config.level.upper()))
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    # Set specific logger levels
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    
    logging.info("Logging configured successfully")


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(name or __name__)