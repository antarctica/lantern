from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from flask import Flask
from flask.testing import FlaskClient, FlaskCliRunner
from flask_entra_auth.mocks.jwks import MockJwks
from flask_entra_auth.mocks.jwt import MockClaims, MockJwtClient
from pytest_httpserver import HTTPServer
from pytest_mock import MockerFixture

from scar_add_metadata_toolbox import create_app
from scar_add_metadata_toolbox.csw import CSWClient, CSWServer
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
)


@pytest.fixture()
def fx_user_claims() -> dict:
    """Token claims relating to the signed in user."""
    return {"name": "Connie Watson", "upn": "conwat@example.com"}


@pytest.fixture()
def fx_server_client_id() -> str:
    """Fake (Entra) client ID for app registration representing server side of app."""
    return "yyy"


@pytest.fixture()
def fx_claims(fx_server_client_id: str) -> MockClaims:
    """Fake claims."""
    return MockClaims(self_app_id=fx_server_client_id)


@pytest.fixture()
def fx_jwks() -> MockJwks:
    """Fake JWKS."""
    return MockJwks()


@pytest.fixture()
def fx_jwt_client(fx_jwks: MockJwks, fx_claims: MockClaims) -> MockJwtClient:
    """Client for generating fake JWTs."""
    return MockJwtClient(key=fx_jwks.jwk, claims=fx_claims)


@pytest.fixture()
def fx_msal_account() -> dict:
    """Subset of a fake MSAL account dict."""
    return {"local_account_id": "abc"}


@pytest.fixture()
def fx_access_token_no_roles(fx_jwt_client: MockJwtClient, fx_user_claims: dict) -> str:
    """Fake access token including user scopes."""
    return fx_jwt_client.generate(additional_claims=fx_user_claims)


@pytest.fixture()
def fx_access_token(fx_jwt_client: MockJwtClient, fx_user_claims: dict) -> str:
    """Fake access token including user scopes."""
    return fx_jwt_client.generate(roles=["BAS.MAGIC.ADD.Records.Publish.All"], additional_claims=fx_user_claims)


@pytest.fixture()
def app(mocker: MockerFixture) -> Flask:
    """Patched application to bypass auth."""
    mocker.patch(
        "scar_add_metadata_toolbox.client_auth.PublicClientApplication", return_value=mocker.MagicMock(auto_spec=True)
    )

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


def create_runner(
    request: pytest.FixtureRequest,
    return_runner: bool = False,
    return_client: bool = False,
    signed_in: bool = False,
    token_error: bool = False,
    csw_client: CSWClient | None = None,
    csw_server: CSWServer | None = None,
) -> Flask | FlaskClient | FlaskCliRunner:
    """
    Fixture generator.

    This method:
    - patches CSW auth to accept locally signed access tokens or simulate an error acquiring a token from Entra
    - patches the CSW Server class with a configurable mock (that either responds successfully or raises a exception)
    - patches the CSW Client class with a configurable mock (that either responds successfully or raises a exception)
    - updates app config to use a temporary directory for storing the MSAL / client auth cache
    - updates app config to use a temporary directory for the static site build output
    - can be configured to return a Flask app, a Flask test HTTP client or Flask test CLI runner as needed
    """
    # # Get fixture values
    #

    mocker: MockerFixture = request.getfixturevalue("mocker")
    access_token: str = request.getfixturevalue("fx_access_token")
    account_info: dict = request.getfixturevalue("fx_msal_account")
    httpserver: HTTPServer = request.getfixturevalue("httpserver")
    mock_jwks: MockJwks = request.getfixturevalue("fx_jwks")
    mock_claims: MockClaims = request.getfixturevalue("fx_claims")
    server_client_id: str = request.getfixturevalue("fx_server_client_id")

    # # Internal setup
    #

    get_accounts_initial_value = [account_info] if signed_in else []
    acquire_token_value = {"error": "-", "error_description": "..."} if token_error else {"access_token": access_token}

    # # Patch auth
    #

    mock_public_client_app = mocker.MagicMock(auto_spec=True)

    # noinspection PyUnusedLocal
    def sf_acquire_token_by_device_flow(flow_state: dict) -> None:
        mock_public_client_app.get_accounts.return_value = [account_info]

    # noinspection PyUnusedLocal
    def sf_remove_account(account: dict) -> None:
        mock_public_client_app.get_accounts.return_value = []

    mock_public_client_app.initiate_device_flow.return_value = {"user_code": "123"}
    mock_public_client_app.get_accounts.return_value = get_accounts_initial_value
    mock_public_client_app.acquire_token_silent.return_value = acquire_token_value
    mock_public_client_app.acquire_token_by_device_flow.side_effect = sf_acquire_token_by_device_flow
    mock_public_client_app.remove_account.side_effect = sf_remove_account
    mocker.patch("scar_add_metadata_toolbox.client_auth.PublicClientApplication", return_value=mock_public_client_app)

    # # Patch CSW Client
    #

    if csw_client is not None:
        mocker.patch("scar_add_metadata_toolbox.classes.CSWClient", side_effect=csw_client)

    # # Patch CSW Server

    if csw_server is not None:
        mocker.patch("scar_add_metadata_toolbox.utils.CSWServer", side_effect=csw_server)

    # # Create fake auth endpoints
    #

    oidc_metadata = {"jwks_uri": httpserver.url_for("/keys"), "issuer": mock_claims.iss}
    httpserver.expect_request("/.well-known/openid-configuration").respond_with_json(oidc_metadata)
    httpserver.expect_request("/keys").respond_with_json(mock_jwks.as_dict())

    # # Create app
    #

    app = create_app()

    # # Patch config
    #

    conf_dir = TemporaryDirectory()
    app.config["MSAL_AUTH_CACHE_PATH"] = Path(conf_dir.name).joinpath("/auth_cache.bin")

    site_dir = TemporaryDirectory()
    app.config["SITE_PATH"] = Path(site_dir.name)

    app.config["ENTRA_AUTH_CLIENT_ID"] = server_client_id
    app.config["ENTRA_AUTH_OIDC_ENDPOINT"] = httpserver.url_for("/.well-known/openid-configuration")

    # # Create runner
    #

    runner = app.test_cli_runner()

    # # Create client
    #

    client = app.test_client()

    # # Yield object
    #

    if return_runner:
        yield runner
    elif return_client:
        yield client
    else:
        yield app

    # # Tear down
    #

    conf_dir.cleanup()
    site_dir.cleanup()


