"""Unit tests for configuration system."""

import pytest
from config import Settings, get_settings


@pytest.mark.unit
def test_settings_creation():
    """Test that settings can be created with defaults."""
    settings = Settings()
    assert settings.app_name == "Agentic AI Testing System"
    assert settings.debug is False
    assert settings.log_level == "INFO"


@pytest.mark.unit
def test_settings_llm_config():
    """Test LLM configuration defaults."""
    settings = Settings()
    assert settings.llm.provider == "openai"
    assert settings.llm.model == "gpt-4"
    assert settings.llm.temperature == 0.7
    assert settings.llm.max_retries == 3


@pytest.mark.unit
def test_settings_database_config():
    """Test database configuration."""
    settings = Settings()
    assert settings.database.type == "sqlite"
    assert "sqlite:///" in settings.database.connection_string


@pytest.mark.unit
def test_settings_execution_config():
    """Test execution configuration defaults."""
    settings = Settings()
    assert settings.execution.max_parallel_tests == 10
    assert settings.execution.test_timeout == 300
    assert settings.execution.virtual_env_enabled is True


@pytest.mark.unit
def test_get_settings_singleton():
    """Test that get_settings returns the same instance."""
    settings1 = get_settings()
    settings2 = get_settings()
    assert settings1 is settings2


@pytest.mark.unit
def test_custom_settings(test_settings):
    """Test custom settings from fixture."""
    assert test_settings.debug is True
    assert test_settings.log_level == "DEBUG"
    assert test_settings.database.type == "sqlite"
