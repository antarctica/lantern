from enum import Enum
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import pytest

from scar_add_metadata_toolbox import create_app
from scar_add_metadata_toolbox.classes import (
    CSWClient,
    RecordSummary,
    Record,
    MirrorRecordSummary,
    MirrorRecord,
    Item,
    Collection,
)

from tests.scar_add_metadata_toolbox.classes import (
    MockCSWClient,
    MockCollections,
    MockCSWClientInsertsFail,
    MockCSWServer,
    MockCSWServerNotSetup,
    MockCSWServerRequestsFail,
    MockCSWServerMissingAuthToken,
    MockCSWServerInsufficientAuthToken,
    MockPublicClientApplication,
    MockCSWClientServerNotSetup,
    MockCSWClientAuthError,
    MockCSWClientAuthMissing,
    MockCSWClientAuthInsufficient,
    MockCollectionsUnknownRecord,
    MockCSWServerAuthTokenError,
)
from tests.scar_add_metadata_toolbox.resources.csw.records import make_test_record


class TestRecords(Enum):
    __test__ = False

    TEST_RECORD_1 = make_test_record(
        identifier="7e3719b4-60a4-4b4e-aa84-cee7a5e7218f", title="Test Record 1 (Published)"
    )
    TEST_RECORD_2 = make_test_record(
        identifier="39d47e50-f94f-43c5-9060-510d9374b81b", title="Test Record 2 (Unpublished)"
    )
    TEST_RECORD_3 = make_test_record(
        identifier="180d07c4-8b97-48ed-87ac-359b6899fa8b", title="Test Record 3 (Imported, Unpublished)"
    )
    TEST_RECORD_4 = make_test_record(
        identifier="7e3719b4-60a4-4b4e-aa84-cee7a5e7218f", title="Test Record 4 (Imported, Updated, Unpublished)"
    )
    TEST_RECORD_5 = make_test_record(
        identifier="2f8ad5b8-b861-4459-88d9-b9ff98a34a98", title="Test Record 5 (Imported, Published)"
    )
    TEST_RECORD_6 = make_test_record(
        identifier="7e3719b4-60a4-4b4e-aa84-cee7a5e7218f",
        title="Test Record 6 (Imported, Updated, Published, Republished)",
    )
    TEST_RECORD_7 = make_test_record(
        identifier="7e3719b4-60a4-4b4e-aa84-cee7a5e7218f", title="Test Record 7 (Imported, Duplicate of Test Record 1)"
    )


class TestCollections(Enum):
    __test__ = False

    TEST_COLLECTION_1 = {
        "identifier": "b759077f-bd3f-4a18-bbd7-e6b3f84bc551",
        "title": "Test Collection 1",
        "topics": ["Topographic Mapping"],
        "publishers": ["Mapping and Geographic Information Centre (MAGIC)"],
        "summary": "Description for Test Collection 1.",
        "item_identifiers": ["7e3719b4-60a4-4b4e-aa84-cee7a5e7218f"],
    }
    TEST_COLLECTION_2 = {
        "identifier": "6062c26f-0165-4109-a2d9-29cf884f079d",
        "title": "Test Collection 2 (Imported)",
        "topics": ["Topographic Mapping"],
        "publishers": ["Mapping and Geographic Information Centre (MAGIC)"],
        "summary": "Description for Test Collection 2.",
        "item_identifiers": ["7e3719b4-60a4-4b4e-aa84-cee7a5e7218f"],
    }
    TEST_COLLECTION_3 = {
        "identifier": "b759077f-bd3f-4a18-bbd7-e6b3f84bc551",
        "title": "Test Collection 3 (Imported, Updated, Duplicate of Test Collection 1)",
        "topics": ["Topographic Mapping"],
        "publishers": ["Mapping and Geographic Information Centre (MAGIC)"],
        "summary": "Description for Test Collection 3.",
        "item_identifiers": ["7e3719b4-60a4-4b4e-aa84-cee7a5e7218f"],
    }
    TEST_COLLECTION_4 = {
        "identifier": "0d1b9063-da63-403d-ba16-f72e5f6f5688",
        "title": "Test Collection 4 (Imported, contains unknown item identifier)",
        "topics": ["Topographic Mapping"],
        "publishers": ["Mapping and Geographic Information Centre (MAGIC)"],
        "summary": "Description for Test Collection 4.",
        "item_identifiers": ["unknown"],
    }


