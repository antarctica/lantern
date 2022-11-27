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
    @pytest.mark.usefixtures("app_client_mocked_csw_server_no_request_type")
    def test_csw_catalogue_no_request_type(self, app_client_mocked_csw_server_no_request_type):
        result = app_client_mocked_csw_server_no_request_type.get("/csw/published?service=CSW")
        assert result.status_code == HTTPStatus.BAD_REQUEST
        assert result.text == "Request/operation information missing."

    @pytest.mark.usefixtures("app_client_mocked_csw_server_ambiguous_request")
    def test_csw_catalogue_ambiguous_request_type(self, app_client_mocked_csw_server_ambiguous_request):
        body = """<csw:DescribeRecord 
            service="CSW" 
            version="2.0.2" 
            outputFormat="application/xml" 
            schemaLanguage="http://www.w3.org/XML/Schema" 
            xmlns="http://www.opengis.net/cat/csw/2.0.2" 
            xmlns:csw30="http://www.opengis.net/cat/csw/3.0" 
            xmlns:csw="http://www.opengis.net/cat/csw/2.0.2" 
            xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
            xsi:schemaLocation="http://www.opengis.net/cat/csw/3.0 
            http://schemas.opengis.net/cat/csw/3.0/cswGetCapabilities.xsd"
        >
            <csw:TypeName>csw:Record</csw:TypeName>
        </csw:DescribeRecord>"""
        result = app_client_mocked_csw_server_ambiguous_request.post(
            "/csw/published?service=CSW&request=GetCapabilities", data=body, headers={"content-type": "text/xml"}
        )
        assert result.status_code == HTTPStatus.BAD_REQUEST
        assert result.text == "Request/operation information specified in multiple forms."

    @pytest.mark.usefixtures("app_client_mocked_csw_server_unmapped_request")
    def test_csw_catalogue_unmapped_request_type(self, app_client_mocked_csw_server_unmapped_request):
        result = app_client_mocked_csw_server_unmapped_request.get("/csw/published?service=CSW&request=unmapped")
        assert result.status_code == HTTPStatus.BAD_REQUEST
        assert result.text == "Request/operation cannot be evaluated / not supported."

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
