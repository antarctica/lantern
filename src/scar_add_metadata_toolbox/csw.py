from __future__ import annotations

import contextlib
import json
from collections.abc import Generator
from copy import deepcopy
from enum import Enum
from pathlib import Path
from tempfile import TemporaryDirectory

from authlib.oauth2.rfc6749.resource_protector import TokenValidator
from bas_metadata_library.standards.iso_19115_2 import MetadataRecord
from dulwich import porcelain
from dulwich.client import HTTPUnauthorized
from dulwich.errors import NotGitRepository
from flask import Request, Response
from flask_entra_auth.token import EntraToken
from lxml.etree import (
    Element,
    ElementTree,
    XMLSyntaxError,
    fromstring,
    tostring,
)
from requests import HTTPError
from sqlalchemy import create_engine, inspect
from sqlalchemy.exc import ProgrammingError

from scar_add_metadata_toolbox.hazmat.owslib.csw import CatalogueServiceWeb as _CSWClient
from scar_add_metadata_toolbox.hazmat.owslib.csw import namespaces as csw_namespaces
from scar_add_metadata_toolbox.hazmat.owslib.namespaces import Namespaces
from scar_add_metadata_toolbox.hazmat.owslib.ows import ExceptionReport
from scar_add_metadata_toolbox.hazmat.owslib.util import Authentication as CSWAuth
from scar_add_metadata_toolbox.hazmat.owslib.util import ServiceException
from scar_add_metadata_toolbox.hazmat.pycsw.core import admin
from scar_add_metadata_toolbox.hazmat.pycsw.server import Csw as _CSWServer


class CSWGetRecordMode(Enum):
    """Represents the element set names used in the CSW specification."""

    FULL = "full"
    SUMMARY = "summary"
    BRIEF = "brief"


class CSWTransactionType(Enum):
    """
    Represents the transaction types used in the CSW specification.

    Plus a 'SELECT' value to represent retrieval only requests.
    """

    SELECT = "select"
    INSERT = "insert"
    UPDATE = "update"
    DELETE = "delete"


class CSWDatabaseAlreadyInitialisedError(Exception):
    """
    Represents a situation whereby a CSW Server's backing database has already been initialised.

    Backing databases must only be initialised once to avoid errors creating duplicate structures or unwanted side
    effects such as table truncation. If a database is initialised multiple times this rule would be violated.
    """

    pass


class CSWDatabaseNotInitialisedError(Exception):
    """
    Represents a situation where the backing database for a CSW Server has not yet been initialised.

    Backing databases must be initialised to ensure relevant database structures, indexes and triggers exist and are
    configured before records are written to or read from a catalogue. If requests are made to a CSW server before has
    happened this rule would be violated. The relevant initialisation method can be run to resolve this.
    """

    pass


class CSWDatabasePostGISExtensionUnavailableError(Exception):
    """
    Represents a situation where the backing database or a CSW Server does not have the PostGIS extension enabled.

    Backing databases must have this extension to support spatial querying as part of the CSW standard (e.g. searching
    by bounding box). If the PyCSW admin database setup method is called without this extension available, it will
    attempt to use a workaround which leads to problems with creating duplicate tables.
    """

    pass


class CSWMethodNotSupportedError(Exception):
    """
    Represents a situation where an unsupported HTTP method is used in a request to a CSW Server.

    CSW requests must use the HEAD, GET or POST HTTP method. If another method is used this rule would be violated.
    """

    pass


class CSWUnknownRequestError(Exception):
    """
    Represents a situation where a CSW request doesn't contain a property describing the type of request.

    E.g. for GET requests, a 'request' string query parameter is not included, or in Post requests, there isn't a
    recognised element that can mapped to a request type (e.g. a '<csw:Query>' element can be mapped to a 'query' type).

    It is inherently hard to be specific about how to resolve this error. As we take a restrictive approach to detecting
    request types, it's possible the request made by the client is perfectly valid but not yet supported by us.
    """

    pass


class CSWAmbiguousRequestError(Exception):
    """
    Represents a situation where a CSW request contains multiple properties describing the type of request.

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
    Represents a situation where a CSW request contains an invalid transaction request type.

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
    Represents a situation where there the authentication information included in a CSW request causes an error.

    This is a non-specific error and could indicate a range of situations, such as a token having expired or being
    malformed.
    """

    pass


class CSWAuthMissingError(Exception):
    """
    Represents a situation where authentication information is required for a CSW request but was not included.

    Requests to authenticated CSW requests must include authentication information. If this is missing this rule would
    be violated.
    """

    pass


class CSWAuthInsufficientError(Exception):
    """
    Indicates a situation where the authorisation requirements for a CSW request are not satisfied by the request.

    Requests to authorised CSW requests must include authorisation information that satisfies all the requirements of
    the resource or action being requested. If any of these requirements are not met this rule would be violated.

    Usually this error relates to missing scopes/roles that are required by the resource or action being requested.
    E.g. to publish a record the 'Publish' scope/role is required.
    """

    pass


