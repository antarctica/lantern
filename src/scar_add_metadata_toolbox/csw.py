from copy import deepcopy
from enum import Enum
from typing import Dict, Generator, Optional

from flask import Request, Response
from flask_azure_oauth import AzureToken
from lxml.etree import (
    Element,
    ElementTree,
    fromstring,
    tostring,
    XMLSyntaxError,
)  # nosec - see 'lxml` package (bandit)' section in README
from requests import HTTPError
from sqlalchemy import create_engine, inspect
from sqlalchemy.exc import ProgrammingError

from scar_add_metadata_toolbox.hazmat.owslib.csw import CatalogueServiceWeb as _CSWClient, namespaces as csw_namespaces
from scar_add_metadata_toolbox.hazmat.owslib.namespaces import Namespaces
from scar_add_metadata_toolbox.hazmat.owslib.ows import ExceptionReport
from scar_add_metadata_toolbox.hazmat.owslib.util import Authentication as CSWAuth, ServiceException
from scar_add_metadata_toolbox.hazmat.pycsw.core import admin
from scar_add_metadata_toolbox.hazmat.pycsw.server import Csw as _CSWServer


class CSWGetRecordMode(Enum):
    """
    Represents the element set names used in the CSW specification
    """

    FULL = "full"
    SUMMARY = "summary"
    BRIEF = "brief"


class CSWTransactionType(Enum):
    """
    Represents the transaction types used in the CSW specification, plus a 'SELECT' value to represent
    retrieval only requests.
    """

    SELECT = "select"
    INSERT = "insert"
    UPDATE = "update"
    DELETE = "delete"


class CSWDatabaseAlreadyInitialisedError(Exception):
    """
    Represents a situation whereby a CSW Server's backing database has already been initialised

    Backing databases must only be initialised once to avoid errors creating duplicate structures or unwanted side
    effects such as table truncation. If a database is initialised multiple times this role would be violated.
    """

    pass


class CSWDatabaseNotInitialisedError(Exception):
    """
    Represents a situation where the backing database for a CSW Server has not yet been initialised

    Backing databases must be initialised to ensure relevant database structures, indexes and triggers exist and are
    configured before records are written or read from a catalogue. If requests are made to a CSW server before has
    happened this rule would be violated. The relevant initialisation method can be run to resolve this.
    """

    pass


class CSWDatabasePostGISExtensionUnavailableError(Exception):
    """
    Represents a situation where the backing database or a CSW Server does not have the PostGIS extension enabled

    Backing databases must have this extension to support spatial querying as part of the CSW standard (e.g. searching
    by bounding box). If the PyCSW admin database setup method is called without this extension available, it will
    attempt to use a workaround which leads to problems with creating duplicate tables.
    """

    pass


class CSWMethodNotSupportedError(Exception):
    """
    Represents a situation where an unsupported HTTP method is used in a request to a CSW Server

    CSW requests must use the HEAD, GET or POST HTTP method. If another method is used this rule would be violated.
    """

    pass


class CSWUnknownRequestError(Exception):
    """
    Represents a situation where a CSW request doesn't contain a property describing the type of request

    E.g. for GET requests, a 'request' string query parameter is not included, or in Post requests, there isn't a
    recognised element that can mapped to a request type (e.g. a '<csw:Query>' element can be mapped to a 'query' type).

    It is inherently hard to be specific about how to resolve this error. As we take a restrictive approach to detecting
    request types, it's possible the request made by the client is perfectly valid but not yet supported by us.
    """

    pass


class CSWAmbiguousRequestError(Exception):
    """
    Represents a situation where a CSW request contains multiple properties describing the type of request

    E.g. a request contains a 'request' string query parameter and an element in the body (such as '<csw:Query>').

    This makes it non-trivial to determine the overall request type (e.g. if one property indicates a read request and
    another a write request) and introduces ambiguity that could lead to processing errors (potentially not doing what
    the user expected) or security errors (where a write request is allowed when it shouldn't).

    To avoid these situations, any request that is ambiguity is rejected. It is inherently hard to be specific about
    how to resolve this error, but it's unlikely to be a false positive.
    """

    pass