@pytest.fixture
def app():
    with patch("scar_add_metadata_toolbox.config.PublicClientApplication") as mock_msal_client_application:
        mock_msal_client_application.side_effect = MockPublicClientApplication
        app = create_app()
        return app


@pytest.fixture
@pytest.mark.usefixtures("app")
def app_runner(app):
    return app.test_cli_runner()


@pytest.fixture
def app_runner_mocked_csw():
    with patch("scar_add_metadata_toolbox.classes.CSWClient") as mock_csw_client:
        mock_csw_client.side_effect = MockCSWClient
        app = create_app()
        return app.test_cli_runner()


@pytest.fixture
def app_runner_mocked_csw_inserts_fail():
    with patch("scar_add_metadata_toolbox.classes.CSWClient") as mock_csw_client:
        mock_csw_client.side_effect = MockCSWClientInsertsFail
        app = create_app()
        return app.test_cli_runner()


@pytest.fixture
def app_runner_mocked_csw_not_setup():
    with patch("scar_add_metadata_toolbox.classes.CSWClient") as mock_csw_client:
        mock_csw_client.side_effect = MockCSWClientServerNotSetup
        app = create_app()
        return app.test_cli_runner()


@pytest.fixture
def app_runner_mocked_csw_auth_token_error():
    with patch("scar_add_metadata_toolbox.classes.CSWClient") as mock_csw_client:
        mock_csw_client.side_effect = MockCSWClientAuthError
        app = create_app()
        return app.test_cli_runner()


@pytest.fixture
def app_runner_mocked_csw_missing_auth_token():
    with patch("scar_add_metadata_toolbox.classes.CSWClient") as mock_csw_client:
        mock_csw_client.side_effect = MockCSWClientAuthMissing
        app = create_app()
        return app.test_cli_runner()


@pytest.fixture
def app_runner_mocked_csw_insufficient_auth_token():
    with patch("scar_add_metadata_toolbox.classes.CSWClient") as mock_csw_client:
        mock_csw_client.side_effect = MockCSWClientAuthInsufficient
        app = create_app()
        return app.test_cli_runner()


@pytest.fixture
def app_runner_mocked_csw_not_setup_mocked_collection():
    with patch("scar_add_metadata_toolbox.classes.CSWClient") as mock_csw_client, patch(
        "scar_add_metadata_toolbox.Collections"
    ) as mock_collections:
        mock_csw_client.side_effect = MockCSWClientServerNotSetup
        mock_collections.side_effect = MockCollections

        app = create_app()
        return app.test_cli_runner()


@pytest.fixture
def app_runner_mocked_csw_auth_token_error_mocked_collection():
    with patch("scar_add_metadata_toolbox.classes.CSWClient") as mock_csw_client, patch(
        "scar_add_metadata_toolbox.Collections"
    ) as mock_collections:
        mock_csw_client.side_effect = MockCSWClientAuthError
        mock_collections.side_effect = MockCollections

        app = create_app()
        return app.test_cli_runner()


@pytest.fixture
def app_runner_mocked_csw_missing_auth_token_mocked_collection():
    with patch("scar_add_metadata_toolbox.classes.CSWClient") as mock_csw_client, patch(
        "scar_add_metadata_toolbox.Collections"
    ) as mock_collections:
        mock_csw_client.side_effect = MockCSWClientAuthMissing
        mock_collections.side_effect = MockCollections

        app = create_app()
        return app.test_cli_runner()


@pytest.fixture
def app_runner_mocked_csw_insufficient_auth_token_mocked_collection():
    with patch("scar_add_metadata_toolbox.classes.CSWClient") as mock_csw_client, patch(
        "scar_add_metadata_toolbox.Collections"
    ) as mock_collections:
        mock_csw_client.side_effect = MockCSWClientAuthInsufficient
        mock_collections.side_effect = MockCollections

        app = create_app()
        return app.test_cli_runner()