@pytest.fixture()
def fx_runner_signed_out(request: pytest.FixtureRequest) -> FlaskCliRunner:
    """Application runner where a user is not signed in."""
    # noinspection PyTypeChecker
    return next(create_runner(request=request, return_runner=True))


@pytest.fixture()
def fx_runner_token_error_signed_out(request: pytest.FixtureRequest) -> FlaskCliRunner:
    """Application runner where a user is not signed in and can't get a token."""
    # noinspection PyTypeChecker
    return next(create_runner(request=request, return_runner=True, token_error=True))


@pytest.fixture()
def app_runner_mocked_csw(request: pytest.FixtureRequest) -> FlaskCliRunner:
    """App runner with mocked CSW client."""
    # noinspection PyTypeChecker
    return next(create_runner(request=request, return_runner=True, csw_client=MockCSWClient))


@pytest.fixture()
def app_runner_mocked_csw_inserts_fail(request: pytest.FixtureRequest) -> FlaskCliRunner:
    """App runner with mocked CSW client that fails to insert."""
    # noinspection PyTypeChecker
    return next(create_runner(request=request, return_runner=True, csw_client=MockCSWClientInsertsFail))


@pytest.fixture()
def app_runner_mocked_csw_not_setup(request: pytest.FixtureRequest) -> FlaskCliRunner:
    """App runner with mocked CSW client that is not setup."""
    # noinspection PyTypeChecker
    return next(create_runner(request=request, return_runner=True, csw_client=MockCSWClientServerNotSetup))


@pytest.fixture()
def app_runner_mocked_csw_auth_token_error(request: pytest.FixtureRequest) -> FlaskCliRunner:
    """App runner with mocked CSW client that has an auth token error."""
    # noinspection PyTypeChecker
    return next(create_runner(request=request, return_runner=True, csw_client=MockCSWClientAuthError))


@pytest.fixture()
def app_runner_mocked_csw_missing_auth_token(request: pytest.FixtureRequest) -> FlaskCliRunner:
    """App runner with mocked CSW client that is missing an auth token."""
    # noinspection PyTypeChecker
    return next(create_runner(request=request, return_runner=True, csw_client=MockCSWClientAuthMissing))


@pytest.fixture()
def app_runner_mocked_csw_insufficient_auth_token(request: pytest.FixtureRequest) -> FlaskCliRunner:
    """App runner with mocked CSW client that has an insufficient auth token."""
    # noinspection PyTypeChecker
    return next(create_runner(request=request, return_runner=True, csw_client=MockCSWClientAuthInsufficient))


@pytest.fixture()
def app_runner_mocked_csw_server(request: pytest.FixtureRequest) -> FlaskCliRunner:
    """App runner with mocked CSW server."""
    # noinspection PyTypeChecker
    return next(create_runner(request=request, return_runner=True, csw_server=MockCSWServer))