class CSWUnmappedRequestError(Exception):
    """
    Represents a situation where a CSW request contains a 'request' string query parameter that is not mapped to a
    transaction type

    E.g. a request contains a 'request' string query parameter with a value of 'Foo', which is not yet mapped to one of
    the four transaction types (select, insert, update, delete).

    The CSW 'request' query parameter is inherently specific to the type of operation being requested (e.g.
    'GetRecordById' vs 'GetRecords'). This is too granular whether a user is authorised to perform an action, where the
    broader transaction type is more appropriate to base a decision on.

    An internal mapping is used to associate specific request types with general transaction types. Where a request
    does not appear in this mapping, this error will be raised. There is nothing the user can do to fix this error,
    except to use a different request type that is mapped, or raise a bug report. We do not list the types of requests
    that are mapped.

    In practice, this error should not occur however, as the catalogue client CLI internally makes CSW requests itself
    and would therefore trigger those that are expected to be used by other types of clients. It's possible other \
    clients may wish to make more exotic requests but that does not mean we need to support them.
    """

    pass


class CSWAuthError(Exception):
    """
    Represents a situation where there the authentication information included in a CSW request causes an error

    This is a non-specific error and could indicate a range of situations, such as a token having expired or being
    malformed.
    """

    pass


class CSWAuthMissingError(Exception):
    """
    Represents a situation where authentication information is required for a CSW request but was not included

    Requests to authenticated CSW requests must include authentication information. If this is missing this rule would
    be violated.
    """

    pass


class CSWAuthInsufficientError(Exception):
    """
    Indicates a situation where the authorisation requirements for a CSW request are not satisfied by the information
    included in the request

    Requests to authorised CSW requests must include authorisation information that satisfies all the requirements of
    the resource or action being requested. If any of these requirements are not met this rule would be violated.

    Usually this error relates to missing scopes/roles that are required by the resource or action being requested.
    E.g. to publish a record the 'Publish' scope/role is required.
    """

    pass


class RecordServerError(Exception):
    """
    Represents a situation where a record server encounters an error processing a request

    This is a non-specific error and could indicate a range of situations, such as a record being malformed or an
    internal error within record server.
    """

    pass


class RecordNotFoundError(Exception):
    """
    Represents a situation where a given record does not exist
    """

    pass


class RecordInsertConflictError(Exception):
    """
    Represents a situation where a record to be inserted already exists in a repository

    Records in repositories must be unique. If a record is inserted with the same identifier as an existing record,
    neither record not be unique and this rule would be violated. Records may be updated instead.
    """

    pass