class CSWTrackingRepositoryAlreadyInitialisedError(Exception):
    """
    Represents a situation whereby a CSW Server's revision tracking backing git repository has already been initialised.

    Backing repositories must only be initialised once to avoid loosing revision information. If a repository is
    initialised multiple times this rule would be violated.
    """

    pass


class CSWTrackingRepositoryInvalidCredentialsError(Exception):
    """
    Represents a situation where credentials used interact for a backing git repository remote are invalid.

    This is a non-specific error and could indicate a range of situations, such as missing credentials (not set),
    invalid credentials (e.g. typos), authorisation issues (e.g. valid credentials but not allowed to perform action)
    or other, service specific, errors (e.g. account lockout, etc.).
    """

    pass


class CSWTrackingRepositoryNotEnabledError(Exception):
    """
    Represents a situation where a backing git repository is set up for a CSW Server with revision tracking disabled.

    Revision tracking is an optional feature and must be enabled to set up a backing git repository. Setting up a
    backing repository where this feature is disabled would violate this rule. If appropriate, this error can be
    resolved by enabling this feature in the catalogue config.
    """

    pass


class CSWTrackingRepositoryNotInitialisedError(Exception):
    """
    Represents a situation where the backing git repository for a CSW Server with revision tracking is not initialised.

    Backing repositories must be initialised to ensure relevant git structures, remotes and branches exist and are
    configured before records are written to a catalogue. If requests are made to a CSW server before has
    happened this rule would be violated. The relevant initialisation method can be run to resolve this.
    """

    pass


class RecordServerError(Exception):
    """
    Represents a situation where a record server encounters an error processing a request.

    This is a non-specific error and could indicate a range of situations, such as a record being malformed or an
    internal error within record server.
    """

    pass


class RecordNotFoundError(Exception):
    """Represents a situation where a given record does not exist."""

    pass


class RecordInsertConflictError(Exception):
    """
    Represents a situation where a record to be inserted already exists in a repository.

    Records in repositories must be unique. If a record is inserted with the same identifier as an existing record,
    neither record not be unique and this rule would be violated. Records may be updated instead.
    """

    pass


