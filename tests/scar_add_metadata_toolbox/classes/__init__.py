from pathlib import Path
from typing import List, Optional

from bas_metadata_library.standards.iso_19115_2 import MetadataRecord
from flask import current_app, Request, Response
from flask_azure_oauth import AzureToken
from flask_azure_oauth.mocks.tokens import TestJwt

from scar_add_metadata_toolbox.csw import (
    CSWAuthException,
    CSWAuthInsufficientException,
    CSWAuthMissingException,
    CSWClient,
    CSWDatabaseAlreadyInitialisedException,
    CSWDatabaseNotInitialisedException,
    CSWGetRecordMode,
    CSWServer,
    RecordInsertConflictException,
    RecordNotFoundException,
    RecordServerException,
)


class MockCSWClient(CSWClient):
    def __init__(self, config: dict):
        super().__init__(config)

        self._records = {}
        self._records_responses_base_path = Path(__file__).parent.resolve().parent.joinpath("resources/csw/records")
        if self._csw_endpoint == "http://example.com/csw/unpublished":
            self._records["7e3719b4-60a4-4b4e-aa84-cee7a5e7218f"] = {"full": ""}
            self._records["39d47e50-f94f-43c5-9060-510d9374b81b"] = {"full": ""}
            self._records["b759077f-bd3f-4a18-bbd7-e6b3f84bc551"] = {"full": ""}
        if self._csw_endpoint == "http://example.com/csw/published":
            self._records["7e3719b4-60a4-4b4e-aa84-cee7a5e7218f"] = {"full": ""}
            self._records["b759077f-bd3f-4a18-bbd7-e6b3f84bc551"] = {"full": ""}
        for identifier in self._records.keys():
            with open(
                self._records_responses_base_path.joinpath(f"get_record_{identifier}_full.xml"), mode="r"
            ) as record:
                self._records[identifier]["full"] = record.read()

    def get_record(self, identifier: str, mode: CSWGetRecordMode = CSWGetRecordMode.FULL) -> str:
        try:
            return self._records[identifier][mode.value]
        except KeyError:
            raise RecordNotFoundException() from None

    def get_records(self, mode: CSWGetRecordMode = CSWGetRecordMode.FULL) -> List[str]:
        for identifier in self._records.keys():
            yield self.get_record(identifier=identifier, mode=mode)

    def insert_record(self, record: str) -> None:
        if isinstance(record, bytes):
            record = record.decode()
        _record_config = MetadataRecord(record=record).make_config().config
        _identifier = str(_record_config["file_identifier"])

        if _identifier in self._records.keys():
            raise RecordInsertConflictException()

        self._records[_identifier] = {"full": record, "brief": record}

    def update_record(self, record: str) -> None:
        if isinstance(record, bytes):
            record = record.decode()
        _record_config = MetadataRecord(record=record).make_config().config
        _identifier = str(_record_config["file_identifier"])

        self._records[_identifier] = {"full": record, "brief": record}

    def delete_record(self, identifier: str) -> None:
        try:
            del self._records[identifier]
        except KeyError:
            raise RecordNotFoundException() from None


class MockCSWClientInsertsFail(MockCSWClient):
    def insert_record(self, record: str) -> None:
        raise RecordServerException() from None


class MockCSWClientServerNotSetup(MockCSWClient):
    def get_record(self, identifier: str, mode: CSWGetRecordMode = CSWGetRecordMode.FULL) -> str:
        raise CSWDatabaseNotInitialisedException() from None

    def get_records(self, mode: CSWGetRecordMode = CSWGetRecordMode.FULL) -> List[str]:
        raise CSWDatabaseNotInitialisedException() from None

    def insert_record(self, record: str) -> None:
        raise CSWDatabaseNotInitialisedException() from None

    def update_record(self, record: str) -> None:
        raise CSWDatabaseNotInitialisedException() from None

    def delete_record(self, identifier: str) -> None:
        raise CSWDatabaseNotInitialisedException() from None


