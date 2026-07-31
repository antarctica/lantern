import base64
from http import HTTPStatus
from typing import TYPE_CHECKING

import pytest
import schemathesis
from schemathesis import Case
from schemathesis.checks import not_a_server_error
from schemathesis.core.errors import LoaderError
from tests.conftest import has_network

if TYPE_CHECKING:
    from schemathesis.hooks import HookContext

BASE_URL = "https://data.bas.ac.uk/static/json/openapi.json"
USES_CLOUDFRONT = True
USES_BAS_HAPROXY = True
USES_ODS = True

try:
    schema = schemathesis.openapi.from_url(url=BASE_URL)
except LoaderError:
    _schema = {
        "openapi": "3.1.1",
        "info": {"title": "Fallback API", "version": "1.0.0"},
        "paths": {"/": {"get": {"responses": {"200": {"description": "OK"}}}}},
    }
    schema = schemathesis.openapi.from_dict(schema=_schema)


@schemathesis.hook("before_call")
def before_call(context: HookContext, case: Case, kwargs: dict) -> None:
    """
    Configure requests.

    - adds basic auth for selected operations
    - disables following redirects, to allow expected redirects to be examined
    """
    # Add basic auth header where needed
    if hasattr(case.operation, "id") and case.operation.id == "getItemTrustedHtml":
        credentials = base64.b64encode(b"x:x").decode("ascii")
        kwargs.setdefault("headers", {})["Authorization"] = f"Basic {credentials}"

    # Disable following redirects for all operations
    # Allows expected redirects to be examined or fail with a status code mismatch
    kwargs["allow_redirects"] = False


@schema.parametrize()
@pytest.mark.xfail(reason="Experimental")
@pytest.mark.skipif(not has_network(), reason="network unavailable")
def test_openapi(case: Case):
    """
    Validate OpenAPI specification.

    Using Schemathesis - https://schemathesis.readthedocs.io/

    Always includes additional logic to:
    - validate operations that are expected to return a redirect

    Conditionally includes logic for CloudFront hosted servers to:
    - Skip validation for 405 responses (Allow header required by RFC 9110 not supported)
    - Non-read methods to give a 403 status not 405 (not supported by S3 origins)

    Conditionally includes logic for running under the BAS HAProxy load balancer to:
    - Amend the non-read methods logic to include 404, 405 or 501 as expected status codes

    Conditionally includes logic where the Ops Data Store web server is used to:
    - Expected unsupported methods to give a 200 or 401 status not 405 (not rejected by Apache)

    TODO: Split this into individual functions
    """
    expected_redirects = [
        "GET /-/health",
        "GET /collections/{aliasIdentifier}/index.html",
        "GET /datasets/{aliasIdentifier}/index.html",
        "GET /products/{aliasIdentifier}/index.html",
        "GET /projects/{aliasIdentifier}/index.html",
        "GET /maps/{aliasIdentifier}/index.html",
    ]

    ods_request: bool = USES_ODS and case.operation.label == "GET /-/items/{fileIdentifier}/index.html"
    case_method: str = case.method.upper()

    response = case.call()

    # Non-read methods in CloudFront may give 403 rather than 405 status from a S3 origin
    if USES_CLOUDFRONT and not ods_request and case_method not in ["HEAD", "GET", "OPTIONS", "TRACE"]:
        expected_statuses = [HTTPStatus.FORBIDDEN]
        if USES_BAS_HAPROXY:
            expected_statuses.extend([HTTPStatus.NOT_FOUND, HTTPStatus.METHOD_NOT_ALLOWED, HTTPStatus.NOT_IMPLEMENTED])
        assert response.status_code in expected_statuses
        return  # Stop validation

    # Expect ODS server to return non-405 status for non-supported methods
    if ods_request and case_method == "TRACE":
        assert response.status_code == HTTPStatus.OK
        return  # Stop validation
    if ods_request and case_method in ["QUERY", "POST", "PUT", "PATCH", "DELETE"]:
        assert response.status_code == HTTPStatus.UNAUTHORIZED
        return  # Stop validation

    # Validate expected redirects
    if case.operation.label in expected_redirects:
        if case.method.upper() not in ("GET", "HEAD"):
            return  # Stop validation (ignore unsupported methods)

        assert response.status_code in (HTTPStatus.MOVED_PERMANENTLY, HTTPStatus.NOT_FOUND)
        location = response.headers.get("Location", []) or response.headers.get("location", [])
        if response.status_code == HTTPStatus.MOVED_PERMANENTLY:
            assert len(location) > 0
        if response.status_code == HTTPStatus.NOT_FOUND:
            assert len(location) == 0
        return  # Stop validation

    # Skip full validation for 405 responses in CloudFront
    if USES_CLOUDFRONT and response.status_code == HTTPStatus.METHOD_NOT_ALLOWED:
        # Only check that it's not a server error
        case.validate_response(response, checks=(not_a_server_error,))
        return  # Stop validation

    # Fallback to Schemathesis
    case.validate_response(response)
