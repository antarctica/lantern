from typing import List, Optional
from pathlib import Path

from flask import Request, Response, current_app
from flask_azure_oauth import AzureToken
from flask_azure_oauth.tokens import TestJwt

from scar_add_metadata_toolbox.hazmat.metadata import generate_record_config_from_record_xml
from scar_add_metadata_toolbox.csw import (
    CSWServer,
    CSWClient,
    CSWGetRecordMode,
    RecordInsertConflictException,
    RecordNotFoundException,
    RecordServerException,
    CSWDatabaseAlreadyInitialisedException,
    CSWDatabaseNotInitialisedException,
    CSWAuthMissingException,
    CSWAuthInsufficientException,
    CSWAuthException,
)
from scar_add_metadata_toolbox.classes import (
    Collections,
    Collection,
    CollectionNotFoundException,
)


class MockCSWClient(CSWClient):
    def __init__(self, config: dict):
        super().__init__(config)

        self._records = {}
        self._records_responses_base_path = Path("./tests/scar_add_metadata_toolbox/resources/csw/records")
        if self._csw_endpoint == "http://example.com/csw/unpublished":
            self._records["7e3719b4-60a4-4b4e-aa84-cee7a5e7218f"] = {"full": "", "brief": ""}
            self._records["39d47e50-f94f-43c5-9060-510d9374b81b"] = {"full": "", "brief": ""}
        if self._csw_endpoint == "http://example.com/csw/published":
            self._records["7e3719b4-60a4-4b4e-aa84-cee7a5e7218f"] = {"full": "", "brief": ""}
        for identifier in self._records.keys():
            with open(
                str(self._records_responses_base_path.joinpath(f"get_record_{identifier}_full.xml")), mode="r",
            ) as record:
                self._records[identifier]["full"] = record.read()
            with open(
                str(self._records_responses_base_path.joinpath(f"get_record_{identifier}_brief.xml")), mode="r",
            ) as record:
                self._records[identifier]["brief"] = record.read()

    def get_record(self, identifier: str, mode: CSWGetRecordMode = CSWGetRecordMode.FULL) -> str:
        try:
            return self._records[identifier][mode.value]
        except KeyError:
            raise RecordNotFoundException()

    def get_records(self, mode: CSWGetRecordMode = CSWGetRecordMode.FULL) -> List[str]:
        for identifier in self._records.keys():
            yield self.get_record(identifier=identifier, mode=mode)

    def insert_record(self, record: str) -> None:
        if isinstance(record, bytes):
            record = record.decode()
        _record_config = generate_record_config_from_record_xml(record_xml=record)
        _identifier = _record_config["file_identifier"]

        if _identifier in self._records.keys():
            raise RecordInsertConflictException()

        self._records[_identifier] = {"full": record, "brief": record}

    def update_record(self, record: str) -> None:
        if isinstance(record, bytes):
            record = record.decode()
        _record_config = generate_record_config_from_record_xml(record_xml=record)
        _identifier = _record_config["file_identifier"]

        self._records[_identifier] = {"full": record, "brief": record}

    def delete_record(self, identifier: str) -> None:
        try:
            del self._records[identifier]
        except KeyError:
            raise RecordNotFoundException()


class MockCSWClientInsertsFail(MockCSWClient):
    def insert_record(self, record: str) -> None:
        raise RecordServerException()


class MockCSWClientServerNotSetup(MockCSWClient):
    def get_record(self, identifier: str, mode: CSWGetRecordMode = CSWGetRecordMode.FULL) -> str:
        raise CSWDatabaseNotInitialisedException()

    def get_records(self, mode: CSWGetRecordMode = CSWGetRecordMode.FULL) -> List[str]:
        raise CSWDatabaseNotInitialisedException()

    def insert_record(self, record: str) -> None:
        raise CSWDatabaseNotInitialisedException()

    def update_record(self, record: str) -> None:
        raise CSWDatabaseNotInitialisedException()

    def delete_record(self, identifier: str) -> None:
        raise CSWDatabaseNotInitialisedException()


class MockCSWClientAuthError(MockCSWClient):
    def get_record(self, identifier: str, mode: CSWGetRecordMode = CSWGetRecordMode.FULL) -> str:
        raise CSWAuthException()

    def get_records(self, mode: CSWGetRecordMode = CSWGetRecordMode.FULL) -> List[str]:
        raise CSWAuthException()

    def insert_record(self, record: str) -> None:
        raise CSWAuthException()

    def update_record(self, record: str) -> None:
        raise CSWAuthException()

    def delete_record(self, identifier: str) -> None:
        raise CSWAuthException()


