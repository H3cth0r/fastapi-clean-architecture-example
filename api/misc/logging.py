"""
Centralized logging configuration for the API.

This module provides a simple, structured logging setup that follows
best practices for production applications while remaining easy to
understand for educational purposes.
"""

import logging
import logging.config

from api.misc.config import config

# Environment-aware log level
# - INFO for production (cleaner logs, less noise)
# - DEBUG for development (detailed information for debugging)
LOG_LEVEL = "INFO" if config.is_production() else "DEBUG"

# Log format with timestamp
# %(levelprefix)s - Colored log level (INFO, DEBUG, etc.) provided by uvicorn
# %(asctime)s - Timestamp when the log was created
# %(message)s - The actual log message
LOG_FORMAT: str = "%(levelprefix)s [%(asctime)s] %(message)s"

# Logging configuration dictionary
# This follows Python's logging.config.dictConfig format
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,  # Keep existing loggers from libraries
    "formatters": {
        "default": {
            "()": "uvicorn.logging.DefaultFormatter",  # Use uvicorn's formatter for colors
            "fmt": LOG_FORMAT,
            "datefmt": "%Y-%m-%d %H:%M:%S",  # ISO-like timestamp format
        },
        "access": {
            "()": "uvicorn.logging.AccessFormatter",
            "fmt": '%(levelprefix)s [%(asctime)s] %(client_addr)s - "%(request_line)s" %(status_code)s',
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
        },
        "access": {
            "class": "logging.StreamHandler",
            "formatter": "access",
        },
    },
    "loggers": {
        "uvicorn": {
            "handlers": ["console"],
            "level": LOG_LEVEL,
            "propagate": False,
        },
        "uvicorn.access": {
            "handlers": ["access"],
            "level": "INFO",
            "propagate": False,
        },
    },
    "root": {
        "handlers": ["console"],
        "level": LOG_LEVEL,
    },
}

# Apply the logging configuration
logging.config.dictConfig(LOGGING_CONFIG)

# Set log levels for third-party libraries
# This prevents them from being too noisy in development
logging.getLogger("tortoise").setLevel(LOG_LEVEL)
logging.getLogger("tortoise.db_client").setLevel(LOG_LEVEL)


def get_logger() -> logging.Logger:
    """
    Get the application logger.

    This is the centralized way to get a logger instance throughout
    the application. All modules should use this function instead of
    creating their own loggers.

    Returns:
        logging.Logger: Configured logger instance

    Example:
        from api.misc.logging import get_logger

        logger = get_logger()
        logger.info("[module:function] Something happened")
    """
    return logging.getLogger("api-logger")
