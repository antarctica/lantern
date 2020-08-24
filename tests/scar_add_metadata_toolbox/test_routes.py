from http import HTTPStatus

import pytest


class TestRouteCSW:
    @pytest.mark.usefixtures("app_client_mocked_csw_server")
    def test_csw(self, app_client_mocked_csw_server):
        result = app_client_mocked_csw_server.get("/csw/published?service=CSW&request=GetCapabilities")
        assert result.status_code == HTTPStatus.OK

    @pytest.mark.usefixtures("app_client_mocked_csw_server")
    def test_csw_missing_catalogue(self, app_client_mocked_csw_server):
        result = app_client_mocked_csw_server.get("/csw")
        assert result.status_code == HTTPStatus.NOT_FOUND

    @pytest.mark.usefixtures("app_client_mocked_csw_server")
    def test_csw_unknown_catalogue(self, app_client_mocked_csw_server):
        result = app_client_mocked_csw_server.get("/csw/invalid?service=CSW&request=GetCapabilities")
        assert result.status_code == HTTPStatus.NOT_FOUND

    @pytest.mark.usefixtures("app_client_mocked_csw_server_not_setup")
    def test_csw_catalogue_not_ready(self, app_client_mocked_csw_server_not_setup):
        result = app_client_mocked_csw_server_not_setup.get("/csw/published?service=CSW&request=GetCapabilities")
        assert result.status_code == HTTPStatus.INTERNAL_SERVER_ERROR

    @pytest.mark.usefixtures("app_client_mocked_csw_server_missing_auth_token")
    def test_csw_missing_auth_token(self, app_client_mocked_csw_server_missing_auth_token):
        result = app_client_mocked_csw_server_missing_auth_token.get(
            "/csw/published?service=CSW&request=GetCapabilities"
        )
        assert result.status_code == HTTPStatus.UNAUTHORIZED

    @pytest.mark.usefixtures("app_client_mocked_csw_server_insufficient_auth_token")
    def test_csw_insufficient_auth_token(self, app_client_mocked_csw_server_insufficient_auth_token):
        result = app_client_mocked_csw_server_insufficient_auth_token.get(
            "/csw/published?service=CSW&request=GetCapabilities"
        )
        assert result.status_code == HTTPStatus.FORBIDDEN