class CSWServer:  # pragma: no cover (until #59 is resolved)
    """
    Represents a CSW Server backed by PyCSW

    This class is largely a wrapper around the PyCSW class in order to improve integrating CSW functionality within
    a larger application, and to add additional functionality including:

    * raising exceptions for errors
    * support for token based authentication
    * support for performing/reporting backing database initialisation
    * simplifying PyCSW configuration options using a base configuration

    Note: This class uses classes from the Hazardous Materials module. This is to work around limitations in the PyCSW
    package. This will be addressed by upstreaming missing functionality or creating a derivative package.
    """

    base_configuration = {
        "server": {
            "url": None,
            "mimetype": "application/xml; charset=UTF-8",
            "encoding": "UTF-8",
            "language": "en-GB",
            "maxrecords": "100",
            "loglevel": "DEBUG",
            "pretty_print": "true",
            "gzip_compresslevel": "8",
            "domainquerytype": "list",
            "domaincounts": "false",
            "profiles": "apiso",
        },
        "manager": {
            "transactions": "true",
            "allowed_ips": "*.*.*.*",
        },
        "metadata:main": {
            "identification_title": "Internal CSW (Published)",
            "identification_abstract": "Internal PyCSW OGC CSW server for published records",
            "identification_keywords": "catalogue, discovery, metadata",
            "identification_keywords_type": "theme",
            "identification_fees": "None",
            "identification_accessconstraints": "None",
            "provider_name": "British Antarctic Survey",
            "provider_url": "https://www.bas.ac.uk/",
            "contact_name": "Mapping and Geographic Information Centre, British Antarctic Survey",
            "contact_position": "Technical Contact",
            "contact_address": "British Antarctic Survey, Madingley Road, High Cross",
            "contact_city": "Cambridge",
            "contact_stateorprovince": "Cambridgeshire",
            "contact_postalcode": "CB30ET",
            "contact_country": "United Kingdom",
            "contact_phone": "+44(0) 1223 221400",
            "contact_email": "magic@bas.ac.uk",
            "contact_url": "https://www.bas.ac.uk/team/magic",
            "contact_hours": "09:00 - 17:00",
            "contact_instructions": "During hours of service on weekdays. Best efforts support only.",
            "contact_role": "pointOfContact",
        },
        "repository": {"database": None, "table": None},
        "metadata:inspire": {
            "enabled": "true",
            "languages_supported": "eng",
            "default_language": "eng",
            "date": "YYYY-MM-DD",
            "gemet_keywords": "Utility and governmental services",
            "conformity_service": "notEvaluated",
            "contact_name": "Mapping and Geographic Information Centre, British Antarctic Survey",
            "contact_email": "magic@bas.ac.uk",
            "temp_extent": "YYYY-MM-DD/YYYY-MM-DD",
        },
    }

    def __init__(self, config: dict):
        """
        Configuration dict must include:

        * endpoint: URL clients will use for access (str)
        * title: catalogue title (str)
        * abstract: catalogue description (str)
        * database_connection_string: PyCSW (SQL Alchemy) connection string (must use Postgres)
        * database_table_table: name of table for storing records (str)
        * auth_required_scopes_read: OAuth scopes required to make record(s) requests (may be empty list)
        * auth_required_scopes_write: OAuth scopes required to make transactional requests (may be empty list)

        Other PyCSW configuration options may not be changed.

        :type config dict
        :param config: PyCSW config subset
        """
        _csw_options = deepcopy(self.base_configuration)
        if "endpoint" in config.keys():
            _csw_options["server"]["url"] = config["endpoint"]
        if "title" in config.keys():
            _csw_options["metadata:main"]["identification_title"] = config["title"]
        if "abstract" in config.keys():
            _csw_options["metadata:main"]["identification_abstract"] = config["abstract"]
        if "database_connection_string" in config.keys():
            _csw_options["repository"]["database"] = config["database_connection_string"]
        if "database_table" in config.keys():
            _csw_options["repository"]["table"] = config["database_table"]

        self._csw_config = _csw_options
        self._csw_auth = {"read": config["auth_required_scopes_read"], "write": config["auth_required_scopes_write"]}

    @property
    def _is_initialised(self) -> bool:
        """
        Tests whether the backing database has been initialised for catalogue

        Checks whether records table used for the catalogue exists, if yes it is assumed to have been initialised.

        :rtype bool
        :return: whether the backing database has been initialised
        """
        csw_database = create_engine(self._csw_config["repository"]["database"])
        return inspect(csw_database).has_table(self._csw_config["repository"]["table"])

    def _check_auth(self, transaction_type: CSWTransactionType, token: Optional[AzureToken]) -> None:
        """
        Checks whether an authorisation token contains the scopes required for a transaction

        I.e. 'is the client allowed to perform the action they're trying to do?'

        `CSWTransactionType` members are simplified to generic 'read' or 'write' permissions. Scopes for these
        permissions are specified by the `auth_required_scopes_read` or `auth_required_scopes_write` class variables
        respectively (see `init()` method).

        If the token does not include the required scopes an exception is raised, otherwise nothing is returned.

        :type transaction_type CSWTransactionType
        :param transaction_type: a CSW transaction type
        :type token AzureToken
        :param token: request authorisation token
        """

        permissions_required = "write"
        if transaction_type == CSWTransactionType.SELECT:
            permissions_required = "read"

        try:
            if len(self._csw_auth[permissions_required]) > 0 and not token.scopes.issuperset(
                set(self._csw_auth[permissions_required])
            ):
                raise CSWAuthInsufficientError() from None
        except AttributeError:
            # noinspection PyComparisonWithNone
            if token is None:
                raise CSWAuthMissingError() from None

    @staticmethod
    def _determine_transaction_type(csw_request: _CSWServer) -> CSWTransactionType:  # noqa: C901
        """
        Determines the CSW transaction type from a CSW request type

        The transaction type is determined from either:
        - the value of a `request` query string parameter
        - the presence of a CSW transaction element (e.g. '<csw:Delete>')
        - the presence of a '<csw:Query>' element

        E.g.:
        - a GET request containing '&request=GetRecordById' query string parameter is a 'SELECT' transaction
        - a POST request containing a '<csw:Query>' element is a 'SELECT' transaction
        - a POST request containing a '<csw:Delete>' element is a 'DELETE' transaction

        Transaction types are represented by the `CSWTransactionType` enumeration. For the purposes of this method,
        transactions include 'SELECT'. Requests such as `GetRecordById` are mapped to a transaction type internally.

        If a transaction type cannot be determined because:

        - _neither_ a 'request' query string parameter or '<csw:Transaction>' element are present in the request:
            - a `CSWUnknownRequestError` exception is raised
        - _both_ a 'request' query string parameter or '<csw:Transaction>' element are present in the request:
            - a `CSWAmbiguousRequestError` exception is raised
        - a 'request' query string parameter (only) is present but its value cannot be mapped to a transaction type:
            - a `CSWUnmappedRequestError` exception is raised

        All of these exceptions should be returned to the user as a 400 Bad Request HTTP error response.

        :type csw_request scar_add_metadata_toolbox.hazmat.pycsw.server.Csw
        :param csw_request: CSW server request
        :rtype CSWTransactionType
        :return: CSW transaction type
        """
        request_transaction_types_mapping: Dict[str, CSWTransactionType] = {
            "GetCapabilities": CSWTransactionType.SELECT,
            "DescribeRecord": CSWTransactionType.SELECT,
            "GetRecords": CSWTransactionType.SELECT,
            "GetRecordById": CSWTransactionType.SELECT,
        }
        request_type: Optional[str] = None
        transaction_type: Optional[CSWTransactionType] = None

        try:
            # '?request=GetRecordById' becomes 'GetRecordById'
            request_type = str(csw_request.kvp["request"])
        except KeyError:
            pass

        if csw_request.requesttype == "POST":
            request_xml = ElementTree(fromstring(csw_request.request))
            if len(request_xml.xpath("/csw:Query", namespaces=csw_namespaces)) > 0:
                transaction_type = CSWTransactionType.SELECT
            elif len(request_xml.xpath("/csw:Transaction/csw:Insert", namespaces=csw_namespaces)) > 0:
                transaction_type = CSWTransactionType.INSERT
            elif len(request_xml.xpath("/csw:Transaction/csw:Update", namespaces=csw_namespaces)) > 0:
                transaction_type = CSWTransactionType.UPDATE
            elif len(request_xml.xpath("/csw:Transaction/csw:Delete", namespaces=csw_namespaces)) > 0:
                transaction_type = CSWTransactionType.DELETE

        if request_type is None and transaction_type is None:
            raise CSWUnknownRequestError() from None

        if request_type is not None and transaction_type is not None:
            raise CSWAmbiguousRequestError() from None

        if transaction_type is not None:
            return transaction_type

        if request_type is not None:
            try:
                return request_transaction_types_mapping[request_type]
            except KeyError:
                raise CSWUnmappedRequestError() from None

    def setup(self) -> None:
        """
        Initialises the backing database for the catalogue

        Convenience method to call the PyCSW admin task for setting up the required database components (tables,
        indexes, triggers, etc.)

        Note: There are currently limitations with using multiple catalogues within one schema. The specific errors
        this causes (which are not fatal) are detected by this method and treated as a false positive. See the project
        README for more information.
        """
        if self._is_initialised:
            raise CSWDatabaseAlreadyInitialisedError()

        try:
            csw_database = create_engine(self._csw_config["repository"]["database"])
            csw_database.execute("SELECT version();")
            csw_database.execute("SELECT PostGIS_Full_Version();")
        except ProgrammingError as e:
            if "ERROR:  function postgis_full_version() does not exist" in e.orig.pgerror:
                raise CSWDatabasePostGISExtensionUnavailableError() from e

        try:
            admin.setup_db(
                database=self._csw_config["repository"]["database"],
                table=self._csw_config["repository"]["table"],
                home=None,
            )
        except ProgrammingError as e:
            # Ignore errors related to PyCSW's limitations with non-namespaced indexes
            if 'ERROR:  relation "fts_gin_idx" already exists' not in e.orig.pgerror:
                raise CSWDatabaseAlreadyInitialisedError() from e
            pass

    def process_request(self, request: Request, token: Optional[AzureToken] = None) -> Response:
        # noinspection GrazieInspection
        """
        Process a CSW request and return a suitable response

        Represents embedding CSW by processing an incoming Flask/HTTP request into a CSW request and returning the CSW
        response as a Flask/HTTP response.

        In addition this method:

        * implements authorisation checks for reading records and using the transactional profile
        * supports HEAD requests by treating them as GET requests and discarding the response body

        :type request Request
        :param request: Flask HTTP request
        :type token AzureToken
        :param token: request authorisation token
        :rtype Response
        :return: Flask HTTP response
        """
        if not self._is_initialised:
            raise CSWDatabaseNotInitialisedError()

        if request.method not in ["HEAD", "GET", "POST"]:
            raise CSWMethodNotSupportedError()

        _csw = _CSWServer(rtconfig=self._csw_config, env=request.environ, version="2.0.2")
        _csw.kvp = request.args.to_dict()
        _csw.requesttype = request.method

        # CSW doesn't natively support HEAD requests so alias to GET
        if request.method == "HEAD":
            _csw.requesttype = "GET"

        if request.method == "POST":
            _csw.request = request.data

        transaction_type = self._determine_transaction_type(csw_request=_csw)
        self._check_auth(transaction_type=transaction_type, token=token)

        status_code, response = _csw.dispatch()

        if request.method == "HEAD":
            return Response(status=status_code)

        return Response(response=response, status=status_code, content_type=_csw.contenttype)


