from __future__ import annotations

from pathlib import Path
from typing import Any

from bas_metadata_library.standards.iso_19115_2 import MetadataRecord
from flask import Flask, Request, Response

from scar_add_metadata_toolbox.csw import (
    CSWAmbiguousRequestError,
    CSWAuthError,
    CSWAuthInsufficientError,
    CSWAuthMissingError,
    CSWClient,
    CSWDatabaseAlreadyInitialisedError,
    CSWDatabaseNotInitialisedError,
    CSWGetRecordMode,
    CSWServer,
    CSWTrackingRepositoryAlreadyInitialisedError,
    CSWTrackingRepositoryInvalidCredentialsError,
    CSWTrackingRepositoryNotEnabledError,
    CSWTrackingRepositoryNotInitialisedError,
    CSWUnknownRequestError,
    CSWUnmappedRequestError,
    RecordInsertConflictError,
    RecordNotFoundError,
    RecordServerError,
)
from scar_add_metadata_toolbox.placeholders import PlaceholderAzureToken


class MockCSWClient(CSWClient):
    def __init__(self, config: dict) -> None:
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
        for identifier in self._records:
            with self._records_responses_base_path.joinpath(f"get_record_{identifier}_full.xml").open(
                mode="r"
            ) as record:
                self._records[identifier]["full"] = record.read()

    def get_record(self, identifier: str, mode: CSWGetRecordMode = CSWGetRecordMode.FULL) -> str:
        try:
            return self._records[identifier][mode.value]
        except KeyError:
            raise RecordNotFoundError() from None

    def get_records(self, mode: CSWGetRecordMode = CSWGetRecordMode.FULL) -> list[str]:
        for identifier in self._records:
            yield self.get_record(identifier=identifier, mode=mode)

    def insert_record(self, record: str) -> None:
        if isinstance(record, bytes):
            record = record.decode()
        _record_config = MetadataRecord(record=record).make_config().config
        _identifier = str(_record_config["file_identifier"])

        if _identifier in self._records:
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

    def get_records(self, mode: CSWGetRecordMode = CSWGetRecordMode.FULL) -> list[str]:
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

    def get_records(self, mode: CSWGetRecordMode = CSWGetRecordMode.FULL) -> list[str]:
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

    def get_records(self, mode: CSWGetRecordMode = CSWGetRecordMode.FULL) -> list[str]:
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

    def get_records(self, mode: CSWGetRecordMode = CSWGetRecordMode.FULL) -> list[str]:
        raise CSWAuthInsufficientError() from None

    def insert_record(self, record: str) -> None:
        raise CSWAuthInsufficientError() from None

    def update_record(self, record: str) -> None:
        raise CSWAuthInsufficientError() from None

    def delete_record(self, identifier: str) -> None:
        raise CSWAuthInsufficientError() from None


class MockCSWServer(CSWServer):
    def __init__(self, config: dict) -> None:
        super().__init__(config)

        self.backing_db_initialised = False
        self.backing_repo_initialised = False

    @property
    def _backing_db_is_initialised(self) -> bool:
        return self.backing_db_initialised

    @property
    def _backing_repo_is_initialised(self) -> bool:
        return self.backing_repo_initialised

    def setup_database(self) -> None:
        if self.backing_db_initialised:
            raise CSWDatabaseAlreadyInitialisedError() from None
        self.backing_db_initialised = True

    def setup_tracking(self) -> None:
        if self.backing_repo_initialised:
            raise CSWTrackingRepositoryAlreadyInitialisedError() from None
        self.backing_repo_initialised = True

    def process_request(self, request: Request, token: PlaceholderAzureToken | None = None) -> Response:
        return Response("ok")


class MockCSWServerBackingDBNotSetup(MockCSWServer):
    def process_request(self, request: Request, token: PlaceholderAzureToken | None = None) -> Response:
        raise CSWDatabaseNotInitialisedError() from None


class MockCSWServerBackingRepoNotSetup(MockCSWServer):
    def process_request(self, request: Request, token: PlaceholderAzureToken | None = None) -> Response:
        raise CSWTrackingRepositoryNotInitialisedError() from None


class MockCSWServerRevisionTrackingDisabled(MockCSWServer):
    def setup_tracking(self) -> None:
        raise CSWTrackingRepositoryNotEnabledError() from None


class MockCSWServerRevisionTrackingInvalidCredentials(MockCSWServer):
    def setup_tracking(self) -> None:
        raise CSWTrackingRepositoryInvalidCredentialsError from None


class MockCSWServerNoRequestType(MockCSWServer):
    def process_request(self, request: Request, token: PlaceholderAzureToken | None = None) -> Response:
        raise CSWUnknownRequestError() from None


class MockCSWServerAmbiguousRequestError(MockCSWServer):
    def process_request(self, request: Request, token: PlaceholderAzureToken | None = None) -> Response:
        raise CSWAmbiguousRequestError() from None


class MockCSWServerUnmappedRequestError(MockCSWServer):
    def process_request(self, request: Request, token: PlaceholderAzureToken | None = None) -> Response:
        raise CSWUnmappedRequestError() from None


class MockCSWServerAuthTokenError(MockCSWServer):
    def process_request(self, request: Request, token: PlaceholderAzureToken | None = None) -> Response:
        raise CSWAuthError() from None


class MockCSWServerMissingAuthToken(MockCSWServer):
    def process_request(self, request: Request, token: PlaceholderAzureToken | None = None) -> Response:
        raise CSWAuthMissingError() from None


class MockCSWServerInsufficientAuthToken(MockCSWServer):
    def process_request(self, request: Request, token: PlaceholderAzureToken | None = None) -> Response:
        raise CSWAuthInsufficientError() from None


class MockCSWServerRequestsFail(MockCSWServer):
    def process_request(self, request: Request, token: PlaceholderAzureToken | None = None) -> Response:
        raise RecordServerError() from None


class MockPublicClientApplication:
    # noinspection PyUnusedLocal
    def __init__(self, client_id: str, authority: str) -> None:
        pass

    # noinspection PyUnusedLocal
    @staticmethod
    def initiate_device_flow(scopes: list[str]) -> dict:
        return {"user_code": "test"}

    # noinspection PyUnusedLocal
    @staticmethod
    def acquire_token_by_device_flow(device_flow: dict) -> dict:
        return {"access_token": {}}
        # return {
        #     "access_token": TestJwt(
        #         app=current_app, roles=["BAS.MAGIC.ADD.Records.ReadWrite.All", "BAS.MAGIC.ADD.Records.Publish.All"]  # noqa: ERA001
        #     ).dumps()
        # }  noqa: ERA001


def create_mock_auth(scopes_used: list[str] | None = None):
    class MockFlaskAzureOauth:
        # noinspection PyUnusedLocal
        def init_app(self, app: Flask) -> None:
            pass

        def __call__(self, scopes: str | None = None, *args, **kwargs) -> callable:  # noqa: ANN002, ANN003
            def checkauth(func: callable) -> Any:
                def wrapper(*args, **kwargs) -> callable:  # noqa: ANN002, ANN003
                    if scopes_used is not None:
                        scopes_used.append(scopes)

                    return func(*args, **kwargs)

                wrapper.__name__ = func.__name__

                return wrapper

            return checkauth

    return MockFlaskAzureOauth
