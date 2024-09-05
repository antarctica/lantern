import os

from flask import Flask
from flask.testing import FlaskCliRunner

from scar_add_metadata_toolbox import create_app
from scar_add_metadata_toolbox.config import Config


def test_app(app: Flask):
    assert app is not None
    assert isinstance(app, Flask)


def test_app_enable_sentry():
    env_bck = os.environ.get("APP_ENABLE_SENTRY", False)
    os.environ["APP_ENABLE_SENTRY"] = "true"

    app = create_app()
    assert app is not None
    assert isinstance(app, Flask)
    assert app.config["APP_ENABLE_SENTRY"] is True

    if env_bck:
        os.environ["APP_ENABLE_SENTRY"] = env_bck


def test_cli_help(app_runner: FlaskCliRunner):
    result = app_runner.invoke(args=["--help"])
    assert result.exit_code == 0
    assert "Show this message and exit." in result.output


def test_cli_version(app_runner: FlaskCliRunner):
    config = Config()

    result = app_runner.invoke(args=["version"])
    assert result.exit_code == 0
    assert f"scar-add-metadata-toolbox version: {config.VERSION}" in result.output
