from http import HTTPStatus

import requests
from pytest_httpserver import HTTPServer, RequestMatcher
from werkzeug import Response

from lantern.lib.requests.auth import HTTPBearerTokenAuth


class TestPlainTextExtension:
    """Test bearer auth extension."""

    def test_request(self, httpserver: HTTPServer):
        """Can attach bearer token to a request."""
        _route = "/"
        _token = "x"  # noqa: S105
        _status = HTTPStatus.ACCEPTED
        httpserver.expect_request(_route).respond_with_response(Response(status=_status))

        requests.get(httpserver.url_for(_route), auth=HTTPBearerTokenAuth(_token), timeout=10)

        httpserver.assert_request_made(RequestMatcher(_route))
        for _request, response in httpserver.iter_matching_requests(RequestMatcher(_route)):
            assert _request.headers["Authorization"] == f"Bearer {_token}"
            assert response.status_code == _status
