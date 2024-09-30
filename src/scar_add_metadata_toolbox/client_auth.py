from __future__ import annotations

from pathlib import Path
from typing import TypedDict

from flask import Flask
from jwt import decode as jwt_decode
from msal import PublicClientApplication
from msal_extensions import FilePersistence, PersistedTokenCache


class MsalFlaskError(Exception):
    """Base class for MSAL Flask errors."""

    pass


class MsalFlaskNoAccountError(MsalFlaskError):
    """Raised when no account is found in MSAL token cache (typically because a user hasn't signed in yet)."""

    pass


class MsalTokenAcquisitionError(MsalFlaskError):
    """Raised when MSAL cannot acquire a token automatically."""

    def __init__(self, error: str | None = None, description: str | None = None) -> None:
        self.error = error
        self.description = description

        super().__init__(f"Error acquiring token: {error} - {description}")


class MsalTokenCacheRenewalError(MsalFlaskError):
    """Raised when MSAL token cache cannot provide a token (typically because the refresh token has expired)."""

    pass


class MsalFlaskAuth:
    """
    Thin abstraction over MSAL.

    Intended for public (non-trusted) CLI apps where the token cache is stored in a single end-users account.
    """

    def __init__(self, tenancy_id: str, client_id: str, scopes: list[str], auth_cache_path: Path) -> None:
        self._tenancy_id = tenancy_id
        self._client_id = client_id
        self._authority = f"https://login.microsoftonline.com/{self._tenancy_id}"
        self._scopes = scopes
        self._auth_cache_path = auth_cache_path
        self._flow_state = {}

        self._client = self._make_client_app()

    def _make_auth_cache(self) -> PersistedTokenCache:
        """
        Create serialised token cache for MSAL client.

        Would ideally be encrypted but can't because MSAL's Linux support requires a desktop environment.
        See https://github.com/AzureAD/microsoft-authentication-extensions-for-python/wiki/Encryption-on-Linux.
        """
        return PersistedTokenCache(persistence=FilePersistence(location=str(self._auth_cache_path)))

    def _make_client_app(self) -> PublicClientApplication:
        """
        Create MSAL client.

        Public client because app runs on a device controlled by the end-user.
        """
        return PublicClientApplication(
            client_id=self._client_id, authority=self._authority, token_cache=self._make_auth_cache()
        )

    @property
    def _account(self) -> dict:
        """Get the MSAL account for the signed in user from the cache."""
        try:
            return self._client.get_accounts()[0]
        except IndexError as e:
            raise MsalFlaskNoAccountError() from e

    @property
    def access_token(self) -> str:
        """Get or refresh the current access token for the signed in user."""
        result = {}
        try:
            result = self._client.acquire_token_silent(scopes=self._scopes, account=self._account)
            return result["access_token"]
        except TypeError as e:
            raise MsalTokenCacheRenewalError() from e
        except KeyError as e:
            error = result.get("error", "-")
            description = result.get("error_description", "-")
            raise MsalTokenAcquisitionError(error=error, description=description) from e

    @property
    def _access_token_claims_unverified(self) -> dict:
        """
        Decode the current access token without verifying signature.

        Warning: These claims are unverified and MUST NOT be used in a trusted context.
        """
        return jwt_decode(self.access_token, options={"verify_signature": False})

    class AccountInfo(TypedDict):
        """Types for `account_info`."""

        name: str
        email: str
        account_id: str

    @property
    def account_info(self) -> AccountInfo:
        """Human and machine oriented account identifiers for current user."""
        access_claims = self._access_token_claims_unverified
        account = self._account

        return {
            "name": access_claims.get("name", "-"),
            "email": access_claims.get("email", "-"),
            "account_id": account.get("local_account_id", "-"),
        }

    @property
    def whoami(self) -> str:
        """Formatted string of current user's account info."""
        account_info = self.account_info
        return (
            f"Signed in as '{account_info['name']}' ({account_info['email']}) [{account_info['account_id']}] "
            f"using cached credentials."
        )

    class DeviceFlowState(TypedDict):
        """Types for `start_device_flow`."""

        user_code: str
        endpoint: str

    def start_device_flow(self) -> DeviceFlowState:
        """Initiate device sign in flow."""
        self._flow_state = self._client.initiate_device_flow(scopes=self._scopes)

        return {
            "user_code": self._flow_state["user_code"],
            "endpoint": "https://microsoft.com/devicelogin",
        }

    def finish_device_flow(self) -> None:
        """Complete device sign in flow."""
        self._client.acquire_token_by_device_flow(self._flow_state)

    def sign_out(self) -> None:
        """Clear signed in user from cache."""
        self._client.remove_account(self._account)


class MsalFlask:
    """Flask extension for acquiring auth tokens using MSAL."""

    def __init__(self, app: Flask | None = None) -> None:
        """Conventional extension init method."""
        if app is not None:  # pragma: no branch
            self.init_app(app)  # pragma: no cover

    @staticmethod
    def init_app(app: Flask) -> None:
        """Initialise extension for an application."""
        with app.app_context():
            app.msal = MsalFlaskAuth(
                tenancy_id=app.config["MSAL_TENANCY"],
                client_id=app.config["MSAL_CLIENT_ID"],
                scopes=app.config["MSAL_SCOPES"],
                auth_cache_path=app.config["MSAL_AUTH_CACHE_PATH"],
            )
