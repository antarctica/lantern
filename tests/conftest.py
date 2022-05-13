from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import pytest

from scar_add_metadata_toolbox import create_app
from tests.scar_add_metadata_toolbox.classes import (
    MockCSWClient,
    MockCSWClientAuthError,
    MockCSWClientAuthInsufficient,
    MockCSWClientAuthMissing,
    MockCSWClientInsertsFail,
    MockCSWClientServerNotSetup,
    MockCSWServer,
    MockCSWServerAuthTokenError,
    MockCSWServerInsufficientAuthToken,
    MockCSWServerMissingAuthToken,
    MockCSWServerNotSetup,
    MockCSWServerRequestsFail,
    MockPublicClientApplication,
)


@pytest.fixture
def app():
    with patch("scar_add_metadata_toolbox.config.PublicClientApplication") as mock_msal_client_application:
        mock_msal_client_application.side_effect = MockPublicClientApplication
        app = create_app()
        return app


@pytest.fixture
@pytest.mark.usefixtures("app")
def app_runner(app):
    return app.test_cli_runner()


@pytest.fixture
def app_runner_mocked_csw():
    with patch("scar_add_metadata_toolbox.classes.CSWClient") as mock_csw_client:
        mock_csw_client.side_effect = MockCSWClient
        app = create_app()
        return app.test_cli_runner()


@pytest.fixture
def app_runner_mocked_csw_inserts_fail():
    with patch("scar_add_metadata_toolbox.classes.CSWClient") as mock_csw_client:
        mock_csw_client.side_effect = MockCSWClientInsertsFail
        app = create_app()
        return app.test_cli_runner()


@pytest.fixture
def app_runner_mocked_csw_not_setup():
    with patch("scar_add_metadata_toolbox.classes.CSWClient") as mock_csw_client:
        mock_csw_client.side_effect = MockCSWClientServerNotSetup
        app = create_app()
        return app.test_cli_runner()


@pytest.fixture
def app_runner_mocked_csw_auth_token_error():
    with patch("scar_add_metadata_toolbox.classes.CSWClient") as mock_csw_client:
        mock_csw_client.side_effect = MockCSWClientAuthError
        app = create_app()
        return app.test_cli_runner()


@pytest.fixture
def app_runner_mocked_csw_missing_auth_token():
    with patch("scar_add_metadata_toolbox.classes.CSWClient") as mock_csw_client:
        mock_csw_client.side_effect = MockCSWClientAuthMissing
        app = create_app()
        return app.test_cli_runner()


@pytest.fixture
def app_runner_mocked_csw_insufficient_auth_token():
    with patch("scar_add_metadata_toolbox.classes.CSWClient") as mock_csw_client:
        mock_csw_client.side_effect = MockCSWClientAuthInsufficient
        app = create_app()
        return app.test_cli_runner()


@pytest.fixture
def app_static_site():
    with patch(
        "scar_add_metadata_toolbox.classes.CSWClient"
    ) as mock_csw_client, TemporaryDirectory() as site_directory:
        mock_csw_client.side_effect = MockCSWClient

        app = create_app()
        app.config["SITE_PATH"] = Path(site_directory)
        return app


@pytest.fixture
def app_runner_mocked_csw_server():
    with patch("scar_add_metadata_toolbox.utils.CSWServer") as mock_csw_server:
        mock_csw_server.side_effect = MockCSWServer

        app = create_app()
        return app.test_cli_runner()


@pytest.fixture
def app_client_mocked_csw_server():
    with patch("scar_add_metadata_toolbox.utils.CSWServer") as mock_csw_server:
        mock_csw_server.side_effect = MockCSWServer

        app = create_app()
        return app.test_client()


@pytest.fixture
def app_client_mocked_csw_server_not_setup():
    with patch("scar_add_metadata_toolbox.utils.CSWServer") as mock_csw_server:
        mock_csw_server.side_effect = MockCSWServerNotSetup

        app = create_app()
        return app.test_client()


@pytest.fixture
def app_client_mocked_csw_server_requests_fail():
    with patch("scar_add_metadata_toolbox.utils.CSWServer") as mock_csw_server:
        mock_csw_server.side_effect = MockCSWServerRequestsFail

        app = create_app()
        return app.test_client()


@pytest.fixture
def app_client_mocked_csw_server_auth_token_error():
    with patch("scar_add_metadata_toolbox.utils.CSWServer") as mock_csw_server:
        mock_csw_server.side_effect = MockCSWServerAuthTokenError

        app = create_app()
        return app.test_client()


@pytest.fixture
def app_client_mocked_csw_server_missing_auth_token():
    with patch("scar_add_metadata_toolbox.utils.CSWServer") as mock_csw_server:
        mock_csw_server.side_effect = MockCSWServerMissingAuthToken

        app = create_app()
        return app.test_client()


@pytest.fixture
def app_client_mocked_csw_server_insufficient_auth_token():
    with patch("scar_add_metadata_toolbox.utils.CSWServer") as mock_csw_server:
        mock_csw_server.side_effect = MockCSWServerInsufficientAuthToken

        app = create_app()
        return app.test_client()