class CSWServer:  # pragma: no cover (until #59 is resolved)
    """
    Represents a CSW Server backed by PyCSW.

    This class is largely a wrapper around the PyCSW class in order to improve integrating CSW functionality within
    a larger application, and to add additional functionality including:

    * raising exceptions for errors
    * support for token based authentication
    * support for performing/reporting backing database initialisation
    * support for tracking revisions to records in a Git repository
    * simplifying PyCSW configuration options using a base configuration

    Note: This class uses classes from the Hazardous Materials module. This is to work around limitations in PyCSW.
    """

    base_configuration: dict = {  # noqa: RUF012
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

    base_auth_configuration: dict[str, list[str]] = {"read": [], "write": []}  # noqa: RUF012

    base_tracking_configuration: dict[str, bool | str | Path | None] = {  # noqa: RUF012
        "enabled": False,
        "working_dir": None,
        "remote_url": None,
        "branch": "main",
        "committer_identity": "SCAR ADD Metadata Toolbox Records Tracking Bot <magic+add-cat-rec-trac@bas.ac.uk>",
        "gitlab_pat": None,
    }

    def __init__(self, config: dict) -> None:
        """
        Initialise a CSW Server instance.

        Configuration dict must include:
        * 'endpoint': URL clients will use for access (str)
        * 'title': catalogue title (str)
        * 'abstract': catalogue description (str)
        * 'database_connection_string': PyCSW (SQL Alchemy) connection string (must use Postgres)
        * 'database_table_table': name of table for storing records (str)

        Note: Other PyCSW configuration options may not be changed.

        Configuration options for other, optional, features should be provided in the same configuration dict:

        For authentication/authorisation:
        * 'auth_required_scopes_read': OAuth scopes required to make record(s) requests (maybe empty list)
        * 'auth_required_scopes_write': OAuth scopes required to make transactional requests (maybe empty list)

        For revision tracking:
        * `tracking_enabled`: whether revision tracking is enabled for a catalogue
        * 'tracking_working_dir': path to working directory (git working copy) used for storing versioned records
        * 'tracking_remote_url': URL to git remote commits for revision tracking are pushed to
        * 'tracking_branch': git branch used for revision tracking (conventionally 'main')
        * 'tracking_committer_identity': name and email used for the committer (not author) identity in git commits
        * 'tracking_gitlab_pat': GitLab Personal Access Token used to authenticate pushing commits to git remote

        :type config dict
        :param config: PyCSW config subset
        """
        self._csw_config = self._init_csw_config(config=config)
        self._auth_config = self._init_auth_config(config=config)
        self._tracking_config = self._init_tracking_config(config=config)

    @property
    def _backing_db_is_initialised(self) -> bool:
        """
        Test whether the backing database has been initialised for catalogue.

        Checks whether records table used for the catalogue exists, if yes it is assumed to have been initialised.

        :rtype bool
        :return: whether the backing database has been initialised
        """
        csw_database = create_engine(self._csw_config["repository"]["database"])
        return inspect(csw_database).has_table(self._csw_config["repository"]["table"])

    @property
    def _backing_repo_is_initialised(self) -> bool:
        """
        Test whether the backing git repository has been initialised for catalogue revision tracking.

        Checks whether the active local branch, and the branch in the current remote, match the expected branch.
        If yes, it is assumed to have been initialised.

        :rtype bool
        :return: whether backing git repository has been initialised
        """
        try:
            return bool(
                porcelain.active_branch(repo=self._tracking_repo).decode() == self._tracking_config["branch"]
                and f"refs/heads/{self._tracking_config['branch']}".encode()
                in porcelain.fetch(
                    repo=self._tracking_repo,
                    remote_location="origin",
                    depth=0,
                    username="gitlab-ci-token",
                    password=self._tracking_config["gitlab_pat"],
                ).refs
            )
        except NotGitRepository:
            return False

    @property
    def _tracking_enabled(self) -> bool:
        """
        Convenience property for determining if revision tracking is enabled.

        :rtype bool
        :return: whether revision tracking is enabled
        """
        return self._tracking_config["enabled"]

    @property
    def _tracking_repo(self) -> str:
        """
        Convenience property for the git working copy used if revision tracking is enabled.

        This property is the file system directory containing the '.git' directory (as a string), which is used by
        Dulwich/Porcelain's functional methods - i.e. it isn't a special kind of Repository object etc.

        :rtype str
        :return: path to git working copy
        """
        return str(self._tracking_config["working_dir"])

    @staticmethod
    def _format_commit_author(token: EntraToken) -> str:
        """
        Format author information for a git commit message from the authenticated use.

        Author information uses the form `{name} <{email}>`. These values are taken from the current OAuth token via
        claims provided by Azure Active Directory.
        """
        return f"{token.claims['given_name']} {token.claims['family_name']} <{token.claims['email']}>"

    @staticmethod
    def _request_record(csw_request: str) -> str:
        """
        Extract the metadata record from a CSW transactional request.

        The record will be wrapped in a CSW Transaction element (plus others), which all need to be stripped off.

        Note: this method assumes a CSW transactional request, and assumes the payload of this request uses ISO 19115-2.

        :type csw_request str
        :param csw_request: body of the PyCSW request
        :rtype str
        :return: metadata record as a string
        """
        record = ElementTree(fromstring(csw_request.encode())).xpath("//gmi:MI_Metadata", namespaces=csw_namespaces)[0]  # noqa: S320
        return tostring(record).decode()

    @staticmethod
    def _request_record_file_identifier(csw_request: str) -> str:
        """
        Extract the file identifier for the metadata record in a CSW transactional request.

        Depending on the type of CSW request, this identifier may be contained in an ISO 'fileIdentifier' element or a
        DCAT 'identifier' element.

        :type csw_request str
        :param csw_request: body of the PyCSW request
        :rtype str
        :return: file identifier as a string
        """
        return str(
            ElementTree(fromstring(csw_request.encode())).xpath(  # noqa: S320
                "//gmd:fileIdentifier/gco:CharacterString/text() | "
                "//ogc:Filter/ogc:PropertyIsEqualTo[ogc:PropertyName/text() = 'dc:identifier']/ogc:Literal/text() | "
                "//ogc:Filter/ogc:PropertyIsLike[ogc:PropertyName/text() = 'dc:identifier']/ogc:Literal/text()",
                namespaces=csw_namespaces,
            )[0]
        )

    @staticmethod
    def _transaction_type(csw_request: _CSWServer) -> CSWTransactionType:  # noqa: C901
        """
        Determine the CSW transaction type from a CSW request type.

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
        request_transaction_types_mapping: dict[str, CSWTransactionType] = {
            "GetCapabilities": CSWTransactionType.SELECT,
            "DescribeRecord": CSWTransactionType.SELECT,
            "GetRecords": CSWTransactionType.SELECT,
            "GetRecordById": CSWTransactionType.SELECT,
        }
        # noinspection PyUnusedLocal
        request_type: str | None = None
        transaction_type: CSWTransactionType | None = None

        # '?request=GetRecordById' becomes 'GetRecordById'
        with contextlib.suppress(KeyError):
            request_type = str(csw_request.kvp["request"])

        if csw_request.requesttype == "POST":
            request_xml = ElementTree(fromstring(csw_request.request))  # noqa: S320
            if (
                len(request_xml.xpath("/csw:DescribeRecord", namespaces=csw_namespaces)) > 0
                or len(request_xml.xpath("/csw:GetRecords", namespaces=csw_namespaces)) > 0
                or len(request_xml.xpath("/csw:Query", namespaces=csw_namespaces)) > 0
            ):
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

        if request_type is not None:  # noqa: RET503
            try:
                return request_transaction_types_mapping[request_type]
            except KeyError:
                raise CSWUnmappedRequestError() from None

    def _check_auth(self, transaction_type: CSWTransactionType, token: EntraToken | None) -> None:
        """
        Check whether an authorisation token contains the scopes required for a transaction.

        I.e. 'is the client allowed to perform the action they're trying to do?'

        `CSWTransactionType` members are simplified to generic 'read' or 'write' permissions. Scopes for these
        permissions are specified by the `auth_required_scopes_read` or `auth_required_scopes_write` class variables
        respectively (see `init()` method).

        If the token does not include the required scopes an exception is raised, otherwise nothing is returned.
        """
        permissions_required = "write"
        if transaction_type == CSWTransactionType.SELECT:
            permissions_required = "read"

        required_scopes = self._auth_config[permissions_required]

        if len(required_scopes) == 0:
            return

        if token is None:
            raise CSWAuthMissingError() from None

        validator = TokenValidator()
        if not validator.scope_insufficient(token_scopes=token.scopes, required_scopes=required_scopes):
            raise CSWAuthInsufficientError() from None

    def _create_tracking_repo(self) -> None:
        """
        Create the git repository used for catalogue revision tracking.

        The git repository is created in a temporary directory rather than the configured working directory to avoid
        differences in behaviour between setting up a repository for the first time (which is only done once), and
        setting up a repository by cloning it from a remote location (which is done every other time).

        I.e. Except for the very first time, setting up a revision tracking is actually setting a local instance of an
        existing repository by cloning it from an existing remote.

        That, much more common, case is covered by the `_clone_tracking_repo()` method. This method covers the one-off,
        initial, case where the remote does not yet exist.

        Steps performed:
        * new repository initialised, and a hard-coded 'origin' remote added
        * a default README file created (to give basic information about the repo, and for content in an initial commit)
        * README file is staged and committed, using an internal author (i.e. app as author rather than user of the app)
        * new branch is created and switched to (as repo is always created with 'master' as default branch name)
        *
        """
        readme_content = """
# SCAR ADD Metadata Toolbox - Revision Tracking Repository

This repository is used to track revisions to metadata records contained in the Unpublished CSW catalogue,
within the [SCAR ADD Metadata Toolbox](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/) project.
See the [CSW Revision Tracking](https://gitlab.data.bas.ac.uk/MAGIC/add-metadata-toolbox/-/blob/main/README.md#user-content-csw-revision-tracking)
subsection for specific information relating to this repository and
its use.

**Note:** This repository is designed to be exclusively managed by the Metadata Toolbox project and
**MUST NOT** be modified outside of this tool."""
        initial_commit_message = "Initial commit; Adding README."

        with TemporaryDirectory() as temp_dir:
            repo = porcelain.init(path=temp_dir)
            porcelain.remote_add(repo=repo, name="origin", url=self._tracking_config["remote_url"])

            readme_path = Path(temp_dir).joinpath("README.md")
            with readme_path.open(mode="w") as readme_file:
                readme_file.write(readme_content)

            porcelain.add(repo=repo, paths=str(readme_path))
            porcelain.commit(
                repo=repo,
                message=initial_commit_message,
                committer=self._tracking_config["committer_identity"],
                author=self._tracking_config["committer_identity"],
            )

            porcelain.branch_create(repo=repo, name=self._tracking_config["branch"])
            porcelain.update_head(repo=repo, target=self._tracking_config["branch"])

            porcelain.push(
                repo=repo,
                remote_location="origin",
                refspecs=self._tracking_config["branch"],
                username="gitlab-ci-token",
                password=self._tracking_config["gitlab_pat"],
            )

    def _clone_tracking_repo(self) -> None:
        """
        Clone the git repository used for catalogue revision tracking to the working directory.

        The relevant branch is cloned from the remote repository to the working directory.
        """
        try:
            porcelain.clone(
                source=self._tracking_config["remote_url"],
                target=self._tracking_config["working_dir"],
                checkout=True,
                branch=self._tracking_config["branch"],
                username="gitlab-ci-token",
                password=self._tracking_config["gitlab_pat"],
            )
        except HTTPUnauthorized as e:
            raise CSWTrackingRepositoryInvalidCredentialsError from e

    def _commit_and_push_tracking_repo(self, commit_message: str, token: EntraToken) -> str:
        """
        Commit staged files and push commit to remote in git repository used for catalogue revision tracking.

        Separate committer and author identities when committing. The author identity is calculated from the current
        OAuth token, the committer is a static value representing this application as a client.

        The commit message is usually a string for the type of operation (e.g. 'Record Inserted'). Modified files are
        indicated commit (inc. file names etc.).

        The hash of the commit is returned for reporting to the user.
        """
        commit_hash = porcelain.commit(
            repo=self._tracking_repo,
            message=commit_message,
            committer=self._tracking_config["committer_identity"],
            author=self._format_commit_author(token=token),
        )

        porcelain.push(
            repo=self._tracking_repo,
            remote_location="origin",
            refspecs=self._tracking_config["branch"],
            username="gitlab-ci-token",
            password=self._tracking_config["gitlab_pat"],
        )

        return commit_hash

    def _init_auth_config(self, config: dict) -> dict[str, list[str]]:
        """
        Prepare configuration options relating to authentication and authorisation.

        :type config dict
        :param config: overall set of CSW configuration options
        :rtype dict
        :return: auth specific configuration options
        """
        auth_options = deepcopy(self.base_auth_configuration)
        if "auth_required_scopes_read" in config:
            auth_options["read"] = config["auth_required_scopes_read"]
        if "auth_required_scopes_write" in config:
            auth_options["write"] = config["auth_required_scopes_write"]

        return auth_options

    def _init_csw_config(self, config: dict) -> dict:
        """
        Prepare configuration options relating to pyCSW.

        :type config dict
        :param config: overall set of CSW configuration options
        :rtype dict
        :return: pyCSW specific configuration options
        """
        csw_options = deepcopy(self.base_configuration)
        if "endpoint" in config:
            csw_options["server"]["url"] = config["endpoint"]
        if "title" in config:
            csw_options["metadata:main"]["identification_title"] = config["title"]
        if "abstract" in config:
            csw_options["metadata:main"]["identification_abstract"] = config["abstract"]
        if "database_connection_string" in config:
            csw_options["repository"]["database"] = config["database_connection_string"]
        if "database_table" in config:
            csw_options["repository"]["table"] = config["database_table"]

        return csw_options

    def _init_tracking_config(self, config: dict) -> dict[str, bool | str | Path | None]:
        """
        Prepare configuration options relating to revision tracking.

        :type config dict
        :param config: overall set of CSW configuration options
        :rtype dict
        :return: revision tracking specific configuration options
        """
        tracking_options = deepcopy(self.base_tracking_configuration)
        if "tracking_enabled" in config:
            tracking_options["enabled"] = config["tracking_enabled"]
        if "tracking_working_dir" in config and config["tracking_working_dir"] is not None:
            tracking_options["working_dir"] = Path(config["tracking_working_dir"])
        if "tracking_remote_url" in config:
            tracking_options["remote_url"] = config["tracking_remote_url"]
        if "tracking_branch" in config:
            tracking_options["branch"] = config["tracking_branch"]
        if "tracking_committer_identity" in config:
            tracking_options["committer_identity"] = config["tracking_committer_identity"]
        if "tracking_gitlab_pat" in config:
            tracking_options["gitlab_pat"] = config["tracking_gitlab_pat"]

        return tracking_options

    def _prepare_csw_request(self, request: Request) -> _CSWServer:
        """
        Construct a PyCSW request from a Flask request.

        Tidying method to group together the logic used to transform a Flask HTTP request into a CSW (HTTP) request.

        :type request Request
        :param request: Flask HTTP request
        :rtype pycsw.server.Csw
        :return: CSW request
        """
        csw = _CSWServer(rtconfig=self._csw_config, env=request.environ, version="2.0.2")
        csw.kvp = request.args.to_dict()
        csw.requesttype = request.method

        # CSW doesn't natively support HEAD requests so alias to GET
        if request.method == "HEAD":
            csw.requesttype = "GET"

        if request.method == "POST":
            csw.request = request.data

        return csw

    def _track_revision_delete(self, csw_request: str, token: EntraToken) -> str:
        """
        Capture a record deleted via a transactional CSW request, where record revision tracking is enabled.

        This method:
        * removes (unlinking) files for the specified record (i.e. all encodings) from the git working copy
        * commits/pushes this change to the remote repository
        * deletes hashed storage directories relevant to the deleted record if they're empty
        * returns the commit hash for reporting to the user

        Empty hashed storage directories are deleted to prevent inconsistency between the working copy
        (which can contain empty directories) and the remote repository (which can't, as git only tracks files).

        See the `_track_revision()` method for general information on how revision tracking works.

        See the `_track_revision_record_paths()` method for information on how hash storage works.
        """
        record_xml_path, record_json_path = self._track_revision_record_paths(csw_request=csw_request)

        record_xml_path.unlink()
        record_json_path.unlink()

        record_path = record_xml_path.parent
        if not any(record_path.iterdir()):
            record_path.rmdir()
        if not any(record_path.parent.iterdir()):
            record_path.parent.rmdir()

        porcelain.add(repo=self._tracking_repo, paths=[record_xml_path, record_json_path])
        return self._commit_and_push_tracking_repo(commit_message="Record Deleted", token=token)

    def _track_revision_filter_request(
        self, csw_request: str, csw_response: str, transaction_type: CSWTransactionType
    ) -> bool:
        """
        Check whether a CSW request should trigger revision tracking.

        Checks applied:
        * whether the CSW request modifies a record (i.e. requests which only retrieve information do not need tracking)
        * whether revision tracking is enabled for the current catalogue
        * whether the CWS request was successful, to avoid tracking changes that aren't present within the CSW server

        If any check fails this method returns False without completing other checks. If all checks pass, a True value
        is returned by default.

        See the `_track_revision()` method for general information on how revision tracking works, and the rationale for
        why it's important to only track successful requests.

        :type csw_request
        :param csw_request: CSW server request body
        :type csw_response str
        :param csw_response: CSW server response body
        :type transaction_type CSWTransactionType
        :param transaction_type: a CSW transaction type
        :rtype bool
        :return: True if revision tracking applies to this request, otherwise False
        """
        if transaction_type == CSWTransactionType.SELECT:
            return False
        if not self._tracking_enabled:
            return False
        return self._transaction_successful(
            transaction_type=transaction_type, csw_request=csw_request, csw_response=csw_response
        )

    def _track_revision_insert_update(
        self, csw_request: str, transaction_type: CSWTransactionType, token: EntraToken
    ) -> str:
        """
        Capture a record added or updated via a transactional CSW request, where record revision tracking is enabled.

        This method:
        * extracts the metadata record from the CSW request (as XML)
        * converts this record into a BAS Metadata Library record configuration (as JSON)
        * validates this record configuration against the ISO 19115-2 JSON schema
        * writes out the metadata record as an XML file within the git working copy
        * writes out the record configuration as a JSON file within the git working copy (and correcting indentation)
        * commits/pushes this change to the remote repository
        * returns the commit hash for reporting to the user

        See the `_track_revision()` method for general information on how revision tracking works.
        """
        record_xml = self._request_record(csw_request=csw_request)
        record_xml_path, record_json_path = self._track_revision_record_paths(csw_request=csw_request)

        record = MetadataRecord(record=record_xml)
        record.validate()
        record_config = record.make_config()
        record_config.validate()

        with record_xml_path.open(mode="w") as xml_file:
            xml_file.write(record.generate_xml_document().decode())

        record_config.dump(file=record_json_path)
        # correct indentation / pretty printing of JSON file
        with record_json_path.open(mode="r") as json_file:
            json_data = json.load(json_file)
        with record_json_path.open(mode="w") as json_file:
            json.dump(json_data, json_file, indent=2)

        commit_message = "Record Inserted"
        if transaction_type == CSWTransactionType.UPDATE:
            commit_message = "Record Updated"

        porcelain.add(repo=self._tracking_repo, paths=[record_xml_path, record_json_path])
        return self._commit_and_push_tracking_repo(commit_message=commit_message, token=token)

    def _track_revision_record_paths(self, csw_request: str) -> tuple[Path, Path]:
        """
        Generate file paths for a record within record tracking repo.

        When record revision tracking is enabled, records are stored in a defined structure within a git working copy.
        Records are stored in both XML and JSON encodings within this structure. Paths for these files are returned by
        this method.

        Files are named after the file identifier of the record modified in the current (transactional) request. These
        files are stored using a 'hashed storage' layout, similar to those used in other systems with potentially large
        numbers of files named after UUID like identifiers. To avoid single directories containing large numbers of
        files, lowering performance, files are stored in subdirectories named after the first and second two character
        components of their identifier. Within this application, all such subdirectories are stored within a top level
        'records' directory.

        For example, a record with a file identifier of 'b1a7d1b5-c419-41e7-9178-b1ffd76d5371' is stored as:
        * '/records/b1/a7/b1a7d1b5-c419-41e7-9178-b1ffd76d5371.xml'
        * '/records/b1/a7/b1a7d1b5-c419-41e7-9178-b1ffd76d5371.json'

        Another record with an identifier 'b1a5b59c-8e53-4091-8548-8d24ca7099ab' is stored as:
        * '/records/b1/a5/b1a5b59c-8e53-4091-8548-8d24ca7099ab.xml'
        * '/records/b1/a5/b1a5b59c-8e53-4091-8548-8d24ca7099ab.json'

        This method will determine these paths and create parent directories as needed by parsing the file identifier
        from the record within a transactional request, and return both paths (XML and JSON) as tuple.

        :type csw_request str
        :param csw_request: CSW server request body
        :rtype Tuple
        :return: tuple of XML and JSON file paths for record in request within tracking repo
        """
        working_directory = Path(self._tracking_config["working_dir"]).resolve()
        record_id = self._request_record_file_identifier(csw_request=csw_request)

        records_directory = working_directory.joinpath("records")
        records_directory.mkdir(parents=False, exist_ok=True)

        record_path = records_directory.joinpath(record_id[0:2]).joinpath(record_id[2:4])
        record_path.mkdir(parents=True, exist_ok=True)

        xml_path = record_path.joinpath(f"{record_id}.xml")
        json_path = record_path.joinpath(f"{record_id}.json")

        return xml_path, json_path

    def _track_revision(
        self,
        flask_request: Request,
        csw_response: str,
        transaction_type: CSWTransactionType,
        token: EntraToken,
    ) -> str | None:
        """
        Capture changes to records modified via transactional CSW requests, where record revision tracking is enabled.

        This method uses information from the request passed _to_, and response returned _from_, an embedded CSW server.
        It does not interact with this server directly or underlying components such as the backing database. This
        method filters out requests where revision tracking is disabled (at a catalogue level), or has not modified a
        record (at a request level, for read/select operations).

        Revision tracking applies _after_ a record has been modified to ensure it reflects the state of the CSW backing
        database. If records were tracked _before_, and an operation failed (meaning the database does not change), we
        would need to roll back the tracked chain to ensure consistency. Tracking _after_ avoids this issue, providing
        we validate that the CSW transaction was successful. All revision information, including tracked records,
        are contained in a git working copy managed by this app.

        **Known Limitations**

        This method fails gracefully, without returning client errors for failures because:
        1. there are no revision tracking errors in the CSW standard to return and adding some may break clients
        2. doing so will not roll back the operation that has already taken place within CSW (i.e. record deletion)

        It is recognised this a poses a consistency problem and undermines confidence in this feature. See #39 for
        more information.
        """
        csw_request = flask_request.data.decode()

        if not self._track_revision_filter_request(
            csw_request=csw_request, csw_response=csw_response, transaction_type=transaction_type
        ):
            return None

        if transaction_type == CSWTransactionType.INSERT or transaction_type == CSWTransactionType.UPDATE:
            return self._track_revision_insert_update(
                csw_request=csw_request, transaction_type=transaction_type, token=token
            )
        if transaction_type == CSWTransactionType.DELETE:
            return self._track_revision_delete(csw_request=csw_request, token=token)

        return None

    def _transaction_successful(
        self, transaction_type: CSWTransactionType, csw_request: str, csw_response: str
    ) -> bool:
        """
        Determine whether a CSW transaction was successful.

        Checks whether the response from `pycsw` indicates an insert, update or delete transaction was successful by
        checking the number of modified records is as expected (specifically 1, since we don't support bulk updates).

        For insert transactions, we additionally check the record that was inserted has the same file identifier as the
        submitted record. This does not apply to other transaction types as PyCSW does not include the information.

        :type transaction_type CSWTransactionType
        :param transaction_type: CSW transaction type
        :type csw_request str
        :param csw_request: CSW server request body
        :type csw_response str
        :param csw_request: CSW server response body
        :rtype bool
        :return: True if request was a successful transaction, otherwise False
        """
        transaction_count_element: str | None = None
        transaction_result_element: str | None = None

        transaction_count: int = 0
        transaction_record_id: str | None = None

        if transaction_type == CSWTransactionType.INSERT:
            transaction_count_element = "csw:totalInserted"
            transaction_result_element = "csw:InsertResult"
        elif transaction_type == CSWTransactionType.UPDATE:
            transaction_count_element = "csw:totalUpdated"
        elif transaction_type == CSWTransactionType.DELETE:
            transaction_count_element = "csw:totalDeleted"

        request_record_id = self._request_record_file_identifier(csw_request=csw_request)
        response_xml = ElementTree(fromstring(csw_response.encode()))  # noqa: S320

        try:
            transaction_count = int(
                response_xml.xpath(
                    f"/csw:TransactionResponse/csw:TransactionSummary/{transaction_count_element}/text()",
                    namespaces=csw_namespaces,
                )[0]
            )
            if transaction_result_element is not None:
                transaction_record_id = str(
                    response_xml.xpath(
                        f"/csw:TransactionResponse/{transaction_result_element}/csw:BriefRecord/dc:identifier/text()",
                        namespaces=csw_namespaces,
                    )[0]
                )
        except IndexError:
            pass

        if transaction_result_element is None and transaction_count == 1:
            return True

        return bool(
            transaction_result_element is not None
            and transaction_count == 1
            and transaction_record_id == request_record_id
        )

    def setup_database(self) -> None:
        """
        Initialise the backing database for the catalogue.

        Convenience method to call the PyCSW admin task for setting up the required database components (tables,
        indexes, triggers, etc.)

        Note: There are currently limitations with using multiple catalogues within one schema. The specific errors
        this causes (which are not fatal) are detected by this method and treated as a false positive. See the project
        README for more information.
        """
        if self._backing_db_is_initialised:
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

    def setup_tracking(self) -> None:
        """
        Initialise the backing git repository for catalogue revision tracking.

        Checks whether:
        * tracking is enabled for catalogue

        If not:
        * setup is aborted (as a repository cannot be setup)

        Otherwise, check whether:
        * the git repository already exists as a working copy, with a remote containing the expected branch

        If not, checks whether:
        * the working directory is already a git repo with a remote by attempting to clone from the remote

        If this fails because:
        * the working directory already exists:
            * setup is aborted (as the repository is already setup)
        * the working directory does not already exist, and does not contain the expected branch:
            * a new temporary working directory is created, configured and pushed to the remote
            * the remote is cloned to the real working directory
        """
        if not self._tracking_enabled:
            raise CSWTrackingRepositoryNotEnabledError() from None

        if self._backing_repo_is_initialised:
            raise CSWTrackingRepositoryAlreadyInitialisedError() from None

        try:
            self._clone_tracking_repo()
        except FileExistsError as e:
            working_copy_git_path = Path(self._tracking_config["working_dir"]).joinpath(".git")
            if e.strerror != "File exists" or e.filename != str(working_copy_git_path):
                raise e  # noqa: TRY201
        except ValueError as e:
            if e.args[0] != f"b'{self._tracking_config['branch']}' is not a valid branch or tag":
                raise e  # noqa: TRY201

            self._create_tracking_repo()
            self._clone_tracking_repo()

    def process_request(self, request: Request, token: EntraToken | None = None) -> Response:
        # noinspection GrazieInspection
        """
        Process a CSW request and return response.

        Represents embedding CSW by processing an incoming Flask/HTTP request into a CSW request and returning the CSW
        response as a Flask/HTTP response.

        In addition this method:
        * supports authorisation checks for reading records and using the transactional profile
        * supports HEAD requests by treating them as GET requests and discarding the response body
        * supports tracking record revisions for requests using the transactional profile (when enabled)
        """
        if not self._backing_db_is_initialised:
            raise CSWDatabaseNotInitialisedError()
        if self._tracking_enabled and not self._backing_repo_is_initialised:
            raise CSWTrackingRepositoryNotInitialisedError()
        if request.method not in ["HEAD", "GET", "POST"]:
            raise CSWMethodNotSupportedError()

        csw_request = self._prepare_csw_request(request=request)
        transaction_type = self._transaction_type(csw_request=csw_request)
        self._check_auth(transaction_type=transaction_type, token=token)

        headers = {}
        status_code, csw_response = csw_request.dispatch()

        revision_id = self._track_revision(
            flask_request=request, csw_response=csw_response.decode(), transaction_type=transaction_type, token=token
        )
        if revision_id is not None:
            headers["X-CSW-REVISION-ID"] = revision_id

        if request.method == "HEAD":
            return Response(status=status_code, headers=headers)
        return Response(
            response=csw_response, status=status_code, content_type=csw_request.contenttype, headers=headers
        )


class CSWClient:  # pragma: no cover (until #59 is resolved)
    """
    Represents a CSW Client backed by OWSLib.

    This class is largely a wrapper around the OWSLib CSW class in order to abstract away CSW or OWSLib specific
    details (such as needing to know to use the `getRecords2` method for example).

    Other features include:
    * raising exceptions for errors
    * support for token based authentication
    * workaround to fix transactional update results count error
    * compatibility with this application's CSWServer class for error handling
    * compatibility with this application's Repository class for setting CSW configuration options

    Note: This class uses classes from the Hazardous Materials module. This is to work around limitations in the OWSLib
    package. This will be addressed by upstreaming missing functionality or creating a derivative package.
    """

    def __init__(self, config: dict) -> None:
        """
        Initialise CSW client.

        Configuration dict must include:

        * endpoint: URL to CSW service (str)
        * auth: parameters for CSW authentication object (maybe empty dict)

        Other OWSLib configuration options may also be included.

        :type config: dict
        :param config: CSW (OWSLib) configuration options
        """
        self._csw_config = config
        self._csw_endpoint = config["endpoint"]
        self._csw_auth = CSWAuth(**config["auth"])
        del self._csw_config["endpoint"]
        del self._csw_config["auth"]

    def __repr__(self) -> str:
        return f"<CSWClient / Endpoint: {self._csw_endpoint}>"

    def _get_client(self) -> _CSWClient:
        """
        Create a OWSLib CSW client instance.

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
        Return a single record.

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
            if _csw.response.decode() == "Insufficient authorisation token.":
                raise CSWAuthInsufficientError() from None

    def get_records(self, mode: CSWGetRecordMode = CSWGetRecordMode.FULL) -> Generator[str, None, None]:
        """
        Return all records.

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
        Insert a new record.

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
            if _csw.response.decode() == "Insufficient authorisation token.":
                raise CSWAuthInsufficientError() from None

    def update_record(self, record: str) -> None:
        """
        Update an existing record.

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
                ElementTree(fromstring(_csw.response)).xpath(  # noqa: S320
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
            if _csw.response.decode() == "Insufficient authorisation token.":
                raise CSWAuthInsufficientError() from None

    def delete_record(self, identifier: str) -> None:
        """
        Delete an existing record.

        Uses the CSW transactional profile to delete an existing record from a CSW catalogue.

        :type identifier str
        :param identifier: ISO 19115 file identifier
        """
        _csw = self._get_client()
        try:
            _csw.transaction(ttype=CSWTransactionType.DELETE.value, identifier=identifier)
            _csw.results["deleted"] = int(
                ElementTree(fromstring(_csw.response)).xpath(  # noqa: S320
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
            if _csw.response.decode() == "Insufficient authorisation token.":
                raise CSWAuthInsufficientError() from None

    @staticmethod
    def _convert_csw_brief_gmd_to_gmi_xml(record_xml: str) -> str:
        """
        Convert CSW GetRecord(s) requests using the 'brief' element set name from ISO-19115(-0) to ISO 19115-2.

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

        gmd_xml_element = ElementTree(fromstring(record_xml))  # noqa: S320
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