class MockCSWClientAuthError(MockCSWClient):
    def get_record(self, identifier: str, mode: CSWGetRecordMode = CSWGetRecordMode.FULL) -> str:
        raise CSWAuthException() from None

    def get_records(self, mode: CSWGetRecordMode = CSWGetRecordMode.FULL) -> List[str]:
        raise CSWAuthException() from None

    def insert_record(self, record: str) -> None:
        raise CSWAuthException() from None

    def update_record(self, record: str) -> None:
        raise CSWAuthException() from None

    def delete_record(self, identifier: str) -> None:
        raise CSWAuthException() from None


class MockCSWClientAuthMissing(MockCSWClient):
    def get_record(self, identifier: str, mode: CSWGetRecordMode = CSWGetRecordMode.FULL) -> str:
        raise CSWAuthMissingException() from None

    def get_records(self, mode: CSWGetRecordMode = CSWGetRecordMode.FULL) -> List[str]:
        raise CSWAuthMissingException() from None

    def insert_record(self, record: str) -> None:
        raise CSWAuthMissingException() from None

    def update_record(self, record: str) -> None:
        raise CSWAuthMissingException() from None

    def delete_record(self, identifier: str) -> None:
        raise CSWAuthMissingException() from None


class MockCSWClientAuthInsufficient(MockCSWClient):
    def get_record(self, identifier: str, mode: CSWGetRecordMode = CSWGetRecordMode.FULL) -> str:
        raise CSWAuthInsufficientException() from None

    def get_records(self, mode: CSWGetRecordMode = CSWGetRecordMode.FULL) -> List[str]:
        raise CSWAuthInsufficientException() from None

    def insert_record(self, record: str) -> None:
        raise CSWAuthInsufficientException() from None

    def update_record(self, record: str) -> None:
        raise CSWAuthInsufficientException() from None

    def delete_record(self, identifier: str) -> None:
        raise CSWAuthInsufficientException() from None


class MockCSWServer(CSWServer):
    def __init__(self, config: dict):
        super().__init__(config)

        self.initialised = False

    @property
    def _is_initialised(self) -> bool:
        return self.initialised

    def setup(self) -> None:
        if self.initialised:
            raise CSWDatabaseAlreadyInitialisedException() from None
        self.initialised = True

    def process_request(self, request: Request, token: Optional[AzureToken] = None) -> Response:
        return Response("ok")


class MockCSWServerNotSetup(MockCSWServer):
    def process_request(self, request: Request, token: Optional[AzureToken] = None) -> Response:
        raise CSWDatabaseNotInitialisedException() from None


class MockCSWServerAuthTokenError(MockCSWServer):
    def process_request(self, request: Request, token: Optional[AzureToken] = None) -> Response:
        raise CSWAuthException() from None


class MockCSWServerMissingAuthToken(MockCSWServer):
    def process_request(self, request: Request, token: Optional[AzureToken] = None) -> Response:
        raise CSWAuthMissingException() from None


class MockCSWServerInsufficientAuthToken(MockCSWServer):
    def process_request(self, request: Request, token: Optional[AzureToken] = None) -> Response:
        raise CSWAuthInsufficientException() from None


class MockCSWServerRequestsFail(MockCSWServer):
    def process_request(self, request: Request, token: Optional[AzureToken] = None) -> Response:
        raise RecordServerException() from None


class MockPublicClientApplication:
    # noinspection PyUnusedLocal
    def __init__(self, client_id, authority):
        pass

    # noinspection PyUnusedLocal
    @staticmethod
    def initiate_device_flow(scopes) -> dict:
        return {"user_code": "test"}

    # noinspection PyUnusedLocal
    @staticmethod
    def acquire_token_by_device_flow(device_flow):
        return {
            "access_token": TestJwt(
                app=current_app, roles=["BAS.MAGIC.ADD.Records.ReadWrite.All", "BAS.MAGIC.ADD.Records.Publish.All"]
            ).dumps()
        }
