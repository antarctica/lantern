from collections import namedtuple
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import pytest
from flask.testing import FlaskClient

from scar_add_metadata_toolbox import create_app
from tests.scar_add_metadata_toolbox_tests.classes import (
    create_mock_auth,
    MockCSWClient,
    MockCSWClientAuthError,
    MockCSWClientAuthInsufficient,
    MockCSWClientAuthMissing,
    MockCSWClientInsertsFail,
    MockCSWClientServerNotSetup,
    MockCSWServer,
    MockCSWServerAmbiguousRequestError,
    MockCSWServerAuthTokenError,
    MockCSWServerBackingDBNotSetup,
    MockCSWServerBackingRepoNotSetup,
    MockCSWServerInsufficientAuthToken,
    MockCSWServerMissingAuthToken,
    MockCSWServerNoRequestType,
    MockCSWServerRequestsFail,
    MockCSWServerRevisionTrackingDisabled,
    MockCSWServerRevisionTrackingInvalidCredentials,
    MockCSWServerUnmappedRequestError,
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
@pytest.mark.usefixtures("app")
def app_client(app) -> FlaskClient:
    with app.test_client() as client:
        return client


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
def app_runner_mocked_csw_server_tracking_not_enabled():
    with patch("scar_add_metadata_toolbox.utils.CSWServer") as mock_csw_server:
        mock_csw_server.side_effect = MockCSWServerRevisionTrackingDisabled

        app = create_app()
        return app.test_cli_runner()


@pytest.fixture
def app_runner_mocked_csw_server_tracking_invalid_credentials():
    with patch("scar_add_metadata_toolbox.utils.CSWServer") as mock_csw_server:
        mock_csw_server.side_effect = MockCSWServerRevisionTrackingInvalidCredentials

        app = create_app()
        return app.test_cli_runner()


@pytest.fixture
def app_static_site():
    with (
        patch("scar_add_metadata_toolbox.classes.CSWClient") as mock_csw_client,
        TemporaryDirectory() as site_directory,
    ):
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
def app_client_mocked_csw_server_backing_db_not_setup():
    with patch("scar_add_metadata_toolbox.utils.CSWServer") as mock_csw_server:
        mock_csw_server.side_effect = MockCSWServerBackingDBNotSetup

        app = create_app()
        return app.test_client()


@pytest.fixture
def app_client_mocked_csw_server_backing_repo_not_setup():
    with patch("scar_add_metadata_toolbox.utils.CSWServer") as mock_csw_server:
        mock_csw_server.side_effect = MockCSWServerBackingRepoNotSetup

        app = create_app()
        return app.test_client()


@pytest.fixture
def app_client_mocked_csw_server_requests_fail():
    with patch("scar_add_metadata_toolbox.utils.CSWServer") as mock_csw_server:
        mock_csw_server.side_effect = MockCSWServerRequestsFail

        app = create_app()
        return app.test_client()


@pytest.fixture
def app_client_mocked_csw_server_no_request_type():
    with patch("scar_add_metadata_toolbox.utils.CSWServer") as mock_csw_server:
        mock_csw_server.side_effect = MockCSWServerNoRequestType

        app = create_app()
        return app.test_client()


@pytest.fixture
def app_client_mocked_csw_server_ambiguous_request():
    with patch("scar_add_metadata_toolbox.utils.CSWServer") as mock_csw_server:
        mock_csw_server.side_effect = MockCSWServerAmbiguousRequestError

        app = create_app()
        return app.test_client()


@pytest.fixture
def app_client_mocked_csw_server_unmapped_request():
    with patch("scar_add_metadata_toolbox.utils.CSWServer") as mock_csw_server:
        mock_csw_server.side_effect = MockCSWServerUnmappedRequestError

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


@pytest.fixture
def app_static_site_auth():
    with (
        patch("scar_add_metadata_toolbox.classes.CSWClient") as mock_csw_client,
        TemporaryDirectory() as site_directory,
        patch("scar_add_metadata_toolbox.FlaskAzureOauth") as mock_flask_azure_oauth,
    ):
        mock_flask_azure_oauth.side_effect = create_mock_auth()
        mock_csw_client.side_effect = MockCSWClient

        app = create_app()
        app.config["SITE_PATH"] = Path(site_directory)
        return app


@pytest.fixture
def app_static_site_auth_csw_not_setup():
    with (
        patch("scar_add_metadata_toolbox.classes.CSWClient") as mock_csw_client,
        TemporaryDirectory() as site_directory,
        patch("scar_add_metadata_toolbox.FlaskAzureOauth") as mock_flask_azure_oauth,
    ):
        mock_flask_azure_oauth.side_effect = create_mock_auth()
        mock_csw_client.side_effect = MockCSWClientServerNotSetup

        app = create_app()
        app.config["SITE_PATH"] = Path(site_directory)
        return app


@pytest.fixture
def app_static_site_auth_csw_auth_token_error():
    with (
        patch("scar_add_metadata_toolbox.classes.CSWClient") as mock_csw_client,
        TemporaryDirectory() as site_directory,
        patch("scar_add_metadata_toolbox.FlaskAzureOauth") as mock_flask_azure_oauth,
    ):
        mock_flask_azure_oauth.side_effect = create_mock_auth()
        mock_csw_client.side_effect = MockCSWClientAuthError

        app = create_app()
        app.config["SITE_PATH"] = Path(site_directory)
        return app


@pytest.fixture
def app_static_site_auth_csw_missing_auth_token():
    with (
        patch("scar_add_metadata_toolbox.classes.CSWClient") as mock_csw_client,
        TemporaryDirectory() as site_directory,
        patch("scar_add_metadata_toolbox.FlaskAzureOauth") as mock_flask_azure_oauth,
    ):
        mock_flask_azure_oauth.side_effect = create_mock_auth()
        mock_csw_client.side_effect = MockCSWClientAuthMissing

        app = create_app()
        app.config["SITE_PATH"] = Path(site_directory)
        return app


@pytest.fixture
def app_static_site_auth_csw_insufficient_auth_token():
    with (
        patch("scar_add_metadata_toolbox.classes.CSWClient") as mock_csw_client,
        TemporaryDirectory() as site_directory,
        patch("scar_add_metadata_toolbox.FlaskAzureOauth") as mock_flask_azure_oauth,
    ):
        mock_flask_azure_oauth.side_effect = create_mock_auth()
        mock_csw_client.side_effect = MockCSWClientAuthInsufficient

        app = create_app()
        app.config["SITE_PATH"] = Path(site_directory)
        return app


AppAuthScopes = namedtuple("AppAuthScopes", ["app", "auth_scopes"])


@pytest.fixture
def app_static_site_auth_get_scopes():
    with (
        patch("scar_add_metadata_toolbox.classes.CSWClient") as mock_csw_client,
        TemporaryDirectory() as site_directory,
        patch("scar_add_metadata_toolbox.FlaskAzureOauth") as mock_flask_azure_oauth,
    ):
        auth_scopes = []

        mock_flask_azure_oauth.side_effect = create_mock_auth(auth_scopes)
        mock_csw_client.side_effect = MockCSWClient

        app = create_app()
        app.config["SITE_PATH"] = Path(site_directory)
        return AppAuthScopes(app, auth_scopes)
