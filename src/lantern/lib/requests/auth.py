from typing import TYPE_CHECKING

from requests.auth import AuthBase

if TYPE_CHECKING:
    from requests import PreparedRequest


class HTTPBearerTokenAuth(AuthBase):
    """
    Attaches bearer token authentication to the given request object.

    Intended for services using OAuth.
    """

    def __init__(self, token: str) -> None:
        self._token = token

    def __call__(self, r: PreparedRequest) -> PreparedRequest:  # noqa: D102
        r.headers["Authorization"] = f"Bearer {self._token}"
        return r
