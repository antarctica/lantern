from copy import deepcopy
from enum import Enum
from typing import List, Optional

# noinspection PyPackageRequirements
# Exempting Bandit security issue (Using Element to parse untrusted XML data is known to be vulnerable to XML attacks)
#
# We don't currently allow untrusted/user-provided XML so this is not a risk
from lxml.etree import ElementTree, fromstring, XMLSyntaxError  # nosec
from flask import Request, Response
from owslib.ows import ExceptionReport
from owslib.util import ServiceException
from pycsw.core import admin
from owslib.csw import namespaces as csw_namespaces
from requests import HTTPError
from sqlalchemy import create_engine
from sqlalchemy.exc import ProgrammingError
from flask_azure_oauth import AzureToken

from scar_add_metadata_toolbox.hazmat.csw import (
    CSWClient as _CSWClient,
    CSWServer as _CSWServer,
    convert_csw_brief_gmd_to_gmi_xml,
    CSWAuth,
)


class CSWGetRecordMode(Enum):
    """
    Represents the element set names used in the CSW specification
    """

    FULL = "full"
    SUMMARY = "summary"
    BRIEF = "brief"


class CSWTransactionType(Enum):
    """
    Represents the transaction types used in the CSW specification
    """

    INSERT = "insert"
    UPDATE = "update"
    DELETE = "delete"


class CSWDatabaseAlreadyInitialisedException(Exception):
    """
    Represents a situation whereby a CSW Server's backing database has already been initialised

    Backing databases must only be initialised once to avoid errors creating duplicate structures or unwanted side
    effects such as table truncation. If a database is initialised multiple times this role would be violated.
    """

    pass


class CSWDatabaseNotInitialisedException(Exception):
    """
    Represents a situation where the backing database for a CSW Server has not yet been initialised

    Backing databases must be initialised to ensure relevant database structures, indexes and triggers exist and are
    configured before records are written or read from a catalogue. If requests are made to a CSW server before has
    happened this rule would be violated. The relevant initialisation method can be ran to resolve this.
    """

    pass


class CSWMethodNotSupportedException(Exception):
    """
    Represents a situation where an unsupported HTTP method is used in a request to a CSW Server

    CSW requests must use the HEAD, GET or POST HTTP method. If another method is used this rule would be violated.
    """

    pass


class CSWAuthException(Exception):
    """
    Represents a situation where there the authentication information included in a CSW request causes an error

    This is a non-specific error and could indicate a range of situations, such as a token having expired or being
    malformed.
    """

    pass


class CSWAuthMissingException(Exception):
    """
    Represents a situation where authentication information is required for a CSW request but was not included

    Requests to authenticated CSW requests must include authentication information. If this is missing this rule would
    be violated.
    """

    pass


class CSWAuthInsufficientException(Exception):
    """
    Indicates a situation where the authorisation requirements for a CSW request are not satisfied by the information
    included in the request

    Requests to authorised CSW requests must include authorisation information that satisfies all the requirements of
    the resource or action being requested. If any of these requirements are not met this rule would be violated.

    Typically this error relates to missing scopes/roles that are required by the resource or action being requested.
    E.g. to publish a record the Publish scope/role is required.
    """

    pass


class RecordServerException(Exception):
    """
    Represents a situation where a record server encounters an error processing a request

    This is a non-specific error and could indicate a range of situations, such as a record being malformed or an
    internal error within record server.
    """

    pass


class RecordNotFoundException(Exception):
    """
    Represents a situation where a given record does not exist
    """

    pass