@pytest.fixture()
def app_runner_mocked_csw_server_tracking_not_enabled(request: pytest.FixtureRequest) -> FlaskCliRunner:
    """App runner with mocked CSW server that has revision tracking disabled."""
    # noinspection PyTypeChecker
    return next(create_runner(request=request, return_runner=True, csw_server=MockCSWServerRevisionTrackingDisabled))


@pytest.fixture()
def app_runner_mocked_csw_server_tracking_invalid_credentials(request: pytest.FixtureRequest) -> FlaskCliRunner:
    """App runner with mocked CSW server that has invalid credentials."""
    # noinspection PyTypeChecker
    return next(
        create_runner(request=request, return_runner=True, csw_server=MockCSWServerRevisionTrackingInvalidCredentials)
    )


@pytest.fixture()
def app_client_mocked_csw_server(request: pytest.FixtureRequest) -> FlaskClient:
    """App client with mocked CSW server."""
    # noinspection PyTypeChecker
    return next(create_runner(request=request, return_client=True, csw_server=MockCSWServer))


@pytest.fixture()
def app_client_mocked_csw_server_backing_db_not_setup(request: pytest.FixtureRequest) -> FlaskClient:
    """App client with mocked CSW server that has backing DB not setup."""
    # noinspection PyTypeChecker
    return next(create_runner(request=request, return_client=True, csw_server=MockCSWServerBackingDBNotSetup))


@pytest.fixture()
def app_client_mocked_csw_server_backing_repo_not_setup(request: pytest.FixtureRequest) -> FlaskClient:
    """App client with mocked CSW server that has backing repo not setup."""
    # noinspection PyTypeChecker
    return next(create_runner(request=request, return_client=True, csw_server=MockCSWServerBackingRepoNotSetup))


@pytest.fixture()
def app_client_mocked_csw_server_requests_fail(request: pytest.FixtureRequest) -> FlaskClient:
    """App client with mocked CSW server that fails requests."""
    # noinspection PyTypeChecker
    return next(create_runner(request=request, return_client=True, csw_server=MockCSWServerRequestsFail))


@pytest.fixture()
def app_client_mocked_csw_server_no_request_type(request: pytest.FixtureRequest) -> FlaskClient:
    """App client with mocked CSW server that has no request type."""
    # noinspection PyTypeChecker
    return next(create_runner(request=request, return_client=True, csw_server=MockCSWServerNoRequestType))


@pytest.fixture()
def app_client_mocked_csw_server_ambiguous_request(request: pytest.FixtureRequest) -> FlaskClient:
    """App client with mocked CSW server that has an ambiguous request."""
    # noinspection PyTypeChecker
    return next(create_runner(request=request, return_client=True, csw_server=MockCSWServerAmbiguousRequestError))


@pytest.fixture()
def app_client_mocked_csw_server_unmapped_request(request: pytest.FixtureRequest) -> FlaskClient:
    """App client with mocked CSW server that has an unmapped request."""
    # noinspection PyTypeChecker
    return next(create_runner(request=request, return_client=True, csw_server=MockCSWServerUnmappedRequestError))


@pytest.fixture()
def app_client_mocked_csw_server_auth_token_error(request: pytest.FixtureRequest) -> FlaskClient:
    """App client with mocked CSW server that has an auth token error."""
    # noinspection PyTypeChecker
    return next(create_runner(request=request, return_client=True, csw_server=MockCSWServerAuthTokenError))


@pytest.fixture()
def app_client_mocked_csw_server_missing_auth_token(request: pytest.FixtureRequest) -> FlaskClient:
    """App client with mocked CSW server that is missing an auth token."""
    # noinspection PyTypeChecker
    return next(create_runner(request=request, return_client=True, csw_server=MockCSWServerMissingAuthToken))


@pytest.fixture()
def app_client_mocked_csw_server_insufficient_auth_token(request: pytest.FixtureRequest) -> FlaskClient:
    """App client with mocked CSW server that has an insufficient auth token."""
    # noinspection PyTypeChecker
    return next(create_runner(request=request, return_client=True, csw_server=MockCSWServerInsufficientAuthToken))


@pytest.fixture()
def app_static_site(request: pytest.FixtureRequest) -> Flask:
    """Patched application to use fake CSW client and temp site directory."""
    # noinspection PyTypeChecker
    return next(create_runner(request=request, csw_client=MockCSWClient))


@pytest.fixture()
def app_static_site_auth_csw_not_setup(request: pytest.FixtureRequest) -> Flask:
    """Patched application to use fake CSW client and auth client that is not configured."""
    # noinspection PyTypeChecker
    return next(create_runner(request=request, csw_client=MockCSWClientServerNotSetup))