class CSWClient:  # pragma: no cover (until #59 is resolved)
    """
    Represents a CSW Client backed by OWSLib

    This class is largely a wrapper around the OWSLib CSW class in order to abstract away CSW or OWSLib specific
    details (such as needing to known to use the `getRecords2` method for example).

    Other features include:
    * raising exceptions for errors
    * support for token based authentication
    * workaround to fix transactional update results count error
    * compatibility with this application's CSWServer class for error handling
    * compatibility with this application's Repository class for setting CSW configuration options

    Note: This class uses classes from the Hazardous Materials module. This is to work around limitations in the OWSLib
    package. This will be addressed by upstreaming missing functionality or creating a derivative package.
    """

    def __init__(self, config: dict):
        """
        Configuration dict must include:

        * endpoint: URL to CSW service (str)
        * auth: parameters for CSW authentication object (may be empty dict)

        Other OWSLib configuration options may also be included.

        :type config: dict
        :param config: CSW (OWSLib) configuration options
        """
        self._csw_config = config
        self._csw_endpoint = config["endpoint"]
        self._csw_auth = CSWAuth(**config["auth"])
        del self._csw_config["endpoint"]
        del self._csw_config["auth"]

    def __repr__(self):
        return f"<CSWClient / Endpoint: {self._csw_endpoint}>"

    def _get_client(self) -> _CSWClient:
        """
        Creates a OWSLib CSW client instance

        A separate CSW instance is used for each action (read/transaction), rather using a class instance singleton, as
        OWSLib will attempt to retrieve the CSW GetCapabilities response on instantiation. This behaviour can result in
        errors where CSW endpoints may not yet exist for example.

        Due to the behaviour of OWSLib, auth errors emanating from the Flask Azure OAuth provider (used to secure CSW
        server instances) trigger a ServiceException before the relevant action is taken, and so must be caught here.

        Note: This method currently uses a modified class from the hazardous materials classes.

        :rtype CatalogueServiceWeb
        :return: OWSLib CSW client (modified)
        """
        try:
            return _CSWClient(self._csw_endpoint, auth=self._csw_auth, **self._csw_config)
        except ServiceException:
            raise CSWAuthError() from None

    def get_record(self, identifier: str, mode: CSWGetRecordMode = CSWGetRecordMode.FULL) -> str:
        """
        Return a single record

        CSW supports returning full/complete records or summary versions with more specific elements. Formally CSW
        refers to these as Element Set Names, this method refers to this as the (record) mode. Options are described by
        the CSWGetRecordMode enumeration.

        Note: If 'brief' records are requested, a fixer method from the hazardous materials classes is used.

        :type identifier str
        :param identifier: ISO 19115 file identifier
        :type mode CSWGetRecordMode
        :param mode: CSW record mode (element set name)
        :rtype str
        :return: ISO 19115-2 record encoded as an XML string
        """
        _csw = self._get_client()
        try:
            _csw.getrecordbyid(id=[identifier], esn=mode.value, outputschema="http://www.isotc211.org/2005/gmd")
            if len(_csw.records) != 1:
                raise RecordNotFoundError()
            return _csw.records[identifier].xml.decode()
        except HTTPError as e:
            if e.response.content.decode() == "Catalogue not yet available.":
                raise CSWDatabaseNotInitialisedError() from None
            raise HTTPError(e) from e
        except XMLSyntaxError:
            if _csw.response.decode() == "Missing authorisation token.":
                raise CSWAuthMissingError() from None
            elif _csw.response.decode() == "Insufficient authorisation token.":
                raise CSWAuthInsufficientError() from None

    def get_records(self, mode: CSWGetRecordMode = CSWGetRecordMode.FULL) -> Generator[str, None, None]:
        """
        Return all records

        Returns all records in a CSW catalogue, i.e. search/filtering options are not yet supported.

        CSW supports returning full/complete records or summary versions with more specific elements. Formally CSW
        refers to these as Element Set Names, this method refers to this as the (record) mode. Options are described by
        the CSWGetRecordMode enumeration.

        Note: If 'brief' records are requested, a fixer method from the hazardous materials classes is used.

        :type mode CSWGetRecordMode
        :param mode: CSW record mode (element set name)
        :rtype list
        :return: list of ISO 19115-2 records encoded as XML strings
        """
        _csw = self._get_client()
        try:
            _csw.getrecords2(
                typenames="gmd:MD_Metadata",
                esn=mode.value,
                resulttype="results",
                outputschema="http://www.isotc211.org/2005/gmd",
                maxrecords=100,
            )
            for raw_record in _csw.records.values():
                if isinstance(raw_record.xml, bytes):
                    raw_record.xml = raw_record.xml.decode()
                if mode == CSWGetRecordMode.BRIEF:
                    raw_record.xml = self._convert_csw_brief_gmd_to_gmi_xml(record_xml=raw_record.xml)

                raw_record_xml = raw_record.xml.replace("</csw:SearchResults>", "")
                raw_record_xml = raw_record_xml.replace("</csw:GetRecordsResponse>", "")
                yield raw_record_xml
        except HTTPError as e:
            if e.response.content.decode() == "Catalogue not yet available.":
                raise CSWDatabaseNotInitialisedError() from e
        except XMLSyntaxError:
            if _csw.response.decode() == "Missing authorisation token.":
                raise CSWAuthMissingError() from None
            elif _csw.response.decode() == "Insufficient authorisation token.":
                raise CSWAuthInsufficientError() from None

    def insert_record(self, record: str) -> None:
        """
        Inserts a new record

        Uses the CSW transactional profile to insert a new record into a CSW catalogue.

        Note: If a record with the same IS0 19115 file identifier exists it will be considered a duplicate of an
        existing record and result in a conflict error. To update an existing record, including changing its file
        identifier, use the `update_record()` method.

        :type record str
        :param record: ISO 19115-2 record encoded as an XML string
        """
        _csw = self._get_client()
        try:
            _csw.transaction(ttype=CSWTransactionType.INSERT.value, typename="gmd:MD_Metadata", record=record)
            if len(_csw.results["insertresults"]) != 1:
                raise RecordServerError() from None
        except ExceptionReport:
            raise RecordInsertConflictError() from None
        except HTTPError as e:
            if e.response.content.decode() == "Catalogue not yet available.":
                raise CSWDatabaseNotInitialisedError() from e
        except XMLSyntaxError:
            if _csw.response.decode() == "Missing authorisation token.":
                raise CSWAuthMissingError() from None
            elif _csw.response.decode() == "Insufficient authorisation token.":
                raise CSWAuthInsufficientError() from None

    def update_record(self, record: str) -> None:
        """
        Updates an existing record

        Uses the CSW transactional profile to update an existing record in a CSW catalogue.

        This method requires complete/replacement records, partial record updates are not supported.

        :type record str
        :param record: ISO 19115-2 record encoded as an XML string
        """
        _csw = self._get_client()
        try:
            _csw.transaction(ttype=CSWTransactionType.UPDATE.value, typename="gmd:MD_Metadata", record=record)
            # Workaround for https://github.com/geopython/OWSLib/issues/678
            _csw.results["updated"] = int(
                ElementTree(fromstring(_csw.response)).xpath(
                    "/csw:TransactionResponse/csw:TransactionSummary/csw:totalUpdated/text()",
                    namespaces=csw_namespaces,
                )[0]
            )
            if _csw.results["updated"] != 1:
                raise RecordServerError() from None
        except HTTPError as e:
            if e.response.content.decode() == "Catalogue not yet available.":
                raise CSWDatabaseNotInitialisedError() from e
        except XMLSyntaxError:
            if _csw.response.decode() == "Missing authorisation token.":
                raise CSWAuthMissingError() from None
            elif _csw.response.decode() == "Insufficient authorisation token.":
                raise CSWAuthInsufficientError() from None

    def delete_record(self, identifier: str) -> None:
        """
        Deletes an existing record

        Uses the CSW transactional profile to delete an existing record from a CSW catalogue.

        :type identifier str
        :param identifier: ISO 19115 file identifier
        """
        _csw = self._get_client()
        try:
            _csw.transaction(ttype=CSWTransactionType.DELETE.value, identifier=identifier)
            _csw.results["deleted"] = int(
                ElementTree(fromstring(_csw.response)).xpath(
                    "/csw:TransactionResponse/csw:TransactionSummary/csw:totalDeleted/text()",
                    namespaces=csw_namespaces,
                )[0]
            )
            # noinspection PyTypeChecker
            if _csw.results["deleted"] != 1:
                raise RecordServerError() from None
        except HTTPError as e:
            if e.response.content.decode() == "Catalogue not yet available.":
                raise CSWDatabaseNotInitialisedError() from e
        except XMLSyntaxError:
            if _csw.response.decode() == "Missing authorisation token.":
                raise CSWAuthMissingError() from None
            elif _csw.response.decode() == "Insufficient authorisation token.":
                raise CSWAuthInsufficientError() from None

    @staticmethod
    def _convert_csw_brief_gmd_to_gmi_xml(record_xml: str) -> str:
        """
        Convert CSW GetRecord(s) requests using the 'brief' element set name from ISO-19115(-0) to ISO 19115-2

        Where GetRecord or GetRecords requests use element set names other than 'full', PyCSW needs to derive
        summarised representations of records. As the PyCSW profile for ISO 19115 was written for the original ISO
        19115:2003 standard, derived representations use this version. This is an issue if newer editions of 19115 are
        used, notably 19115-2 and 19115-3 (19115-1).

        As the BAS Metadata Library is sensitive to each edition (as the namespace and elements differ between
        editions), this means that a 'brief' version of an ISO 19115-2 record can't be parsed as it will use the ISO
        19115 namespace (GMD rather than GMI).

        To prevent needing to use different edition implementations depending on the element set used, this method
        will 'covert' a record using the GMD namespace to the GMI namespace. This is a crude conversion, as it simply
        creates a new root level element (using the GMI namespace) and copies all direct children of the original GMD
        root element.

        The effect is to replace the root element with the expected namespace to allow records to be parsed as
        expected. This is possible because ISO 19115-2 is a superset and extension of the original ISO 19115 standard.
        It would not be possible to do this in the same way with ISO 19115-3, as it uses a different conceptual model.
        """
        iso_ns = Namespaces()

        gmd_xml_element = ElementTree(fromstring(record_xml))
        gmd_sub_elements = gmd_xml_element.getroot().xpath("/gmd:MD_Metadata/*", namespaces=iso_ns.namespace_dict)
        gmi_xml_element = Element(
            f"{{{iso_ns.get_namespace('gmi')}}}MI_Metadata",
            nsmap=iso_ns.namespace_dict,
        )
        for gmd_sub_element in gmd_sub_elements:
            gmi_xml_element.append(gmd_sub_element)

        record_xml = tostring(
            ElementTree(gmi_xml_element),
            pretty_print=True,
            xml_declaration=False,
            encoding="utf-8",
        )
        return record_xml.decode()
