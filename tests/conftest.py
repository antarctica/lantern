from collections import namedtuple
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import pytest
from flask import Flask
from flask.testing import FlaskClient, FlaskCliRunner

from scar_add_metadata_toolbox import create_app
from tests.scar_add_metadata_toolbox_tests.classes import (
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


@pytest.fixture()
def app() -> Flask:
    """Patched application to bypass auth."""
    with patch("scar_add_metadata_toolbox.config.PublicClientApplication") as mock_msal_client_application:
        mock_msal_client_application.side_effect = MockPublicClientApplication
        return create_app()


@pytest.fixture()
def app_runner(app: Flask) -> FlaskCliRunner:
    """App runner."""
    return app.test_cli_runner()


@pytest.fixture()
def app_client(app: Flask) -> FlaskClient:
    """App client."""
    with app.test_client() as client:
        return client


@pytest.fixture()
def app_runner_mocked_csw() -> FlaskCliRunner:
    """App runner with mocked CSW client."""
    with patch("scar_add_metadata_toolbox.classes.CSWClient") as mock_csw_client:
        mock_csw_client.side_effect = MockCSWClient
        app = create_app()
        return app.test_cli_runner()


@pytest.fixture()
def app_runner_mocked_csw_inserts_fail() -> FlaskCliRunner:
    """App runner with mocked CSW client that fails to insert."""
    with patch("scar_add_metadata_toolbox.classes.CSWClient") as mock_csw_client:
        mock_csw_client.side_effect = MockCSWClientInsertsFail
        app = create_app()
        return app.test_cli_runner()


@pytest.fixture()
def app_runner_mocked_csw_not_setup() -> FlaskCliRunner:
    """App runner with mocked CSW client that is not setup."""
    with patch("scar_add_metadata_toolbox.classes.CSWClient") as mock_csw_client:
        mock_csw_client.side_effect = MockCSWClientServerNotSetup
        app = create_app()
        return app.test_cli_runner()


@pytest.fixture()
def app_runner_mocked_csw_auth_token_error() -> FlaskCliRunner:
    """App runner with mocked CSW client that has an auth token error."""
    with patch("scar_add_metadata_toolbox.classes.CSWClient") as mock_csw_client:
        mock_csw_client.side_effect = MockCSWClientAuthError
        app = create_app()
        return app.test_cli_runner()


@pytest.fixture()
def app_runner_mocked_csw_missing_auth_token() -> FlaskCliRunner:
    """App runner with mocked CSW client that is missing an auth token."""
    with patch("scar_add_metadata_toolbox.classes.CSWClient") as mock_csw_client:
        mock_csw_client.side_effect = MockCSWClientAuthMissing
        app = create_app()
        return app.test_cli_runner()


@pytest.fixture()
def app_runner_mocked_csw_insufficient_auth_token() -> FlaskCliRunner:
    """App runner with mocked CSW client that has an insufficient auth token."""
    with patch("scar_add_metadata_toolbox.classes.CSWClient") as mock_csw_client:
        mock_csw_client.side_effect = MockCSWClientAuthInsufficient
        app = create_app()
        return app.test_cli_runner()


@pytest.fixture()
def app_runner_mocked_csw_server_tracking_not_enabled() -> FlaskCliRunner:
    """App runner with mocked CSW server that has revision tracking disabled."""
    with patch("scar_add_metadata_toolbox.utils.CSWServer") as mock_csw_server:
        mock_csw_server.side_effect = MockCSWServerRevisionTrackingDisabled

        app = create_app()
        return app.test_cli_runner()


@pytest.fixture()
def app_runner_mocked_csw_server_tracking_invalid_credentials() -> FlaskCliRunner:
    """App runner with mocked CSW server that has invalid credentials."""
    with patch("scar_add_metadata_toolbox.utils.CSWServer") as mock_csw_server:
        mock_csw_server.side_effect = MockCSWServerRevisionTrackingInvalidCredentials

        app = create_app()
        return app.test_cli_runner()


@pytest.fixture()
def app_static_site() -> Flask:
    """Patched application to use fake CSW client and temp site directory."""
    with (
        patch("scar_add_metadata_toolbox.classes.CSWClient") as mock_csw_client,
        TemporaryDirectory() as site_directory,
    ):
        mock_csw_client.side_effect = MockCSWClient

        app = create_app()
        app.config["SITE_PATH"] = Path(site_directory)
        return app


@pytest.fixture()
def app_runner_mocked_csw_server() -> FlaskCliRunner:
    """App runner with mocked CSW server."""
    with patch("scar_add_metadata_toolbox.utils.CSWServer") as mock_csw_server:
        mock_csw_server.side_effect = MockCSWServer

        app = create_app()
        return app.test_cli_runner()


@pytest.fixture()
def app_client_mocked_csw_server() -> FlaskClient:
    """App client with mocked CSW server."""
    with patch("scar_add_metadata_toolbox.utils.CSWServer") as mock_csw_server:
        mock_csw_server.side_effect = MockCSWServer

        app = create_app()
        return app.test_client()


@pytest.fixture()
def app_client_mocked_csw_server_backing_db_not_setup() -> FlaskClient:
    """App client with mocked CSW server that has backing DB not setup."""
    with patch("scar_add_metadata_toolbox.utils.CSWServer") as mock_csw_server:
        mock_csw_server.side_effect = MockCSWServerBackingDBNotSetup

        app = create_app()
        return app.test_client()


@pytest.fixture()
def app_client_mocked_csw_server_backing_repo_not_setup() -> FlaskClient:
    """App client with mocked CSW server that has backing repo not setup."""
    with patch("scar_add_metadata_toolbox.utils.CSWServer") as mock_csw_server:
        mock_csw_server.side_effect = MockCSWServerBackingRepoNotSetup

        app = create_app()
        return app.test_client()


@pytest.fixture()
def app_client_mocked_csw_server_requests_fail() -> FlaskClient:
    """App client with mocked CSW server that fails requests."""
    with patch("scar_add_metadata_toolbox.utils.CSWServer") as mock_csw_server:
        mock_csw_server.side_effect = MockCSWServerRequestsFail

        app = create_app()
        return app.test_client()


@pytest.fixture()
def app_client_mocked_csw_server_no_request_type() -> FlaskClient:
    """App client with mocked CSW server that has no request type."""
    with patch("scar_add_metadata_toolbox.utils.CSWServer") as mock_csw_server:
        mock_csw_server.side_effect = MockCSWServerNoRequestType

        app = create_app()
        return app.test_client()


@pytest.fixture()
def app_client_mocked_csw_server_ambiguous_request() -> FlaskClient:
    """App client with mocked CSW server that has an ambiguous request."""
    with patch("scar_add_metadata_toolbox.utils.CSWServer") as mock_csw_server:
        mock_csw_server.side_effect = MockCSWServerAmbiguousRequestError

        app = create_app()
        return app.test_client()


@pytest.fixture()
def app_client_mocked_csw_server_unmapped_request() -> FlaskClient:
    """App client with mocked CSW server that has an unmapped request."""
    with patch("scar_add_metadata_toolbox.utils.CSWServer") as mock_csw_server:
        mock_csw_server.side_effect = MockCSWServerUnmappedRequestError

        app = create_app()
        return app.test_client()


@pytest.fixture()
def app_client_mocked_csw_server_auth_token_error() -> FlaskClient:
    """App client with mocked CSW server that has an auth token error."""
    with patch("scar_add_metadata_toolbox.utils.CSWServer") as mock_csw_server:
        mock_csw_server.side_effect = MockCSWServerAuthTokenError

        app = create_app()
        return app.test_client()


@pytest.fixture()
def app_client_mocked_csw_server_missing_auth_token() -> FlaskClient:
    """App client with mocked CSW server that is missing an auth token."""
    with patch("scar_add_metadata_toolbox.utils.CSWServer") as mock_csw_server:
        mock_csw_server.side_effect = MockCSWServerMissingAuthToken

        app = create_app()
        return app.test_client()


@pytest.fixture()
def app_client_mocked_csw_server_insufficient_auth_token() -> FlaskClient:
    """App client with mocked CSW server that has an insufficient auth token."""
    with patch("scar_add_metadata_toolbox.utils.CSWServer") as mock_csw_server:
        mock_csw_server.side_effect = MockCSWServerInsufficientAuthToken

        app = create_app()
        return app.test_client()


@pytest.fixture()
def app_static_site_auth() -> Flask:
    """Patched application to use fake CSW client and auth client."""
    with (
        patch("scar_add_metadata_toolbox.classes.CSWClient") as mock_csw_client,
        TemporaryDirectory() as site_directory,
        # patch("scar_add_metadata_toolbox.FlaskAzureOauth") as mock_flask_azure_oauth,
    ):
        # mock_flask_azure_oauth.side_effect = create_mock_auth()  # noqa: ERA001
        mock_csw_client.side_effect = MockCSWClient

        app = create_app()
        app.config["SITE_PATH"] = Path(site_directory)
        return app


@pytest.fixture()
def app_static_site_auth_csw_not_setup() -> Flask:
    """Patched application to use fake CSW client and auth client that is not configured."""
    with (
        patch("scar_add_metadata_toolbox.classes.CSWClient") as mock_csw_client,
        TemporaryDirectory() as site_directory,
        # patch("scar_add_metadata_toolbox.FlaskAzureOauth") as mock_flask_azure_oauth,
    ):
        # mock_flask_azure_oauth.side_effect = create_mock_auth()  # noqa: ERA001
        mock_csw_client.side_effect = MockCSWClientServerNotSetup

        app = create_app()
        app.config["SITE_PATH"] = Path(site_directory)
        return app


@pytest.fixture()
def app_static_site_auth_csw_auth_token_error() -> Flask:
    """Patched application to use fake CSW client and auth client that has an auth token error."""
    with (
        patch("scar_add_metadata_toolbox.classes.CSWClient") as mock_csw_client,
        TemporaryDirectory() as site_directory,
        # patch("scar_add_metadata_toolbox.FlaskAzureOauth") as mock_flask_azure_oauth,
    ):
        # mock_flask_azure_oauth.side_effect = create_mock_auth()  # noqa: ERA001
        mock_csw_client.side_effect = MockCSWClientAuthError

        app = create_app()
        app.config["SITE_PATH"] = Path(site_directory)
        return app


@pytest.fixture()
def app_static_site_auth_csw_missing_auth_token() -> Flask:
    """Patched application to use fake CSW client and auth client that is missing an auth token."""
    with (
        patch("scar_add_metadata_toolbox.classes.CSWClient") as mock_csw_client,
        TemporaryDirectory() as site_directory,
        # patch("scar_add_metadata_toolbox.FlaskAzureOauth") as mock_flask_azure_oauth,
    ):
        # mock_flask_azure_oauth.side_effect = create_mock_auth()  # noqa: ERA001
        mock_csw_client.side_effect = MockCSWClientAuthMissing

        app = create_app()
        app.config["SITE_PATH"] = Path(site_directory)
        return app


@pytest.fixture()
def app_static_site_auth_csw_insufficient_auth_token() -> Flask:
    """Patched application to use fake CSW client and auth client that has an insufficient auth token."""
    with (
        patch("scar_add_metadata_toolbox.classes.CSWClient") as mock_csw_client,
        TemporaryDirectory() as site_directory,
        # patch("scar_add_metadata_toolbox.FlaskAzureOauth") as mock_flask_azure_oauth,
    ):
        # mock_flask_azure_oauth.side_effect = create_mock_auth()  # noqa: ERA001
        mock_csw_client.side_effect = MockCSWClientAuthInsufficient

        app = create_app()
        app.config["SITE_PATH"] = Path(site_directory)
        return app


AppAuthScopes = namedtuple("AppAuthScopes", ["app", "auth_scopes"])


@pytest.fixture()
def app_static_site_auth_get_scopes() -> AppAuthScopes:
    """Patched application auth scopes."""
    with (
        patch("scar_add_metadata_toolbox.classes.CSWClient") as mock_csw_client,
        TemporaryDirectory() as site_directory,
        # patch("scar_add_metadata_toolbox.FlaskAzureOauth") as mock_flask_azure_oauth,
    ):
        auth_scopes = []

        # mock_flask_azure_oauth.side_effect = create_mock_auth(auth_scopes)  # noqa: ERA001
        mock_csw_client.side_effect = MockCSWClient

        app = create_app()
        app.config["SITE_PATH"] = Path(site_directory)
        return AppAuthScopes(app, auth_scopes)