class MockCSWClientAuthMissing(MockCSWClient):
    def get_record(self, identifier: str, mode: CSWGetRecordMode = CSWGetRecordMode.FULL) -> str:
        raise CSWAuthMissingException()

    def get_records(self, mode: CSWGetRecordMode = CSWGetRecordMode.FULL) -> List[str]:
        raise CSWAuthMissingException()

    def insert_record(self, record: str) -> None:
        raise CSWAuthMissingException()

    def update_record(self, record: str) -> None:
        raise CSWAuthMissingException()

    def delete_record(self, identifier: str) -> None:
        raise CSWAuthMissingException()


class MockCSWClientAuthInsufficient(MockCSWClient):
    def get_record(self, identifier: str, mode: CSWGetRecordMode = CSWGetRecordMode.FULL) -> str:
        raise CSWAuthInsufficientException()

    def get_records(self, mode: CSWGetRecordMode = CSWGetRecordMode.FULL) -> List[str]:
        raise CSWAuthInsufficientException()

    def insert_record(self, record: str) -> None:
        raise CSWAuthInsufficientException()

    def update_record(self, record: str) -> None:
        raise CSWAuthInsufficientException()

    def delete_record(self, identifier: str) -> None:
        raise CSWAuthInsufficientException()


class MockCSWServer(CSWServer):
    def __init__(self, config: dict):
        super().__init__(config)

        self.initialised = False

    @property
    def _is_initialised(self) -> bool:
        return self.initialised

    def setup(self) -> None:
        if self.initialised:
            raise CSWDatabaseAlreadyInitialisedException()
        self.initialised = True

    def process_request(self, request: Request, token: Optional[AzureToken] = None) -> Response:
        return Response("ok")


class MockCSWServerNotSetup(MockCSWServer):
    def process_request(self, request: Request, token: Optional[AzureToken] = None) -> Response:
        raise CSWDatabaseNotInitialisedException()


class MockCSWServerAuthTokenError(MockCSWServer):
    def process_request(self, request: Request, token: Optional[AzureToken] = None) -> Response:
        raise CSWAuthException()


class MockCSWServerMissingAuthToken(MockCSWServer):
    def process_request(self, request: Request, token: Optional[AzureToken] = None) -> Response:
        raise CSWAuthMissingException()


class MockCSWServerInsufficientAuthToken(MockCSWServer):
    def process_request(self, request: Request, token: Optional[AzureToken] = None) -> Response:
        raise CSWAuthInsufficientException()


class MockCSWServerRequestsFail(MockCSWServer):
    def process_request(self, request: Request, token: Optional[AzureToken] = None) -> Response:
        raise RecordServerException()


class MockCollections(Collections):
    # noinspection PyMissingConstructor,PyUnusedLocal
    def __init__(self, config: dict):
        self.collections = {
            "b759077f-bd3f-4a18-bbd7-e6b3f84bc551": {
                "identifier": "b759077f-bd3f-4a18-bbd7-e6b3f84bc551",
                "title": "Test Collection 1",
                "topics": ["Topographic Mapping"],
                "publishers": ["Mapping and Geographic Information Centre (MAGIC)"],
                "summary": "Description for Test Collection 1.",
                "item_identifiers": ["7e3719b4-60a4-4b4e-aa84-cee7a5e7218f"],
            },
        }

    def update(self, collection: Collection) -> None:
        self.collections[collection.identifier] = collection.dumps()

    def delete(self, collection_identifier: str) -> None:
        try:
            del self.collections[collection_identifier]
        except KeyError:
            raise CollectionNotFoundException()


class MockCollectionsUnknownRecord(Collections):
    # noinspection PyMissingConstructor,PyUnusedLocal
    def __init__(self, config: dict):
        self.collections = {
            "0d1b9063-da63-403d-ba16-f72e5f6f5688": {
                "identifier": "0d1b9063-da63-403d-ba16-f72e5f6f5688",
                "title": "Test Collection 4 (Imported, contains unknown item identifier)",
                "topics": ["Topographic Mapping"],
                "publishers": ["Mapping and Geographic Information Centre (MAGIC)"],
                "summary": "Description for Test Collection 4.",
                "item_identifiers": ["unknown"],
            },
        }

    def update(self, collection: Collection) -> None:
        self.collections[collection.identifier] = collection.dumps()

    def delete(self, collection_identifier: str) -> None:
        try:
            del self.collections[collection_identifier]
        except KeyError:
            raise CollectionNotFoundException()


class MockPublicClientApplication:
    # noinspection PyUnusedLocal
    def __init__(self, client_id, authority):
        pass

    # noinspection PyUnusedLocal
    @staticmethod
    def initiate_device_flow(scopes):
        return {"user_code": "test"}

    # noinspection PyUnusedLocal
    @staticmethod
    def acquire_token_by_device_flow(device_flow):
        return {
            "access_token": TestJwt(
                app=current_app, roles=["BAS.MAGIC.ADD.Records.ReadWrite.All", "BAS.MAGIC.ADD.Records.Publish.All"]
            ).dumps()
        }
