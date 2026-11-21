import json
from http import HTTPStatus
from urllib.parse import parse_qs

import pytest
import requests
from pytest_httpserver import HTTPServer, RequestMatcher
from werkzeug import Response

from lantern.lib.magic_distribution.arcgis.gis.enums import SharingLevel
from lantern.lib.magic_distribution.arcgis.utils import (
    ArcGISAuthError,
    ArcGISRequestError,
    HTTPArcGISTokenAuth,
    check_arcgis_error,
    ensure_query_param,
    normalise_arcgis_html,
    sharing_level_parameters,
    snake_to_camel_case,
)


class TestUtils:
    """Test util methods."""

    @pytest.mark.parametrize(
        ("url", "name", "value", "expected"),
        [
            ("https://example.com", "x", "x", "https://example.com?x=x"),
            ("https://example.com?x=x", "x", "x", "https://example.com?x=x"),
            ("https://example.com?y=y", "x", "x", "https://example.com?y=y&x=x"),
        ],
    )
    def test_ensure_query_param(self, url: str, name: str, value: str, expected: str):
        """Can ensure a query parameter is present in a URL."""
        assert ensure_query_param(url=url, name=name, value=value) == expected

    @pytest.mark.parametrize(("value", "expected"), [("x_x", "xX"), ("x", "x"), ("", "")])
    def test_snake_to_camel_case(self, value: str, expected: str):
        """Can convert snake_case strings to camelCase."""
        assert snake_to_camel_case(value) == expected

    @pytest.mark.parametrize(
        ("html", "expected"),
        [
            (
                '<a href="https://example.com">Link</a>',
                '<div><a href="https://example.com" rel="nofollow ugc">Link</a></div>',
            ),
            (
                '<div><p><a href="https://example.com" rel="ugc custom">Link</a></p></div>',
                '<div><p><a href="https://example.com" rel="custom nofollow ugc">Link</a></p></div>',
            ),
            ("<div><p>Text</p></div>", "<div><p>Text</p></div>"),
        ],
    )
    def test_normalise_arcgis_html(self, html: str, expected: str):
        """Can normalise anchor attributes and extra div wrappers."""
        assert normalise_arcgis_html(html) == expected

    @pytest.mark.parametrize(
        ("sharing_level", "expected"),
        [
            (SharingLevel.PRIVATE, {"everyone": (None, False), "org": (None, False)}),
            (SharingLevel.SHARED, {"everyone": (None, False), "org": (None, False)}),
            (SharingLevel.ORG, {"everyone": (None, False), "org": (None, True)}),
            (SharingLevel.EVERYONE, {"everyone": (None, True), "org": (None, True)}),
        ],
    )
    def test_sharing_level_parameters(self, sharing_level: SharingLevel, expected: dict[str, tuple]):
        """Can determine the sharing API parameters for each sharing level."""
        assert sharing_level_parameters(sharing_level) == expected

    @pytest.mark.parametrize(
        ("body", "expected"),
        [
            ("", None),
            ("x", None),
            (json.dumps({"x": "x"}), None),
            (
                json.dumps({"error": {"code": 0}}),
                ArcGISRequestError,
            ),
            (
                json.dumps(
                    {
                        "error": {
                            "code": 499,
                            "message": "Token Required",
                            "messageCode": "GWM_0003",
                            "details": ["Token Required"],
                        }
                    }
                ),
                ArcGISAuthError,
            ),
        ],
    )
    def test_check_arcgis_error(self, httpserver: HTTPServer, body: str, expected: Exception | None):
        """Can determine if a response body contains an ArcGIS API error."""
        _route = "/endpoint"
        httpserver.expect_request(_route).respond_with_response(Response(response=body, status=HTTPStatus.OK))

        result = requests.get(httpserver.url_for(_route), timeout=10)

        if not expected:
            check_arcgis_error(result)
            return
        with pytest.raises(expected):
            check_arcgis_error(result)


class TestHTTPArcGISTokenAuth:
    """Test ArcGIS bearer auth extension."""

    def test_request(self, httpserver: HTTPServer):
        """Can attach bearer token to a request."""
        _route = "/"
        _token = "x"  # noqa: S105
        _status = HTTPStatus.ACCEPTED
        httpserver.expect_request(_route).respond_with_response(Response(status=_status))

        requests.get(httpserver.url_for(_route), auth=HTTPArcGISTokenAuth(_token), timeout=10)

        httpserver.assert_request_made(RequestMatcher(_route))
        for request, response in httpserver.iter_matching_requests(RequestMatcher(_route)):
            # query string parameters may be repeated so select the first instance of a token parameter
            assert parse_qs(request.query_string.decode(), keep_blank_values=True)["token"][0] == _token
            assert response.status_code == _status
