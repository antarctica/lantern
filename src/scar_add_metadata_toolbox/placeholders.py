class PlaceholderAzureToken:
    """Needed whilst the `flask_azure_oauth` package is unavailable."""

    def __init__(self) -> None:
        self._claims = {"given_name": "unknown", "family_name": "unknown", "email": "unknown@example.com"}
        self._scopes: set = {"openid", "profile", "email"}

    @property
    def claims(self) -> dict:
        """Fake claims."""
        return self._claims

    @property
    def scopes(self) -> set:
        """Fake scopes."""
        return self._scopes
