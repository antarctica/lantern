from http import HTTPStatus
from pathlib import Path

import pytest
from flask.testing import FlaskClient

from tests.scar_add_metadata_toolbox_tests.records import TestRecordConfigurations


@pytest.mark.usefixtures("app_client")
def test_404(app_client: FlaskClient):
    response = app_client.get("/404")
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.text == "Not Found."


@pytest.mark.usefixtures("app_client")
def test_health(app_client: FlaskClient):
    expected_response = {
        "description": "Server side endpoints for the SCAR Antarctic Digital Database " "(ADD) Metadata Toolbox.",
        "links": {
            "about": "https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox",
            "describedBy": "https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/blob/vN/A/README.md",
            "self": "http://localhost/meta/health/v1",
        },
        "releaseId": "N/A",
        "status": "pass",
        "version": 1,
    }
    response = app_client.get("/meta/health/v1")
    assert response.status_code == HTTPStatus.OK
    assert response.mimetype == "application/json"
    assert response.json == expected_response


class TestRouteCSW:
    @pytest.mark.usefixtures("app_client_mocked_csw_server")
    def test_csw(self, app_client_mocked_csw_server):
        result = app_client_mocked_csw_server.get("/csw/published?service=CSW&request=GetCapabilities")
        assert result.status_code == HTTPStatus.OK

    @pytest.mark.usefixtures("app_client_mocked_csw_server")
    def test_csw_unknown_catalogue(self, app_client_mocked_csw_server):
        result = app_client_mocked_csw_server.get("/csw/invalid?service=CSW&request=GetCapabilities")
        assert result.status_code == HTTPStatus.NOT_FOUND
        assert result.text == "Catalogue not found."

    @pytest.mark.usefixtures("app_client_mocked_csw_server_backing_db_not_setup")
    def test_csw_catalogue_not_ready_backing_db(self, app_client_mocked_csw_server_backing_db_not_setup):
        result = app_client_mocked_csw_server_backing_db_not_setup.get(
            "/csw/published?service=CSW&request=GetCapabilities"
        )
        assert result.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
        assert result.text == "Catalogue DB not yet available."

    @pytest.mark.usefixtures("app_client_mocked_csw_server_backing_repo_not_setup")
    def test_csw_catalogue_not_ready_backing_repo(self, app_client_mocked_csw_server_backing_repo_not_setup):
        result = app_client_mocked_csw_server_backing_repo_not_setup.get(
            "/csw/unpublished?service=CSW&request=GetCapabilities"
        )
        assert result.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
        assert result.text == "Catalogue Repo not yet available."

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
        assert result.text == "Missing authorisation token."

    @pytest.mark.usefixtures("app_client_mocked_csw_server_insufficient_auth_token")
    def test_csw_insufficient_auth_token(self, app_client_mocked_csw_server_insufficient_auth_token):
        result = app_client_mocked_csw_server_insufficient_auth_token.get(
            "/csw/published?service=CSW&request=GetCapabilities"
        )
        assert result.status_code == HTTPStatus.FORBIDDEN
        assert result.text == "Insufficient authorisation token."


