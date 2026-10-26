import json
from http import HTTPStatus
from urllib.parse import parse_qs

import pytest
import requests
from pytest_httpserver import HTTPServer, RequestMatcher
from werkzeug import Response

from lantern.lib.arcgis.utils import (
    ArcGISAuthError,
    ArcGISRequestError,
    HTTPArcGISTokenAuth,
    check_arcgis_error,
    ensure_query_param,
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
