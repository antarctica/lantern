from http import HTTPStatus
from unittest.mock import patch

import pytest
from flask import Flask
from flask.testing import FlaskClient

from scar_add_metadata_toolbox import create_app
from scar_add_metadata_toolbox.config import (
    Config,
    TestingConfig as _TestingConfig,
)  # TestingConfig renamed to prevent PyTest trying to test the class


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
    assert "scar-add-metadata-toolbox version: N/A" in result.output


@pytest.mark.usefixtures("app_client")
def test_health(app_client: FlaskClient):
    expected_response = {
        "description": "Server side endpoints for the SCAR Antarctic Digital Database " "(ADD) Metadata Toolbox.",
        "links": {
            "about": "https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox",
            "describedBy": "https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/blob/vN/A/README.md",
            "self": "http://localhost/meta/health/v1",
        },
        "releaseId": "N/A",
        "status": "pass",
        "version": 1,
    }
    response = app_client.get("/meta/health/v1")
    assert response.status_code == HTTPStatus.OK
    assert response.mimetype == "application/json"
    assert response.json == expected_response
