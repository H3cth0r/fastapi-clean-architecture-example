"""
Tests for logging configuration.

These tests verify that the logging system is configured correctly
and returns the expected logger instance.

Note: These tests do NOT need database access, so they are not marked
with @pytest.mark.use_db and will not trigger database initialization.
"""

import logging
from unittest.mock import patch

from api.misc.logging import get_logger


def test_get_logger_returns_logger_instance():
    """Test that get_logger returns a logging.Logger instance"""
    logger = get_logger()

    assert isinstance(logger, logging.Logger)
    assert logger.name == "api-logger"


def test_get_logger_returns_same_instance():
    """Test that get_logger returns the same logger instance each time"""
    logger1 = get_logger()
    logger2 = get_logger()

    assert logger1 is logger2


@patch("logging.getLogger")
def test_get_logger_calls_logging_get_logger(mock_get_logger):
    """Test that get_logger calls logging.getLogger with correct name"""
    mock_logger = logging.Logger("test")
    mock_get_logger.return_value = mock_logger

    logger = get_logger()

    mock_get_logger.assert_called_once_with("api-logger")
    assert logger == mock_logger