class TestRouteSiteBuild:
    @pytest.mark.usefixtures("app_static_site_auth")
    def test_site_build(self, app_static_site_auth):
        result = app_static_site_auth.test_client().post(
            f"/site/build?item={TestRecordConfigurations.TEST_RECORD_1.value['file_identifier']}"
        )
        assert result.status_code == HTTPStatus.CREATED

        # Verify file structure
        record_pages_paths = list(Path(app_static_site_auth.config["SITE_PATH"]).glob("**/*.*"))
        item_pages_paths = list(Path(app_static_site_auth.config["SITE_PATH"]).glob("**/*.*"))
        assert len(record_pages_paths) == 4
        assert (
            Path(app_static_site_auth.config["SITE_PATH"]).joinpath(
                f"records/{TestRecordConfigurations.TEST_RECORD_1.value['file_identifier']}/iso-html/"
                f"{TestRecordConfigurations.TEST_RECORD_1.value['file_identifier']}.xml"
            )
            in record_pages_paths
        )
        assert (
            Path(app_static_site_auth.config["SITE_PATH"]).joinpath(
                f"records/{TestRecordConfigurations.TEST_RECORD_1.value['file_identifier']}/iso-rubric/"
                f"{TestRecordConfigurations.TEST_RECORD_1.value['file_identifier']}.xml"
            )
            in record_pages_paths
        )
        assert (
            Path(app_static_site_auth.config["SITE_PATH"]).joinpath(
                f"records/{TestRecordConfigurations.TEST_RECORD_1.value['file_identifier']}/iso-xml/"
                f"{TestRecordConfigurations.TEST_RECORD_1.value['file_identifier']}.xml"
            )
            in record_pages_paths
        )
        assert (
            Path(app_static_site_auth.config["SITE_PATH"]).joinpath(
                f"items/{TestRecordConfigurations.TEST_RECORD_1.value['file_identifier']}/index.html"
            )
            in item_pages_paths
        )

    @pytest.mark.usefixtures("app_static_site_auth")
    def test_site_build_missing_record(self, app_static_site_auth):
        result = app_static_site_auth.test_client().post("/site/build?item=does-not-exist")
        assert result.status_code == HTTPStatus.NOT_FOUND
        assert result.text == "Record not found."

    @pytest.mark.usefixtures("app_static_site_auth")
    def test_site_build_missing_item_parameter(self, app_static_site_auth):
        result = app_static_site_auth.test_client().post("/site/build")
        assert result.status_code == HTTPStatus.BAD_REQUEST
        assert result.text == "Parameter 'item' missing."

    @pytest.mark.usefixtures("app_static_site_auth_get_scopes")
    def test_site_build_auth_scopes(self, app_static_site_auth_get_scopes):
        app_static_site_auth_get_scopes.app.test_client().post(
            f"/site/build?item={TestRecordConfigurations.TEST_RECORD_1.value['file_identifier']}"
        )
        assert len(app_static_site_auth_get_scopes.auth_scopes) == 1
        assert app_static_site_auth_get_scopes.auth_scopes[0] == ["BAS.MAGIC.ADD.Records.Publish.All"]

    @pytest.mark.usefixtures("app_static_site_auth_csw_not_setup")
    def test_site_build_csw_not_setup(self, app_static_site_auth_csw_not_setup):
        result = app_static_site_auth_csw_not_setup.test_client().post(
            f"/site/build?item={TestRecordConfigurations.TEST_RECORD_1.value['file_identifier']}"
        )
        assert result.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
        assert result.text == "Internal server error."

    @pytest.mark.usefixtures("app_static_site_auth_csw_auth_token_error")
    def test_site_build_csw_auth_token_error(self, app_static_site_auth_csw_auth_token_error):
        result = app_static_site_auth_csw_auth_token_error.test_client().post(
            f"/site/build?item={TestRecordConfigurations.TEST_RECORD_1.value['file_identifier']}"
        )
        assert result.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
        assert result.text == "Internal server error."

    @pytest.mark.usefixtures("app_static_site_auth_csw_missing_auth_token")
    def test_site_build_csw_missing_auth_token(self, app_static_site_auth_csw_missing_auth_token):
        result = app_static_site_auth_csw_missing_auth_token.test_client().post(
            f"/site/build?item={TestRecordConfigurations.TEST_RECORD_1.value['file_identifier']}"
        )
        assert result.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
        assert result.text == "Internal server error."

    @pytest.mark.usefixtures("app_static_site_auth_csw_insufficient_auth_token")
    def test_site_build_csw_insufficient_auth_token(self, app_static_site_auth_csw_insufficient_auth_token):
        result = app_static_site_auth_csw_insufficient_auth_token.test_client().post(
            f"/site/build?item={TestRecordConfigurations.TEST_RECORD_1.value['file_identifier']}"
        )
        assert result.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
        assert result.text == "Internal server error."
