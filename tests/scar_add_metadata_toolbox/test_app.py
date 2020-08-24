import pytest

from unittest.mock import patch

from flask import Flask

from scar_add_metadata_toolbox import create_app

# TestingConfig is renamed to prevent PyTest trying to test the class
from scar_add_metadata_toolbox.config import Config, TestingConfig as _TestingConfig


@pytest.mark.usefixtures("app")
def test_app(app):
    assert app is not None
    assert isinstance(app, Flask)


@pytest.mark.usefixtures("app")
def test_app_environment(app):
    assert app.config["TESTING"] is True


def test_app_no_environment():
    with patch("scar_add_metadata_toolbox._create_app_config") as mock_create_app_config:
        config = Config()
        mock_create_app_config.return_value = config

        app = create_app()
        assert app is not None
        assert isinstance(app, Flask)
        assert app.config["TESTING"] is False


def test_app_enable_sentry():
    with patch("scar_add_metadata_toolbox._create_app_config") as mock_create_app_config:
        config = _TestingConfig()
        config.APP_ENABLE_SENTRY = True
        mock_create_app_config.return_value = config

        app = create_app()
        assert app is not None
        assert isinstance(app, Flask)
        assert app.config["TESTING"] is True
        assert app.config["APP_ENABLE_SENTRY"] is True


@pytest.mark.usefixtures("app_runner")
def test_cli_help(app_runner):
    result = app_runner.invoke(args=["--help"])
    assert result.exit_code == 0
    assert "Show this message and exit." in result.output


@pytest.mark.usefixtures("app_runner")
def test_cli_version(app_runner):
    result = app_runner.invoke(args=["version"])
    assert result.exit_code == 0
    assert "Unknown version: N/A" in result.output
