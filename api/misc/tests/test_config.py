"""
Tests for configuration module.
"""

from unittest.mock import patch

from api.misc.config import Config, EnvName


def test_config_is_production_returns_true_for_production():
    """Test that is_production returns True when environment is production."""
    with patch.dict(
        "os.environ",
        {
            "ENVIRONMENT": "production",
            "POSTGRES_URL": "postgres://user:pass@localhost:5432/db",
        },
    ):
        config = Config()
        assert config.is_production() is True


def test_config_is_production_returns_false_for_development():
    """Test that is_production returns False when environment is development."""
    with patch.dict(
        "os.environ",
        {
            "ENVIRONMENT": "development",
            "POSTGRES_URL": "postgres://user:pass@localhost:5432/db",
        },
    ):
        config = Config()
        assert config.is_production() is False


def test_config_is_production_returns_false_for_testing():
    """Test that is_production returns False when environment is testing."""
    with patch.dict(
        "os.environ",
        {
            "ENVIRONMENT": "testing",
            "POSTGRES_URL": "postgres://user:pass@localhost:5432/db",
        },
    ):
        config = Config()
        assert config.is_production() is False


def test_config_is_production_returns_false_for_staging():
    """Test that is_production returns False when environment is staging."""
    with patch.dict(
        "os.environ",
        {
            "ENVIRONMENT": "staging",
            "POSTGRES_URL": "postgres://user:pass@localhost:5432/db",
        },
    ):
        config = Config()
        assert config.is_production() is False
