from pathlib import Path
from typing import List, Optional

from bas_metadata_library.standards.iso_19115_2 import MetadataRecord
from flask import current_app, Request, Response
from flask_azure_oauth import AzureToken
from flask_azure_oauth.mocks.tokens import TestJwt

from scar_add_metadata_toolbox.csw import (
    CSWAuthError,
    CSWAuthInsufficientError,
    CSWAuthMissingError,
    CSWClient,
    CSWDatabaseAlreadyInitialisedError,
    CSWDatabaseNotInitialisedError,
    CSWGetRecordMode,
    CSWServer,
    RecordInsertConflictError,
    RecordNotFoundError,
    RecordServerError,
)


class MockCSWClient(CSWClient):
    def __init__(self, config: dict):
        super().__init__(config)

        self._records = {}
        self._records_responses_base_path = Path(__file__).parent.resolve().parent.joinpath("resources/csw/records")
        if self._csw_endpoint == "https://example.com/csw/unpublished":
            self._records["7e3719b4-60a4-4b4e-aa84-cee7a5e7218f"] = {"full": ""}
            self._records["39d47e50-f94f-43c5-9060-510d9374b81b"] = {"full": ""}
            self._records["b759077f-bd3f-4a18-bbd7-e6b3f84bc551"] = {"full": ""}
        if self._csw_endpoint == "https://example.com/csw/published":
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
            raise RecordNotFoundError() from None

    def get_records(self, mode: CSWGetRecordMode = CSWGetRecordMode.FULL) -> List[str]:
        for identifier in self._records.keys():
            yield self.get_record(identifier=identifier, mode=mode)

    def insert_record(self, record: str) -> None:
        if isinstance(record, bytes):
            record = record.decode()
        _record_config = MetadataRecord(record=record).make_config().config
        _identifier = str(_record_config["file_identifier"])

        if _identifier in self._records.keys():
            raise RecordInsertConflictError()

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
            raise RecordNotFoundError() from None


class MockCSWClientInsertsFail(MockCSWClient):
    def insert_record(self, record: str) -> None:
        raise RecordServerError() from None


class MockCSWClientServerNotSetup(MockCSWClient):
    def get_record(self, identifier: str, mode: CSWGetRecordMode = CSWGetRecordMode.FULL) -> str:
        raise CSWDatabaseNotInitialisedError() from None

    def get_records(self, mode: CSWGetRecordMode = CSWGetRecordMode.FULL) -> List[str]:
        raise CSWDatabaseNotInitialisedError() from None

    def insert_record(self, record: str) -> None:
        raise CSWDatabaseNotInitialisedError() from None

    def update_record(self, record: str) -> None:
        raise CSWDatabaseNotInitialisedError() from None

    def delete_record(self, identifier: str) -> None:
        raise CSWDatabaseNotInitialisedError() from None


class MockCSWClientAuthError(MockCSWClient):
    def get_record(self, identifier: str, mode: CSWGetRecordMode = CSWGetRecordMode.FULL) -> str:
        raise CSWAuthError() from None

    def get_records(self, mode: CSWGetRecordMode = CSWGetRecordMode.FULL) -> List[str]:
        raise CSWAuthError() from None

    def insert_record(self, record: str) -> None:
        raise CSWAuthError() from None

    def update_record(self, record: str) -> None:
        raise CSWAuthError() from None

    def delete_record(self, identifier: str) -> None:
        raise CSWAuthError() from None


class MockCSWClientAuthMissing(MockCSWClient):
    def get_record(self, identifier: str, mode: CSWGetRecordMode = CSWGetRecordMode.FULL) -> str:
        raise CSWAuthMissingError() from None

    def get_records(self, mode: CSWGetRecordMode = CSWGetRecordMode.FULL) -> List[str]:
        raise CSWAuthMissingError() from None

    def insert_record(self, record: str) -> None:
        raise CSWAuthMissingError() from None

    def update_record(self, record: str) -> None:
        raise CSWAuthMissingError() from None

    def delete_record(self, identifier: str) -> None:
        raise CSWAuthMissingError() from None


class MockCSWClientAuthInsufficient(MockCSWClient):
    def get_record(self, identifier: str, mode: CSWGetRecordMode = CSWGetRecordMode.FULL) -> str:
        raise CSWAuthInsufficientError() from None

    def get_records(self, mode: CSWGetRecordMode = CSWGetRecordMode.FULL) -> List[str]:
        raise CSWAuthInsufficientError() from None

    def insert_record(self, record: str) -> None:
        raise CSWAuthInsufficientError() from None

    def update_record(self, record: str) -> None:
        raise CSWAuthInsufficientError() from None

    def delete_record(self, identifier: str) -> None:
        raise CSWAuthInsufficientError() from None


class MockCSWServer(CSWServer):
    def __init__(self, config: dict):
        super().__init__(config)

        self.initialised = False

    @property
    def _is_initialised(self) -> bool:
        return self.initialised

    def setup(self) -> None:
        if self.initialised:
            raise CSWDatabaseAlreadyInitialisedError() from None
        self.initialised = True

    def process_request(self, request: Request, token: Optional[AzureToken] = None) -> Response:
        return Response("ok")


class MockCSWServerNotSetup(MockCSWServer):
    def process_request(self, request: Request, token: Optional[AzureToken] = None) -> Response:
        raise CSWDatabaseNotInitialisedError() from None


class MockCSWServerAuthTokenError(MockCSWServer):
    def process_request(self, request: Request, token: Optional[AzureToken] = None) -> Response:
        raise CSWAuthError() from None


class MockCSWServerMissingAuthToken(MockCSWServer):
    def process_request(self, request: Request, token: Optional[AzureToken] = None) -> Response:
        raise CSWAuthMissingError() from None


class MockCSWServerInsufficientAuthToken(MockCSWServer):
    def process_request(self, request: Request, token: Optional[AzureToken] = None) -> Response:
        raise CSWAuthInsufficientError() from None


class MockCSWServerRequestsFail(MockCSWServer):
    def process_request(self, request: Request, token: Optional[AzureToken] = None) -> Response:
        raise RecordServerError() from None


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
