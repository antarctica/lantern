from __future__ import annotations

from json import JSONDecodeError
from typing import TYPE_CHECKING
from urllib.parse import parse_qs, urlencode, urlsplit, urlunsplit

from lxml.html import HTMLParser
from lxml.html import fragment_fromstring as html_fromstring
from lxml.html import tostring as html_tostring
from requests.auth import AuthBase

from lantern.lib.magic_distribution.arcgis.gis.enums import SharingLevel

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


def snake_to_camel_case(s: str) -> str:
    """Convert from snake_case to camelCase."""
    parts = s.split("_")
    return parts[0] + "".join(p.capitalize() for p in parts[1:])


def normalise_arcgis_html(html: str) -> str:
    """
    Normalise HTML string between a Lantern catalogue record and an ArcGIS item.

    Converts between HTML generated:
    - from Markdown in the catalogue item
    - after having been submitted and processed by Arc

    Accounts for:
    - differences in syntax (`<a href='x'>` vs `<a href="x">`)
    - `rel="nofollow ugc"` being added to anchor elements
    - possible extra div wrapper
    """
    element = html_fromstring(html, create_parent=True, parser=HTMLParser())
    # add `rel="nofollow ugc"` to any anchor elements
    for a in element.iter("a"):
        relations = {t for t in a.get("rel", "").split() if t}
        relations.update({"nofollow", "ugc"})
        a.set("rel", " ".join(sorted(relations)))
    # correct double wrapping div
    if element.tag == "div" and len(element) == 1 and element[0].tag == "div":
        element = element[0]
    return html_tostring(doc=element, encoding="unicode")


def sharing_level_parameters(sharing_level: SharingLevel) -> dict[str, tuple]:
    """Determine ArcGIS sharing API parameters based on sharing level."""
    sharing = {"everyone": False, "org": False}
    if sharing_level == SharingLevel.ORG:
        sharing["org"] = True
    elif sharing_level == SharingLevel.EVERYONE:
        sharing["everyone"] = True
        sharing["org"] = True
    return {k: (None, v) for k, v in sharing.items()}
