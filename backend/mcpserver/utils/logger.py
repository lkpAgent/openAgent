"""Logging configuration for the MCP server."""

import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logger(
    name: str = "mcpserver",
    level: str = "INFO",
    log_file: Optional[str] = None
) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.handlers.clear()
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


# Default logger
logger = setup_logger()


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(f"mcpserver.{name}")