class RecordInsertConflictException(Exception):
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
            "logfile": "/dev/null",
            "pretty_print": "true",
            "gzip_compresslevel": "8",
            "domainquerytype": "list",
            "domaincounts": "false",
            "profiles": "apiso",
        },
        "manager": {"transactions": "true", "allowed_ips": "*.*.*.*",},
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
        * database_connection_string: PyCSW (SQL Alchemy) connection string (must use PostgreSQL)
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
        return csw_database.dialect.has_table(csw_database, self._csw_config["repository"]["table"])

    def _check_auth(self, method: str, token: Optional[AzureToken]) -> None:
        """
        Checks whether an authorisation token contains all of a required set of scopes

        I.e. is the client allowed to perform the action they're trying to do.

        Currently actions are simplified to 'read' or 'write' and the required set of scopes is specified by the
        'auth_required_scopes_read' or 'auth_required_scopes_write' class config options.

        If the token does not include the required scopes an exception is raised, otherwise nothing is returned.

        :type method str
        :param method: either 'read' or 'write'
        :type token AzureToken
        :param token: request authorisation token
        """
        try:
            if len(self._csw_auth[method]) > 0 and not token.scopes.issuperset(set(self._csw_auth[method])):
                raise CSWAuthInsufficientException()
        except AttributeError:
            # noinspection PyComparisonWithNone
            if token == None:
                raise CSWAuthMissingException()

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
            raise CSWDatabaseAlreadyInitialisedException()

        csw_database = create_engine(self._csw_config["repository"]["database"])
        csw_database.execute("SELECT version();")

        try:
            admin.setup_db(
                database=self._csw_config["repository"]["database"],
                table=self._csw_config["repository"]["table"],
                home=None,
            )
        except ProgrammingError as e:
            # Ignore errors related to PyCSW's limitations with non-namespaced indexes
            if 'ERROR:  relation "fts_gin_idx" already exists' not in e.orig.pgerror:
                raise CSWDatabaseAlreadyInitialisedException()
            pass

    def process_request(self, request: Request, token: Optional[AzureToken] = None) -> Response:
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
            raise CSWDatabaseNotInitialisedException()

        if request.method != "HEAD" and request.method != "GET" and request.method != "POST":
            raise CSWMethodNotSupportedException()

        _csw = _CSWServer(rtconfig=self._csw_config, env=request.environ, version="2.0.2")
        _csw.requesttype = "GET"
        _csw.kvp = request.args.to_dict()
        _request_type = "inspect"

        if request.method == "POST":
            _request_type = "read"
            _csw.requesttype = "POST"
            _csw.request = request.data

            request_xml = ElementTree(fromstring(_csw.request))
            if len(request_xml.xpath("/csw:Transaction/csw:Insert", namespaces=csw_namespaces)) > 0:
                _request_type = "create"
            elif len(request_xml.xpath("/csw:Transaction/csw:Update", namespaces=csw_namespaces)) > 0:
                _request_type = "update"
            elif len(request_xml.xpath("/csw:Transaction/csw:Delete", namespaces=csw_namespaces)) > 0:
                _request_type = "delete"

        if _request_type == "read":
            self._check_auth(method="read", token=token)
        elif _request_type == "create" or _request_type == "update" or _request_type == "delete":
            self._check_auth(method="write", token=token)

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
    * compatibility with this applications CSWServer class for error handling
    * compatibility with this applications Repository class for setting CSW configuration options

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
            raise CSWAuthException()

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
                raise RecordNotFoundException()
            return _csw.records[identifier].xml.decode()
        except HTTPError as e:
            if e.response.content.decode() == "Catalogue not yet available.":
                raise CSWDatabaseNotInitialisedException()
        except XMLSyntaxError:
            if _csw.response.decode() == "Missing authorisation token.":
                raise CSWAuthMissingException()
            elif _csw.response.decode() == "Insufficient authorisation token.":
                raise CSWAuthInsufficientException()

    def get_records(self, mode: CSWGetRecordMode = CSWGetRecordMode.FULL) -> List[str]:
        """
        Return all records

        Currently returns all records in a CSW catalogue, i.e. search/filtering options are not yet supported.

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
                    raw_record.xml = convert_csw_brief_gmd_to_gmi_xml(record_xml=raw_record.xml)
                yield raw_record.xml
        except HTTPError as e:
            if e.response.content.decode() == "Catalogue not yet available.":
                raise CSWDatabaseNotInitialisedException()
        except XMLSyntaxError:
            if _csw.response.decode() == "Missing authorisation token.":
                raise CSWAuthMissingException()
            elif _csw.response.decode() == "Insufficient authorisation token.":
                raise CSWAuthInsufficientException()

    def insert_record(self, record: str) -> None:
        """
        Inserts a new record

        Uses the CSW transactional profile to insert a new record into a CSW catalogue.

        Note: If a record with the same IS0 19115 file identifier exists it will be considered a duplicate of an
        existing record and result in a conflict error. To update an existing record, including changing it's file
        identifier, use the `update_record()` method.

        :type record str
        :param record: ISO 19115-2 record encoded as an XML string
        """
        _csw = self._get_client()
        try:
            _csw.transaction(ttype=CSWTransactionType.INSERT.value, typename="gmd:MD_Metadata", record=record)
            if len(_csw.results["insertresults"]) != 1:
                raise RecordServerException()
        except ExceptionReport:
            raise RecordInsertConflictException()
        except HTTPError as e:
            if e.response.content.decode() == "Catalogue not yet available.":
                raise CSWDatabaseNotInitialisedException()
        except XMLSyntaxError:
            if _csw.response.decode() == "Missing authorisation token.":
                raise CSWAuthMissingException()
            elif _csw.response.decode() == "Insufficient authorisation token.":
                raise CSWAuthInsufficientException()

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
                raise RecordServerException()
        except HTTPError as e:
            if e.response.content.decode() == "Catalogue not yet available.":
                raise CSWDatabaseNotInitialisedException()
        except XMLSyntaxError:
            if _csw.response.decode() == "Missing authorisation token.":
                raise CSWAuthMissingException()
            elif _csw.response.decode() == "Insufficient authorisation token.":
                raise CSWAuthInsufficientException()

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
                raise RecordServerException()
        except HTTPError as e:
            if e.response.content.decode() == "Catalogue not yet available.":
                raise CSWDatabaseNotInitialisedException()
        except XMLSyntaxError:
            if _csw.response.decode() == "Missing authorisation token.":
                raise CSWAuthMissingException()
            elif _csw.response.decode() == "Insufficient authorisation token.":
                raise CSWAuthInsufficientException()