@pytest.fixture
def app_runner_mocked_collections():
    with patch("scar_add_metadata_toolbox.classes.CSWClient") as mock_csw_client, patch(
        "scar_add_metadata_toolbox.Collections"
    ) as mock_collections:
        mock_csw_client.side_effect = MockCSWClient
        mock_collections.side_effect = MockCollections

        app = create_app()
        return app.test_cli_runner()


@pytest.fixture
def app_runner_mocked_collections_unknown_record():
    with patch("scar_add_metadata_toolbox.classes.CSWClient") as mock_csw_client, patch(
        "scar_add_metadata_toolbox.Collections"
    ) as mock_collections:
        mock_csw_client.side_effect = MockCSWClient
        mock_collections.side_effect = MockCollectionsUnknownRecord

        app = create_app()
        return app.test_cli_runner()


@pytest.fixture
def app_static_site():
    with patch("scar_add_metadata_toolbox.classes.CSWClient") as mock_csw_client, patch(
        "scar_add_metadata_toolbox.Collections"
    ) as mock_collections, TemporaryDirectory() as site_directory:
        mock_csw_client.side_effect = MockCSWClient
        mock_collections.side_effect = MockCollections

        app = create_app()
        app.config["SITE_PATH"] = Path(site_directory)
        return app


@pytest.fixture
def app_runner_mocked_csw_server():
    with patch("scar_add_metadata_toolbox.utils.CSWServer") as mock_csw_server:
        mock_csw_server.side_effect = MockCSWServer

        app = create_app()
        return app.test_cli_runner()


@pytest.fixture
def app_client_mocked_csw_server():
    with patch("scar_add_metadata_toolbox.utils.CSWServer") as mock_csw_server:
        mock_csw_server.side_effect = MockCSWServer

        app = create_app()
        return app.test_client()


@pytest.fixture
def app_client_mocked_csw_server_not_setup():
    with patch("scar_add_metadata_toolbox.utils.CSWServer") as mock_csw_server:
        mock_csw_server.side_effect = MockCSWServerNotSetup

        app = create_app()
        return app.test_client()


@pytest.fixture
def app_client_mocked_csw_server_requests_fail():
    with patch("scar_add_metadata_toolbox.utils.CSWServer") as mock_csw_server:
        mock_csw_server.side_effect = MockCSWServerRequestsFail

        app = create_app()
        return app.test_client()


@pytest.fixture
def app_client_mocked_csw_server_auth_token_error():
    with patch("scar_add_metadata_toolbox.utils.CSWServer") as mock_csw_server:
        mock_csw_server.side_effect = MockCSWServerAuthTokenError

        app = create_app()
        return app.test_client()


@pytest.fixture
def app_client_mocked_csw_server_missing_auth_token():
    with patch("scar_add_metadata_toolbox.utils.CSWServer") as mock_csw_server:
        mock_csw_server.side_effect = MockCSWServerMissingAuthToken

        app = create_app()
        return app.test_client()


@pytest.fixture
def app_client_mocked_csw_server_insufficient_auth_token():
    with patch("scar_add_metadata_toolbox.utils.CSWServer") as mock_csw_server:
        mock_csw_server.side_effect = MockCSWServerInsufficientAuthToken

        app = create_app()
        return app.test_client()


@pytest.fixture
def classes_csw_client():
    return CSWClient(config={"endpoint": "test", "auth": {}})


@pytest.fixture
def classes_record_summary():
    return RecordSummary(config={"file_identifier": "test", "resource": {"title": {"value": "test"}}})


@pytest.fixture
def classes_record():
    return Record(config={"file_identifier": "test", "resource": {"title": {"value": "test"}}})


@pytest.fixture
def classes_mirror_record_summary():
    return MirrorRecordSummary(
        config={"file_identifier": "test", "resource": {"title": {"value": "test"}}}, published=False
    )


@pytest.fixture
def classes_mirror_record():
    return MirrorRecord(config={"file_identifier": "test", "resource": {"title": {"value": "test"}}}, published=False)


@pytest.fixture
def classes_item():
    return Item(record=Record(config={"file_identifier": "test", "title": "test"}))


@pytest.fixture
def classes_collection():
    return Collection(config={"identifier": "test"})
