from unittest.mock import patch

import pytest
from flask import Flask
from flask.testing import FlaskCliRunner

from scar_add_metadata_toolbox import create_app
from scar_add_metadata_toolbox.config import (
    Config,
)  # TestingConfig renamed to prevent Pytest trying to test the class
from scar_add_metadata_toolbox.config import (
    TestingConfig as _TestingConfig,
)


def test_app(app: Flask):
    assert app is not None
    assert isinstance(app, Flask)


@pytest.mark.usefixtures("app")
def test_app_environment(app: Flask):
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


def test_cli_help(app_runner: FlaskCliRunner):
    result = app_runner.invoke(args=["--help"])
    assert result.exit_code == 0
    assert "Show this message and exit." in result.output


def test_cli_version(app_runner: FlaskCliRunner):
    result = app_runner.invoke(args=["version"])
    assert result.exit_code == 0
    assert "scar-add-metadata-toolbox version: N/A" in result.output
