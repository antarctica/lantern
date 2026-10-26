from __future__ import annotations

from json import JSONDecodeError
from typing import TYPE_CHECKING
from urllib.parse import parse_qs, urlencode, urlsplit, urlunsplit

from requests.auth import AuthBase

if TYPE_CHECKING:
    import requests
    from requests import PreparedRequest


def ensure_query_param(url: str, name: str, value: str) -> str:
    """Ensure a URL contains a given query parameter."""
    parts = urlsplit(url)
    query = parse_qs(parts.query, keep_blank_values=True)
    if name not in query:
        query[name] = [value]
        return urlunsplit(parts._replace(query=urlencode(query, doseq=True)))
    return url


class HTTPArcGISTokenAuth(AuthBase):
    """
    ArcGIS bearer token for Requests auth.

    Attaches an ArcGIS bearer token authentication as a query parameter to a Requests object.
    """

    def __init__(self, token: str) -> None:
        self._token = token

    def __call__(self, r: PreparedRequest) -> PreparedRequest:  # noqa: D102
        url = r.url if isinstance(r.url, str) else ""
        r.url = ensure_query_param(url, "token", self._token)
        return r


class ArcGISRequestError(Exception):
    """Represents any application error returned by an ArcGIS endpoint."""


class ArcGISAuthError(Exception):
    """Represents an authentication related application error returned by an ArcGIS endpoint."""


def check_arcgis_error(response: requests.Response) -> None:
    """
    Check if a Requests response contains an ArcGIS service error.

    ArcGIS returns application level errors in 200 responses. Therefore, the typical
    `requests.exceptions.RequestException` is not raised, and standard error handling (`raise_for_status()`) will not
    work.

    Raises errors related to lack of authentication (498, 499) as a specific exception.
    """
    try:
        data = response.json()
    except JSONDecodeError:
        return
    if "error" not in data or "code" not in data["error"]:
        return
    if int(data["error"]["code"]) in {403, 499}:
        # authentication errors
        raise ArcGISAuthError() from None
    msg = data["error"].get("message", "Unknown ArcGIS error")
    raise ArcGISRequestError(msg) from None
