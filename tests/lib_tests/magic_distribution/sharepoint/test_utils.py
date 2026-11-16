from __future__ import annotations

from http import HTTPStatus

import pytest
import requests
from bas_metadata_library.standards.magic_administration.v1 import AdministrationMetadata, Permission
from pytest_httpserver import HTTPServer, RequestMatcher
from werkzeug import Response

from lantern.lib.magic_distribution.sharepoint.models.types import SharePointPermissions
from lantern.lib.magic_distribution.sharepoint.utils import HTTPBearerTokenAuth, get_sharepoint_permissions
from lantern.lib.metadata_library.models.record.presets.admin import OPEN_ACCESS


class TestHTTPBearerTokenAuth:
    """Test OAuth bearer token auth extension."""

    def test_request(self, httpserver: HTTPServer):
        """Can attach bearer token to a request."""
        _route = "/"
        _token = "x"  # noqa: S105
        _status = HTTPStatus.ACCEPTED
        httpserver.expect_request(_route).respond_with_response(Response(status=_status))

        requests.get(httpserver.url_for(_route), auth=HTTPBearerTokenAuth(_token), timeout=10)

        httpserver.assert_request_made(RequestMatcher(_route))
        for request, response in httpserver.iter_matching_requests(RequestMatcher(_route)):
            assert request.headers["Authorization"] == f"Bearer {_token}"
            assert response.status_code == _status


class TestSharePointPermissions:
    """Test resolving real groups identifiers from administration metadata access permissions for use in SharePoint."""

    @pytest.mark.parametrize(
        ("permissions", "mapping", "expected"),
        [
            # none
            ([], {}, SharePointPermissions(group_ids=set(), unrestricted=False)),
            # unrestricted
            ([OPEN_ACCESS], {}, SharePointPermissions(group_ids=set(), unrestricted=True)),
            # unrestricted but not exclusive
            (
                [OPEN_ACCESS, Permission(directory="x", group="x")],
                {},
                SharePointPermissions(group_ids=set(), unrestricted=False),
            ),
            # match
            (
                [Permission(directory="~nerc", group="~foo")],
                {"~foo": ["x", "y"]},
                SharePointPermissions(group_ids={"x", "y"}, unrestricted=False),
            ),
            # deduplicated
            (
                [Permission(directory="~nerc", group="~foo"), Permission(directory="~nerc", group="~bar")],
                {"~foo": ["x"], "~bar": ["x"]},
                SharePointPermissions(group_ids={"x"}, unrestricted=False),
            ),
            # filter out out-of-scope directories
            (
                [Permission(directory="~nerc", group="~foo"), Permission(directory="~x", group="~baz")],
                {"~foo": ["x"], "~baz": ["y"]},
                SharePointPermissions(group_ids={"x"}, unrestricted=False),
            ),
        ],
    )
    def test_resolve(self, permissions: list[Permission], mapping: dict, expected: SharePointPermissions):
        """Can resolve groups from admin metadata."""
        admin_meta = AdministrationMetadata(id="x", resource_permissions=permissions)
        result = get_sharepoint_permissions(admin_meta=admin_meta, groups_mapping=mapping)
        assert result == expected

    @pytest.mark.cov()
    def test_no_admin(self):
        """Can handle missing administration metadata."""
        result = get_sharepoint_permissions(admin_meta=None, groups_mapping={})
        assert result == SharePointPermissions(group_ids=set(), unrestricted=False)
