import os
import warnings
from time import strftime

import requests
import sentry_sdk
import simplejson as json

from logging import Formatter
from logging.handlers import RotatingFileHandler
from datetime import date, datetime
from pathlib import Path
from urllib.parse import urlparse as url_parse, parse_qs as query_string_parse
from unittest import mock

from click import (
    echo,
    style as click_style,
    pause as click_pause,
    confirm as click_confirm,
    Abort,
)
from flask import (
    Flask,
    logging as flask_logging,
    render_template,
    url_for,
    request,
    Response,
)
from flask.cli import AppGroup
from jinja2 import PrefixLoader, FileSystemLoader, PackageLoader
from markupsafe import escape as markup_escape
from markdown import markdown
from dateutil.relativedelta import relativedelta
from bas_metadata_library.standards.iso_19115_2_v1 import (
    MetadataRecordConfig,
    MetadataRecord,
)
from owslib.util import Authentication
from owslib.csw import (
    CatalogueServiceWeb as _CatalogueServiceWeb,
    namespaces as csw_namespaces,
)
from pycsw import __version__ as pycsw_version
from authlib.integrations.flask_oauth2 import current_token
from flask_azure_oauth.errors import ApiAuthTokenScopesInsufficient
from flask_azure_oauth import FlaskAzureOauth
from flask_frozen import Freezer
from awscli.clidriver import create_clidriver

# noinspection PyPep8Naming
from inquirer import prompt, List as inquirer_list, Path as inquirer_path

# noinspection PyPackageRequirements
# Exempting Bandit security issue (Using Element to parse untrusted XML data is known to be vulnerable to XML attacks)
#
# We don't currently allow untrusted/user-provided XML so this is not a risk
from lxml.etree import ElementTree, ProcessingInstruction, fromstring, tostring  # nosec

warnings.simplefilter(action="ignore", category=FutureWarning)
from pycsw.server import Csw

# For overloaded CSW class
import inspect
from io import BytesIO
from owslib.etree import etree
from owslib import util
from owslib import ows
from owslib.util import cleanup_namespaces, bind_url, add_namespaces, openURL, http_post
from owslib import fes
from owslib.util import OrderedDict
from owslib.csw import (
    outputformat as csw_outputformat,
    schema_location as csw_schema_location,
)

from scar_add_metadata_toolbox.utils import _create_app_config


def aws_cli(*cmd):
    """
    TODO: Add docblock
    Source: https://github.com/boto/boto3/issues/358#issuecomment-372086466
    """
    old_env = dict(os.environ)
    try:

        # Environment
        env = os.environ.copy()
        env["LC_CTYPE"] = "en_US.UTF"
        os.environ.update(env)

        # Run awscli in the same process
        exit_code = create_clidriver().main(*cmd)

        # Deal with problems
        if exit_code > 0:
            raise RuntimeError("AWS CLI exited with code {}".format(exit_code))
    finally:
        os.environ.clear()
        os.environ.update(old_env)


class CatalogueServiceWebAuthentication(Authentication):
    """
    @TODO: Add docblock
    """

    _TOKEN = None

    def __init__(
        self, token=None, username=None, password=None, cert=None, verify=True, shared=False,
    ):
        """
        :param str token=None: Token for bearer authentication, None for
            unauthenticated access (or if using user/pass or cert/verify)
        """
        super().__init__(username, password, cert, verify, shared)
        self.token = token

    @property
    def token(self):
        if self.shared:
            return self._TOKEN
        return self._token

    @token.setter
    def token(self, value):
        if value is None:
            pass
        elif not isinstance(value, str):
            raise TypeError('Value for "token" must be a str')
        if self.shared:
            self.__class__._TOKEN = value
        else:
            self._token = value

    @property
    def urlopen_kwargs(self):
        return {
            "token": self.token,
            "username": self.username,
            "password": self.password,
            "cert": self.cert,
            "verify": self.verify,
        }

    def __repr__(self, *args, **kwargs):
        return "<{} shared={} token={} username={} password={} cert={} verify={}>".format(
            self.__class__.__name__, self.shared, self.token, self.username, self.password, self.cert, self.verify,
        )


original_request = requests.request


def wrapped_request_request(*args, **kwargs):
    if (
        "auth" in kwargs.keys()
        and isinstance(kwargs["auth"], tuple)
        and len(kwargs["auth"]) == 2
        and kwargs["auth"][0] == "bearer-token"
    ):
        if "headers" not in kwargs.keys():
            kwargs["headers"] = {}
        kwargs["headers"]["authorization"] = f"bearer {kwargs['auth'][1]}"
        del kwargs["auth"]

    print("November")
    print(args)
    print(kwargs)
    _ = original_request(*args, **kwargs)
    print("request")
    print(_.content[0:100])
    print(_.content)
    return _


original_post = requests.post


def wrapped_request_post(*args, **kwargs):
    if (
        "auth" in kwargs.keys()
        and isinstance(kwargs["auth"], tuple)
        and len(kwargs["auth"]) == 2
        and kwargs["auth"][0] == "bearer-token"
    ):
        if "headers" not in kwargs.keys():
            kwargs["headers"] = {}
        kwargs["headers"]["authorization"] = f"bearer {kwargs['auth'][1]}"
        del kwargs["auth"]

    print("India")
    print(args)
    print(kwargs)

    _ = original_post(*args, **kwargs)
    print("request 2")
    print(_.content[0:100])
    return _


class CatalogueServiceWeb(_CatalogueServiceWeb):
    """
    @TODO: Add docblock
    """

    # @mock.patch("requests.get", wraps=wrapped_request_get)
    # @mock.patch("requests.request", wraps=wrapped_request_request)
    # def _invoke2(self, mock_requests_get, mock_requests_request):
    #     try:
    #         if self.auth.token is not None:
    #             self.auth.username = "bearer-token"
    #             self.auth.password = self.auth.token
    #     except AttributeError:
    #         pass
    #
    #     # debug
    #     _ = super()._invoke()
    #     print("invoke")
    #     print(_)
    #     return _

    # TODO: Revert to minimal class
    @mock.patch("requests.post", wraps=wrapped_request_post)
    @mock.patch("requests.request", wraps=wrapped_request_request)
    def _invoke(self, mock_requests_post, mock_requests_request):
        try:
            if self.auth.token is not None:
                self.auth.username = "bearer-token"
                self.auth.password = self.auth.token
        except AttributeError:
            pass

        # do HTTP request

        request_url = self.url

        # Get correct URL based on Operation list.

        # If skip_caps=True, then self.operations has not been set, so use
        # default URL.
        if hasattr(self, "operations"):
            caller = inspect.stack()[1][3]
            if caller == "getrecords2":
                caller = "getrecords"
            # noinspection PyBroadException
            try:
                op = self.get_operation_by_name(caller)
                if isinstance(self.request, str):  # GET KVP
                    get_verbs = [x for x in op.methods if x.get("type").lower() == "get"]
                    request_url = get_verbs[0].get("url")
                else:
                    post_verbs = [x for x in op.methods if x.get("type").lower() == "post"]
                    if len(post_verbs) > 1:
                        # Filter by constraints.  We must match a PostEncoding of "XML"
                        for pv in post_verbs:
                            for const in pv.get("constraints"):
                                if const.name.lower() == "postencoding":
                                    values = [v.lower() for v in const.values]
                                    if "xml" in values:
                                        request_url = pv.get("url")
                                        break
                        else:
                            # Well, just use the first one.
                            request_url = post_verbs[0].get("url")
                    elif len(post_verbs) == 1:
                        request_url = post_verbs[0].get("url")
            except Exception:  # nosec
                # no such luck, just go with request_url
                pass

        print("Echo")

        if isinstance(self.request, str):  # GET KVP
            print("Foxtrot")

            self.request = "%s%s" % (bind_url(request_url), self.request)
            self.response = openURL(self.request, None, "Get", timeout=self.timeout, auth=self.auth).read()

            # debug
            print("invoke")
            print(self.response[0:100])
        else:
            print("Golf")

            self.request = cleanup_namespaces(self.request)
            # Add any namespaces used in the "typeNames" attribute of the
            # csw:Query element to the query's xml namespaces.
            # noinspection PyUnresolvedReferences
            for query in self.request.findall(util.nspath_eval("csw:Query", csw_namespaces)):
                ns = query.get("typeNames", None)
                if ns is not None:
                    # Pull out "gmd" from something like "gmd:MD_Metadata" from the list
                    # of typenames
                    ns_keys = [x.split(":")[0] for x in ns.split(" ")]
                    self.request = add_namespaces(self.request, ns_keys)
            self.request = add_namespaces(self.request, "ows")

            self.request = util.element_to_string(self.request, encoding="utf-8")

            print("Hotel")

            self.response = http_post(request_url, self.request, self.lang, self.timeout, auth=self.auth)

            # debug
            print("invoke 2")
            print(self.response[0:100])

        # debug
        print("parse")
        print(self.response[0:100])
        print(self.response)

        # parse result see if it's XML
        self._exml = etree.parse(BytesIO(self.response))

        # it's XML.  Attempt to decipher whether the XML response is CSW-ish """
        valid_xpaths = [
            util.nspath_eval("ows:ExceptionReport", csw_namespaces),
            util.nspath_eval("csw:Capabilities", csw_namespaces),
            util.nspath_eval("csw:DescribeRecordResponse", csw_namespaces),
            util.nspath_eval("csw:GetDomainResponse", csw_namespaces),
            util.nspath_eval("csw:GetRecordsResponse", csw_namespaces),
            util.nspath_eval("csw:GetRecordByIdResponse", csw_namespaces),
            util.nspath_eval("csw:HarvestResponse", csw_namespaces),
            util.nspath_eval("csw:TransactionResponse", csw_namespaces),
        ]

        if self._exml.getroot().tag not in valid_xpaths:
            raise RuntimeError("Document is XML, but not CSW-ish")

        # check if it's an OGC Exception
        val = self._exml.find(util.nspath_eval("ows:Exception", csw_namespaces))
        if val is not None:
            raise ows.ExceptionReport(self._exml, self.owscommon.namespace)
        else:
            self.exceptionreport = None

    def getrecords2(
        self,
        constraints=[],
        sortby=None,
        typenames="csw:Record",
        esn="summary",
        outputschema=csw_namespaces["csw"],
        format=csw_outputformat,
        startposition=0,
        maxrecords=10,
        cql=None,
        xml=None,
        resulttype="results",
    ):
        """

        Construct and process a  GetRecords request

        Parameters
        ----------

        - constraints: the list of constraints (OgcExpression from owslib.fes module)
        - sortby: an OGC SortBy object (SortBy from owslib.fes module)
        - typenames: the typeNames to query against (default is csw:Record)
        - esn: the ElementSetName 'full', 'brief' or 'summary' (default is 'summary')
        - outputschema: the outputSchema (default is 'http://www.opengis.net/cat/csw/2.0.2')
        - format: the outputFormat (default is 'application/xml')
        - startposition: requests a slice of the result set, starting at this position (default is 0)
        - maxrecords: the maximum number of records to return. No records are returned if 0 (default is 10)
        - cql: common query language text.  Note this overrides bbox, qtype, keywords
        - xml: raw XML request.  Note this overrides all other options
        - resulttype: the resultType 'hits', 'results', 'validate' (default is 'results')

        """

        if xml is not None:
            self.request = etree.fromstring(xml)
            val = self.request.find(util.nspath_eval("csw:Query/csw:ElementSetName", csw_namespaces))
            if val is not None:
                esn = util.testXMLValue(val)
            val = self.request.attrib.get("outputSchema")
            if val is not None:
                outputschema = util.testXMLValue(val, True)
        else:
            # construct request
            node0 = self._setrootelement("csw:GetRecords")
            if etree.__name__ != "lxml.etree":  # apply nsmap manually
                node0.set("xmlns:ows", csw_namespaces["ows"])
                node0.set("xmlns:gmd", csw_namespaces["gmd"])
                node0.set("xmlns:dif", csw_namespaces["dif"])
                node0.set("xmlns:fgdc", csw_namespaces["fgdc"])
            node0.set("outputSchema", outputschema)
            node0.set("outputFormat", format)
            node0.set("version", self.version)
            node0.set("service", self.service)
            node0.set("resultType", resulttype)
            if startposition > 0:
                node0.set("startPosition", str(startposition))
            node0.set("maxRecords", str(maxrecords))
            node0.set(
                util.nspath_eval("xsi:schemaLocation", csw_namespaces), csw_schema_location,
            )

            node1 = etree.SubElement(node0, util.nspath_eval("csw:Query", csw_namespaces))
            node1.set("typeNames", typenames)

            etree.SubElement(node1, util.nspath_eval("csw:ElementSetName", csw_namespaces)).text = esn

            if any([len(constraints) > 0, cql is not None]):
                node2 = etree.SubElement(node1, util.nspath_eval("csw:Constraint", csw_namespaces))
                node2.set("version", "1.1.0")
                flt = fes.FilterRequest()
                if len(constraints) > 0:
                    node2.append(flt.setConstraintList(constraints))
                # Now add a CQL filter if passed in
                elif cql is not None:
                    etree.SubElement(node2, util.nspath_eval("csw:CqlText", csw_namespaces)).text = cql

            if sortby is not None and isinstance(sortby, fes.SortBy):
                node1.append(sortby.toXML())

            self.request = node0

        print("Delta")
        self._invoke()

        if self.exceptionreport is None:
            self.results = {}

            # process search results attributes
            val = self._exml.find(util.nspath_eval("csw:SearchResults", csw_namespaces)).attrib.get(
                "numberOfRecordsMatched"
            )
            self.results["matches"] = int(util.testXMLValue(val, True))
            val = self._exml.find(util.nspath_eval("csw:SearchResults", csw_namespaces)).attrib.get(
                "numberOfRecordsReturned"
            )
            self.results["returned"] = int(util.testXMLValue(val, True))
            val = self._exml.find(util.nspath_eval("csw:SearchResults", csw_namespaces)).attrib.get("nextRecord")
            if val is not None:
                self.results["nextrecord"] = int(util.testXMLValue(val, True))
            else:
                warnings.warn(
                    """CSW Server did not supply a nextRecord value (it is optional), so the client
                should page through the results in another way."""
                )
                # For more info, see:
                # https://github.com/geopython/OWSLib/issues/100
                self.results["nextrecord"] = None

            # process list of matching records
            self.records = OrderedDict()

            self._parserecords(outputschema, esn)


def create_app():
    app = Flask(__name__)

    app.config.from_object(_create_app_config())

    app.jinja_loader = PrefixLoader(
        {"app": FileSystemLoader("templates"), "bas_style_kit": PackageLoader("bas_style_kit_jinja_templates"),}
    )
    app.config["bsk_templates"] = app.config["BSK_TEMPLATES"]

    @app.template_filter()
    def format_datetime(value, date_format="date+time"):
        if date_format == "date+time":
            date_format = "%Y-%m-%d %H:%M:%s"
        elif date_format == "date":
            date_format = "%Y-%m-%d"
        return value.strftime(format=date_format)

    if "LOGGING_LEVEL" in app.config:
        app.logger.setLevel(app.config["LOGGING_LEVEL"])
        flask_logging.default_handler.setFormatter(Formatter(app.config["LOG_FORMAT"]))
    # TODO: Remove file based logging in favour of stdout
    # if app.config["APP_ENABLE_FILE_LOGGING"]:
    #     file_log = RotatingFileHandler(app.config["LOG_FILE_PATH"], maxBytes=5242880, backupCount=5)
    #     file_log.setLevel(app.config["LOGGING_LEVEL"])
    #     file_log.setFormatter(Formatter(app.config["LOG_FORMAT"]))
    #     app.logger.addHandler(file_log)

    if app.config["APP_ENABLE_SENTRY"]:
        app.logger.info("Sentry error reporting enabled")
        sentry_sdk.init(**app.config["SENTRY_CONFIG"])

    auth = FlaskAzureOauth()
    auth.init_app(app)

    freezer = Freezer(with_no_argument_rules=False, log_url_for=False)
    freezer.init_app(app)

    app.logger.info(
        f"APP.NAME [{app.config['NAME']}], APP.VERSION [{app.config['VERSION']}] APP.ENV [{app.config['ENV']}]"
    )

    # CLI commands
    #

    @app.cli.command("version")
    def version():
        """Display application version."""
        print(f"Version: {app.config['VERSION']}")

    @app.cli.command("export")
    def export():
        """Export application routes as a static website."""
        freezer.freeze()
        echo(
            f"{click_style('Successfully exported static site', fg='green')} to "
            f"{click_style(str(app.config['STATIC_BUILD_DIR']), fg='blue')}"
        )

    @app.cli.command("publish")
    def publish():
        """Publish exported application as a static website."""
        try:
            aws_cli(
                ["s3", "sync", str(app.config["STATIC_BUILD_DIR"]), f"s3://{app.config['S3_BUCKET']}", "--delete",]
            )
            echo(
                f"{click_style('Successfully published static site', fg='green')} to "
                f"https://{click_style(app.config['S3_BUCKET'], fg='blue')}"
            )
        except RuntimeError as e:
            echo(f"{click_style('Unable to publish static site', fg='red')}")
            raise e

    auth_cli_group = AppGroup("auth", help="Authentication and access control.")
    app.cli.add_command(auth_cli_group)

    @auth_cli_group.command("sign-in")
    def sign_in():
        """Sign-in to application (requires user account)."""
        if app.config["CLIENT_AUTH_TOKEN"] is not None:
            echo(
                f"{click_style('Sign-in unavailable', fg='yellow')}, someone is already signed-in, run "
                f"{click_style('auth check', fg='cyan')} to see who or {click_style('auth sign-out', fg='cyan')} to "
                f"sign out and change user"
            )
            raise Abort()

        app.logger.info(
            f"Starting Azure device flow, requesting {len(app.config['AUTH_CLIENT_SCOPES'])} scopes "
            f"[{', '.join(app.config['AUTH_CLIENT_SCOPES'])}]"
        )
        auth_flow = app.config["CLIENT_AUTH"].initiate_device_flow(scopes=app.config["AUTH_CLIENT_SCOPES"])
        if "user_code" not in auth_flow:
            app.logger.error("Authentication failure - 'user_code' not returned by Azure")
            app.logger.error(json.dumps(auth_flow))
            raise RuntimeError("Could not start authentication flow. No 'user_code' returned by Azure.")

        app.logger.info(f"Authorisation request successful, displaying user instructions for how to authenticate")
        echo(
            f"To sign into this application, use a web browser to open the page "
            f"'{click_style('https://microsoft.com/devicelogin', fg='blue')}' and enter this code: "
            f"'{click_style(auth_flow['user_code'], fg='cyan')}'"
        )
        app.logger.info(f"Pausing until user has signed-in")
        click_pause(
            info=f"Once you've signed in, {click_style('press any key to continue', fg='yellow')}, or "
            f"{click_style('press [ctrl + c] twice to abort', fg='yellow')} ..."
        )
        auth_token = app.config["CLIENT_AUTH"].acquire_token_by_device_flow(auth_flow)
        if "access_token" not in auth_token:
            app.logger.error("Authentication failure - 'access_token' not returned by Azure")
            app.logger.error(json.dumps(auth_flow))
            raise RuntimeError("Could not start authentication flow. No 'access_token' returned by Azure.")

        app.logger.info(
            f"Authentication flow completed, [{auth_token['id_token_claims']['preferred_username']}] "
            f"signed-in successfully, writing to auth file {app.config['APP_AUTH_SESSION_FILE_PATH'].absolute()}"
        )
        # TODO: Refactor this into the setter in config class
        app.logger.info(f"Creating auth file parent directories if needed")
        app.config["APP_AUTH_SESSION_FILE_PATH"].parent.mkdir(parents=True, exist_ok=True)
        app.logger.info(f"Creating auth file as [{app.config['APP_AUTH_SESSION_FILE_PATH'].absolute()}]")
        with open(app.config["APP_AUTH_SESSION_FILE_PATH"], "w") as auth_file:
            json.dump(auth_token, auth_file)

        # TODO: Try to improve this, we use the string split method to get just the first name of the user
        # TODO: Is it just a case of base64 decoding the token?
        # That exists as a proper claim in the access token (but not the ID token) but it wasn't trivial to decode
        # the JWT as we also need to provide a JWK to sign-it, even though we don't care if the token is valid here.
        echo(
            f"{click_style('Sign-in successful', fg='green')}, "
            f"hello {click_style(auth_token['id_token_claims']['name'].split(' ')[0], fg='magenta')}"
        )
        echo(
            f"For reference, your login details have been saved to "
            f"{click_style(str(app.config['APP_AUTH_SESSION_FILE_PATH'].absolute()), fg='blue')}"
        )

    @auth_cli_group.command("sign-out")
    def sign_out():
        """Sign-out of application, removing stored sign-in details."""

        if app.config["CLIENT_AUTH_TOKEN"] is None:
            echo(
                f"{click_style('Sign-out unavailable', fg='yellow')}, run {click_style('auth sign-in', fg='cyan')} "
                f"to sign in first"
            )
            raise Abort()

        click_confirm(
            text=f"{click_style('Are you sure you want to sign-out?', fg='yellow')}", abort=True,
        )
        app.logger.info(
            f"Unlinking auth file {click_style(str(app.config['APP_AUTH_SESSION_FILE_PATH'].absolute()), fg='blue')}"
        )
        app.config["APP_AUTH_SESSION_FILE_PATH"].unlink()
        echo(click_style("Sign-out successful", fg="green"))

    @auth_cli_group.command("check")
    def check():
        """Checks whether a user is still Signed-in to application."""
        if app.config["CLIENT_AUTH_TOKEN"] is None:
            echo(
                f"{click_style('No one is signed in', fg='yellow')}, run {click_style('auth sign-in', fg='cyan')} "
                f"to sign in"
            )
            raise Abort()

        echo(
            f"{click_style('You are signed in', fg='green')} as "
            f"{click_style(app.config['CLIENT_AUTH_TOKEN']['id_token_claims']['name'].split(' ')[0], fg='magenta')} "
            f"({click_style(app.config['CLIENT_AUTH_TOKEN']['id_token_claims']['preferred_username'], fg='cyan')})"
        )

    records_cli_group = AppGroup("records", help="Manage metadata records.")
    app.cli.add_command(records_cli_group)

    # TODO: Add support for published status (i.e. is record published or not)
    @records_cli_group.command("list")
    def list_records():
        """List records in the ADD CSW catalogue."""
        app.logger.info(f"Listing records from CSW catalogue [{app.config['CSW_ENDPOINT_UNPUBLISHED']}]")

        csw_auth = CatalogueServiceWebAuthentication(token=app.config["CLIENT_AUTH_TOKEN"]["access_token"])
        csw_unpublished = CatalogueServiceWeb(app.config["CSW_ENDPOINT_UNPUBLISHED"], auth=csw_auth)
        csw_unpublished.getrecords2(
            typenames="gmd:MD_Metadata",
            esn="brief",
            resulttype="results",
            outputschema="http://www.isotc211.org/2005/gmd",
            maxrecords=100,
        )

        csw_published = CatalogueServiceWeb(app.config["CSW_ENDPOINT_PUBLISHED"], auth=csw_auth)
        csw_published.getrecords2(
            typenames="gmd:MD_Metadata",
            esn="brief",
            resulttype="results",
            outputschema="http://www.isotc211.org/2005/gmd",
            maxrecords=100,
        )

        echo(f"List of ADD metadata records:")
        for record in csw_unpublished.records:
            publication_status = f"{click_style('Unpublished', fg='yellow')}"
            if csw_unpublished.records[record].identifier in csw_published.records:
                publication_status = f"{click_style('Published', fg='green')}"

            echo(
                f"* {click_style(csw_unpublished.records[record].identifier, fg='cyan')} - "
                f"{click_style(csw_unpublished.records[record].identification.title, fg='magenta')} - "
                f"{publication_status}"
            )

    # TODO: Add record and path as command arguments for completeness
    @records_cli_group.command("import")
    def import_record():
        """Import a new or updated record into the unpublished catalogue."""
        # TODO: Review logging statements to ensure we only log whats needed (is this?)
        app.logger.info(f"Importing a record as JSON into CSW catalogue [{app.config['CSW_ENDPOINT_UNPUBLISHED']}]")
        # TODO: I hate this, refactor into bare variables
        options = {
            "data": None,
            "record": None,
            "path": None,
            "title": None,
            "update": False,
        }
        selected_file = prompt(
            [
                inquirer_path(
                    name="path",
                    message="What is the path to the file containing the record you would like to import?",
                    exists=True,
                    path_type=inquirer_path.FILE,
                    normalize_to_absolute_path=True,
                ),
            ]
        )
        if selected_file is None:
            raise Abort()
        options["path"] = selected_file["path"]
        options["path"] = Path(options["path"])

        app.logger.info(f"Importing record from [{str(options['path'].absolute())}]")
        echo(f"Importing metadata record from file {click_style(str(options['path'].absolute()), fg='blue')}")
        if not options["path"].exists():
            # TODO: Raise proper error
            app.logger.error(f"Unable to import file, path [{str(options['path'].absolute())}], does not exist")
            raise RuntimeError("File to import does not exist")
        with open(str(options["path"]), "r") as import_file:
            # TODO: Check JSON is valid
            options["data"] = json.load(import_file)

        # TODO: Consider whether this should go into the metadata generator
        # TODO: Deal with the fact that these could be date or datetime objects
        app.logger.info(f"Convert date strings into Python date objects")
        options["data"]["date_stamp"] = date.fromisoformat(options["data"]["date_stamp"])
        options["data"]["reference_system_info"]["authority"]["dates"][0]["date"] = date.fromisoformat(
            options["data"]["reference_system_info"]["authority"]["dates"][0]["date"]
        )
        for index, resource_date in enumerate(options["data"]["resource"]["dates"]):
            if "date_precision" in resource_date.keys() and resource_date["date_precision"] == "year":
                options["data"]["resource"]["dates"][index]["date"] = date(
                    year=int(options["data"]["resource"]["dates"][index]["date"]), month=1, day=1,
                ).isoformat()

            # TODO: Fix this horrible hack
            if len(options["data"]["resource"]["dates"][index]["date"]) == 10:
                options["data"]["resource"]["dates"][index]["date"] = date.fromisoformat(
                    options["data"]["resource"]["dates"][index]["date"]
                )
            elif len(options["data"]["resource"]["dates"][index]["date"]) == 19:
                options["data"]["resource"]["dates"][index]["date"] = datetime.fromisoformat(
                    options["data"]["resource"]["dates"][index]["date"]
                )

        for index, keyword in enumerate(options["data"]["resource"]["keywords"]):
            options["data"]["resource"]["keywords"][index]["thesaurus"]["dates"][0]["date"] = date.fromisoformat(
                options["data"]["resource"]["keywords"][index]["thesaurus"]["dates"][0]["date"]
            )

        # TODO: Fix horrible hack!
        if len(options["data"]["resource"]["extent"]["temporal"]["period"]["start"]) == 4:
            options["data"]["resource"]["extent"]["temporal"]["period"][
                "start"
            ] = f"{options['data']['resource']['extent']['temporal']['period']['start']}-01-01"
        options["data"]["resource"]["extent"]["temporal"]["period"]["start"] = datetime.fromisoformat(
            options["data"]["resource"]["extent"]["temporal"]["period"]["start"]
        )
        options["data"]["resource"]["extent"]["temporal"]["period"]["end"] = datetime.fromisoformat(
            options["data"]["resource"]["extent"]["temporal"]["period"]["end"]
        )
        if "measures" in options["data"]["resource"].keys():
            options["data"]["resource"]["measures"][0]["dates"][0]["date"] = date.fromisoformat(
                options["data"]["resource"]["measures"][0]["dates"][0]["date"]
            )

        record_config = MetadataRecordConfig(**options["data"])
        # TODO: Catch errors
        record_config.validate()
        options["record"] = options["data"]["file_identifier"]
        options["title"] = options["data"]["resource"]["title"]["value"]
        app.logger.info(f"loaded record [{options['record']}]")
        echo(
            f"Loaded record {click_style(options['record'], fg='cyan')} - "
            f"{click_style(options['title'], fg='magenta')}"
        )

        # TODO: Refactor this into a common object & method
        csw_auth = CatalogueServiceWebAuthentication(token=app.config["CLIENT_AUTH_TOKEN"]["access_token"])
        csw = CatalogueServiceWeb(app.config["CSW_ENDPOINT_UNPUBLISHED"], auth=csw_auth)
        csw.getrecords2(
            typenames="gmd:MD_Metadata",
            esn="brief",
            resulttype="results",
            outputschema="http://www.isotc211.org/2005/gmd",
            maxrecords=100,
        )
        if record_config.config["file_identifier"] in list(csw.records.keys()):
            options["update"] = True

        if options["update"]:
            click_confirm(
                f"A record with ID [{click_style(options['record'], fg='cyan')}] already exists - "
                f"{click_style('do you want to update it with this import?', fg='yellow')}",
                abort=True,
            )

        app.logger.info(f"Creating record [{options['record']}] (without XML declaration)")
        record = MetadataRecord(configuration=record_config).make_element()
        document = tostring(ElementTree(record), pretty_print=True, xml_declaration=False, encoding="utf-8",)

        # TODO: Refactor this to use a single CSW instance
        csw_auth = CatalogueServiceWebAuthentication(token=app.config["CLIENT_AUTH_TOKEN"]["access_token"])
        csw = CatalogueServiceWeb(app.config["CSW_ENDPOINT_UNPUBLISHED"], auth=csw_auth)
        # TODO: Refactor to remove else/repetition
        if options["update"]:
            app.logger.info(
                f"Updating record [{options['record']}] in CSW repository [{app.config['CSW_ENDPOINT_UNPUBLISHED']}]"
            )
            csw.transaction(ttype="update", typename="gmd:MD_Metadata", record=document)
            # Workaround for https://github.com/geopython/OWSLib/issues/678
            csw.results["updated"] = int(
                ElementTree(fromstring(csw.response)).xpath(
                    "/csw:TransactionResponse/csw:TransactionSummary/csw:totalUpdated/text()",
                    namespaces=csw_namespaces,
                )[0]
            )

            print("Romeo")
            print(csw.results["updated"])

            if csw.results["updated"] != 1:
                # TODO: Raise proper error
                app.logger.error(f"Unable to update record in CSW")
                raise RuntimeError("Unable to update record in CSW")
            echo(
                f"{click_style('Successfully updated', fg='green')} record "
                f"[{click_style(options['record'], fg='cyan')}]."
            )
        else:
            app.logger.info(
                f"Inserting record [{options['record']}] into CSW repository [{app.config['CSW_ENDPOINT_UNPUBLISHED']}]"
            )

            csw.transaction(ttype="insert", typename="gmd:MD_Metadata", record=document)

            print("Oscar")
            print(csw.results["insertresults"])

            # noinspection PyTypeChecker
            if len(csw.results["insertresults"]) != 1:
                # TODO: Raise proper error
                app.logger.error(f"Unable to insert record in CSW")
                raise RuntimeError("Unable to insert record in CSW")
            echo(
                f"{click_style('Successfully added', fg='green')} record "
                f"[{click_style(csw.results['insertresults'][0], fg='cyan')}]."
            )

    # TODO: Add record and path as command arguments for completeness
    @records_cli_group.command("export")
    def export_record():
        """Export a record from the unpublished catalogue for editing."""
        app.logger.info(f"Exporting a record from CSW catalogue [{app.config['CSW_ENDPOINT_UNPUBLISHED']}] as JSON")
        # TODO: Refactor to extract common function
        csw_auth = CatalogueServiceWebAuthentication(token=app.config["CLIENT_AUTH_TOKEN"]["access_token"])
        csw = CatalogueServiceWeb(app.config["CSW_ENDPOINT_UNPUBLISHED"], auth=csw_auth)
        csw.getrecords2(
            typenames="gmd:MD_Metadata",
            esn="full",
            resulttype="results",
            outputschema="http://www.isotc211.org/2005/gmd",
            maxrecords=100,
        )
        records = {}
        for record in csw.records:
            records[csw.records[record].identifier] = csw.records[record].identification.title
        _records = {f"* {click_style(k, fg='cyan')} - {click_style(v, fg='magenta')}": k for k, v in records.items()}

        # TODO:
        # Create a Catalogue and Record class

        # TODO: Refactor to remove options dict and have one set of questions
        options = {"record": None, "path": None, "title": None}
        selected_record = prompt(
            [
                inquirer_list(
                    name="record", message="Which record would like to export?", choices=list(_records.items()),
                ),
            ]
        )
        if selected_record is None:
            raise Abort()
        options["record"] = selected_record["record"]
        options["title"] = records[options["record"]]
        selected_path = prompt(
            [
                inquirer_path(
                    name="path",
                    message="Which directory would like to export this record into?",
                    default=f"/tmp",
                    exists=True,
                    path_type=inquirer_path.DIRECTORY,
                    normalize_to_absolute_path=True,
                ),
            ]
        )
        if selected_path is None:
            raise Abort()
        options["path"] = selected_path["path"]
        app.logger.info(f"selected record [{options['record']}], selected path [{options['path']}]")

        # TODO: Refactor this into common code
        app.logger.info(
            f"Requesting record [{options['record']}] from CSW endpoint [{app.config['CSW_ENDPOINT_UNPUBLISHED']}]"
        )
        csw_auth = CatalogueServiceWebAuthentication(token=app.config["CLIENT_AUTH_TOKEN"]["access_token"])
        csw = CatalogueServiceWeb(app.config["CSW_ENDPOINT_UNPUBLISHED"], auth=csw_auth)
        csw.getrecordbyid(id=[options["record"]], outputschema="http://www.isotc211.org/2005/gmd")
        if len(csw.records) != 1:
            # TODO: Add error
            raise RuntimeError(f"No record with identifier [{options['record']}] exists in CSW catalogue")
        record_xml = csw.records[options["record"]].xml.decode()
        app.logger.info(f"Reverse engineering metadata config from metadata record")
        record_config = MetadataRecord(record=record_xml).make_config().config
        app.logger.debug("Metadata record configuration:")
        app.logger.debug(record_config)

        app.logger.info(f"Checking destination directory [{options['path']}] exists")
        options["path"] = Path(options["path"])
        if not options["path"].exists():
            # TODO: Add error
            raise RuntimeError(f"specified export path [{options['path']}] does not exist")
        options["path"] = options["path"].joinpath(
            f"ADD-metadata-record-{options['record']}-{datetime.utcnow().isoformat()}.json"
        )
        app.logger.info(f"Saving record as [{options['path'].absolute()}]")
        with open(str(options["path"]), "w",) as export_file:
            json.dump(record_config, export_file, indent=4, default=str)
        echo(
            f"{click_style('Successfully exported', fg='green')} record {click_style(options['record'], fg='cyan')} - "
            f"{click_style(options['record'], fg='magenta')} to {click_style(str(options['path']), fg='magenta')}"
        )
        # TODO: Expand output message (editing instructions next step in workflow etc.
        # Do not change the ID unless you want a new record (do this if cloning a record

    # TODO: Add record and path as command arguments for completeness
    @records_cli_group.command("remove")
    def remove_record():
        """Delete a record from the unpublished catalogue."""
        # TODO: Refactor to extract common function
        csw_auth = CatalogueServiceWebAuthentication(token=app.config["CLIENT_AUTH_TOKEN"]["access_token"])
        csw = CatalogueServiceWeb(app.config["CSW_ENDPOINT_UNPUBLISHED"], auth=csw_auth)
        csw.getrecords2(
            typenames="gmd:MD_Metadata",
            esn="full",
            resulttype="results",
            outputschema="http://www.isotc211.org/2005/gmd",
            maxrecords=100,
        )
        records = {}
        for record in csw.records:
            records[csw.records[record].identifier] = csw.records[record].identification.title
        _records = {f"* {click_style(k, fg='cyan')} - {click_style(v, fg='magenta')}": k for k, v in records.items()}

        # TODO:
        # Create a Catalogue and Record class

        # TODO: Refactor to remove options dict and have one set of questions
        options = {"record": None, "title": None}
        selected_record = prompt(
            [
                inquirer_list(
                    name="record", message="Which record would like to remove?", choices=list(_records.items()),
                ),
            ]
        )
        if selected_record is None:
            raise Abort()
        options["record"] = selected_record["record"]
        options["title"] = records[options["record"]]
        app.logger.info(f"selected record [{options['record']}]")

        click_confirm(
            f"{click_style('Are you sure you want to remove', fg='yellow')} record "
            f"[{click_style(options['record'], fg='cyan')}] '{click_style(options['title'], fg='magenta')}'?",
            abort=True,
        )

        # TODO: Refactor this into common code
        app.logger.info(
            f"Deleting record [{options['record']}] in CSW endpoint [{app.config['CSW_ENDPOINT_PUBLISHED']}]"
        )
        csw.transaction(ttype="delete", identifier=options["record"])
        csw.results["deleted"] = int(
            ElementTree(fromstring(csw.response)).xpath(
                "/csw:TransactionResponse/csw:TransactionSummary/csw:totalDeleted/text()", namespaces=csw_namespaces,
            )[0]
        )
        # noinspection PyTypeChecker
        if csw.results["deleted"] != 1:
            # TODO: Raise proper error
            app.logger.error(f"Unable to remove record in CSW")
            raise RuntimeError("Unable to remove record in CSW")
        echo(f"{click_style('Successfully removed', fg='green')} record [{click_style(options['record'], fg='cyan')}].")

    # TODO: Add record and path as command arguments for completeness
    @records_cli_group.command("publish")
    def publish_record():
        """Copy a record from the unpublished to published catalogue."""
        # TODO: Refactor to extract common function
        csw_auth = CatalogueServiceWebAuthentication(token=app.config["CLIENT_AUTH_TOKEN"]["access_token"])
        csw = CatalogueServiceWeb(app.config["CSW_ENDPOINT_UNPUBLISHED"], auth=csw_auth)
        csw.getrecords2(
            typenames="gmd:MD_Metadata",
            esn="full",
            resulttype="results",
            outputschema="http://www.isotc211.org/2005/gmd",
            maxrecords=100,
        )
        records = {}
        for record in csw.records:
            records[csw.records[record].identifier] = csw.records[record].identification.title
        _records = {f"* {click_style(k, fg='cyan')} - {click_style(v, fg='magenta')}": k for k, v in records.items()}

        # TODO:
        # Create a Catalogue and Record class

        # TODO: Refactor to remove options dict and have one set of questions
        options = {"record": None, "title": None}
        selected_record = prompt(
            [
                inquirer_list(
                    name="record", message="Which record would like to publish?", choices=list(_records.items()),
                ),
            ]
        )
        if selected_record is None:
            raise Abort()
        options["record"] = selected_record["record"]
        options["title"] = records[options["record"]]
        app.logger.info(f"selected record [{options['record']}]")

        # TODO: Refactor this into common code
        app.logger.info(
            f"Requesting record [{options['record']}] from CSW endpoint [{app.config['CSW_ENDPOINT_UNPUBLISHED']}]"
        )
        csw_auth = CatalogueServiceWebAuthentication(token=app.config["CLIENT_AUTH_TOKEN"]["access_token"])
        csw = CatalogueServiceWeb(app.config["CSW_ENDPOINT_UNPUBLISHED"], auth=csw_auth)
        csw.getrecordbyid(id=[options["record"]], outputschema="http://www.isotc211.org/2005/gmd")
        if len(csw.records) != 1:
            # TODO: Add error
            raise RuntimeError(f"No record with identifier [{options['record']}] exists in CSW catalogue")
        record_xml = csw.records[options["record"]].xml.decode()

        # TODO: Refactor this to use a single CSW instance
        csw_auth = CatalogueServiceWebAuthentication(token=app.config["CLIENT_AUTH_TOKEN"]["access_token"])
        csw = CatalogueServiceWeb(app.config["CSW_ENDPOINT_PUBLISHED"], auth=csw_auth)

        app.logger.info(
            f"Inserting record [{options['record']}] into CSW repository [{app.config['CSW_ENDPOINT_PUBLISHED']}]"
        )

        csw.transaction(ttype="insert", typename="gmd:MD_Metadata", record=record_xml)
        # noinspection PyTypeChecker
        if len(csw.results["insertresults"]) != 1:
            # TODO: Raise proper error
            app.logger.error(f"Unable to publish record in CSW")
            raise RuntimeError("Unable to publish record in CSW")
        echo(
            f"{click_style('Successfully published', fg='green')} record "
            f"[{click_style(csw.results['insertresults'][0], fg='cyan')}]."
        )

    # TODO: Add record and path as command arguments for completeness
    @records_cli_group.command("retract")
    def retract_record():
        """Delete a record from the published catalogue."""
        # TODO: Refactor to extract common function
        csw_auth = CatalogueServiceWebAuthentication(token=app.config["CLIENT_AUTH_TOKEN"]["access_token"])
        csw = CatalogueServiceWeb(app.config["CSW_ENDPOINT_PUBLISHED"], auth=csw_auth)
        csw.getrecords2(
            typenames="gmd:MD_Metadata",
            esn="full",
            resulttype="results",
            outputschema="http://www.isotc211.org/2005/gmd",
            maxrecords=100,
        )
        records = {}
        for record in csw.records:
            records[csw.records[record].identifier] = csw.records[record].identification.title
        _records = {f"* {click_style(k, fg='cyan')} - {click_style(v, fg='magenta')}": k for k, v in records.items()}

        # TODO:
        # Create a Catalogue and Record class

        # TODO: Refactor to remove options dict and have one set of questions
        options = {"record": None, "title": None}
        selected_record = prompt(
            [
                inquirer_list(
                    name="record", message="Which record would like to retract?", choices=list(_records.items()),
                ),
            ]
        )
        if selected_record is None:
            raise Abort()
        options["record"] = selected_record["record"]
        options["title"] = records[options["record"]]
        app.logger.info(f"selected record [{options['record']}]")

        # TODO: Refactor this into common code
        app.logger.info(
            f"Deleting record [{options['record']}] in CSW endpoint [{app.config['CSW_ENDPOINT_PUBLISHED']}]"
        )
        csw.transaction(ttype="delete", identifier=options["record"])
        csw.results["deleted"] = int(
            ElementTree(fromstring(csw.response)).xpath(
                "/csw:TransactionResponse/csw:TransactionSummary/csw:totalDeleted/text()", namespaces=csw_namespaces,
            )[0]
        )
        # noinspection PyTypeChecker
        if csw.results["deleted"] != 1:
            # TODO: Raise proper error
            app.logger.error(f"Unable to retract record in CSW")
            raise RuntimeError("Unable to retract record in CSW")
        echo(
            f"{click_style('Successfully retracted', fg='green')} record [{click_style(options['record'], fg='cyan')}]."
        )

    # Routes
    #

    # noinspection PyUnusedLocal
    @app.errorhandler(404)
    def page_not_found(e):
        """General 404 error handler"""
        # noinspection PyUnresolvedReferences
        return render_template("app/errors/404.j2"), 404

    @app.route("/feedback/")
    def feedback():
        return render_template("app/feedback.j2")

    @freezer.register_generator
    def feedback():
        yield {}

    @app.route("/legal/<string:policy>/")
    def legal(policy: str):
        if policy == "privacy":
            return render_template("app/legal/privacy.j2")
        elif policy == "copyright":
            return render_template("app/legal/copyright.j2")
        elif policy == "cookies":
            return render_template("app/legal/cookies.j2")

        # noinspection PyUnresolvedReferences
        return render_template("app/errors/404.j2"), 404

    @freezer.register_generator
    def legal():
        yield {"policy": "privacy"}
        yield {"policy": "copyright"}
        yield {"policy": "cookies"}

    @app.route("/collections/<uuid:collection_id>/")
    def view_collection(collection_id: str):
        collection_id = markup_escape(collection_id)
        if collection_id != "e74543c0-4c4e-4b41-aa33-5bb2f67df389":
            # TODO: Add specific error
            # noinspection PyUnresolvedReferences
            return render_template("app/errors/404.j2"), 404

        # TODO: Store this data somewhere (config file to being with?)
        # noinspection PyDictCreation
        collection = {
            "id": "e74543c0-4c4e-4b41-aa33-5bb2f67df389",
            "title": "SCAR Antarctic Digital Database (ADD)",
            "description": "The Scientific Committee on Antarctic Research (SCAR) Antarctic Digital Database (ADD) "
            "aims to provide a seamless topographic map compiled from the best available international geographic "
            "information for all areas. It covers Antarctica south of 60°S.\n\n"
            "The SCAR ADD consists of geographic information layers including:\n\n"
            "* coastline\n"
            "* ice-shelf grounding line\n"
            "* rock outcrop\n"
            "* contours\n"
            "\n\n"
            "See the [SCAR website](https://scar.org/data-products/antarctic-digital-database/) for more information.",
            "topic": "Topographic mapping",
            "publishers": ["Mapping and Geographic Information Centre (MAGIC)"],
        }

        # transform collection data
        collection["description"] = markdown(collection["description"], output_format="html5")

        # TODO: Get collection items via a CSW search for a keyword - for now include all items
        collection["items"] = []
        app.logger.info(f"Requesting all records from CSW endpoint [{app.config['CSW_ENDPOINT_PUBLISHED']}]")
        csw = CatalogueServiceWeb(app.config["CSW_ENDPOINT_PUBLISHED"])
        csw.getrecords2(
            typenames="gmd:MD_Metadata",
            esn="full",
            resulttype="results",
            outputschema="http://www.isotc211.org/2005/gmd",
            maxrecords=100,
        )

        for record in csw.records.values():
            record_xml = record.xml.decode()
            app.logger.info(f"Reverse engineering metadata config from metadata record")
            record_config = MetadataRecord(record=record_xml).make_config().config
            app.logger.debug("Metadata record configuration:")
            app.logger.debug(record_config)

            # TODO: Refactor as part of view_item
            item = record_config
            for index, item_date in enumerate(item["resource"]["dates"]):
                if isinstance(item_date["date"], datetime):
                    item_date["display_value"] = item_date["date"].isoformat(sep=" ")
                elif isinstance(item_date["date"], date):
                    item_date["display_value"] = item_date["date"].isoformat()
                if "date_precision" in item_date and item_date["date_precision"]:
                    item_date["display_value"] = item_date["date"].year
                item["resource"]["dates"][index] = item_date

            item["resource"]["dates_by_type"] = {}
            for item_date in item["resource"]["dates"]:
                item["resource"]["dates_by_type"][item_date["date_type"]] = item_date

            for index, contact in enumerate(item["resource"]["contacts"]):
                if "organisation" in contact and "name" in contact["organisation"]:
                    contact["organisation"]["display_name"] = contact["organisation"]["name"]
                    if (
                        contact["organisation"]["name"]
                        == "Mapping and Geographic Information Centre, British Antarctic Survey"
                    ):
                        contact["organisation"]["display_name"] = "Mapping and Geographic Information Centre (MAGIC)"
                item["resource"]["contacts"][index] = contact

            item["resource"]["contacts_by_role"] = {}
            for item_contact in item["resource"]["contacts"]:
                for item_contact_role in item_contact["role"]:
                    if item_contact_role not in list(item["resource"]["contacts_by_role"].keys()):
                        item["resource"]["contacts_by_role"][item_contact_role] = []
                    item["resource"]["contacts_by_role"][item_contact_role].append(item_contact)

            collection["items"].append(item)

        # noinspection PyUnresolvedReferences
        return render_template(f"app/collection-details.j2", collection_id=collection_id, collection=collection,)

    @freezer.register_generator
    def view_collection():
        # TODO: Make dynamic
        yield {"collection_id": "e74543c0-4c4e-4b41-aa33-5bb2f67df389"}

    @app.route("/items/<uuid:item_id>/")
    def view_item(item_id: str):
        """Displays details about an item from a CSW record"""
        item_id = markup_escape(item_id)
        csw = CatalogueServiceWeb(app.config["CSW_ENDPOINT_PUBLISHED"])
        app.logger.info(f"Requesting record [{item_id}] from CSW endpoint [{app.config['CSW_ENDPOINT_PUBLISHED']}]")
        csw.getrecordbyid(id=[item_id], outputschema="http://www.isotc211.org/2005/gmd")
        if len(csw.records) != 1:
            # TODO: Add specific error
            # noinspection PyUnresolvedReferences
            return render_template("app/errors/404.j2"), 404
        item_xml = csw.records[item_id].xml.decode()
        item = MetadataRecord(record=item_xml).make_config().config

        # Transform item information to make use in templates more straightforward

        # TODO: Sort all this date handling out so we check whether things are dates or datetimes
        _date_stamp = {
            "value": item["date_stamp"],
            "display_value": item["date_stamp"].isoformat(sep=" ", timespec="seconds"),
        }
        item["date_stamp"] = _date_stamp
        for index, item_date in enumerate(item["resource"]["dates"]):
            if isinstance(item_date["date"], datetime):
                item_date["display_value"] = item_date["date"].isoformat(sep=" ")
            elif isinstance(item_date["date"], date):
                item_date["display_value"] = item_date["date"].isoformat()
            if "date_precision" in item_date and item_date["date_precision"]:
                item_date["display_value"] = item_date["date"].year
            item["resource"]["dates"][index] = item_date

        item["resource"]["dates_by_type"] = {}
        for item_date in item["resource"]["dates"]:
            item["resource"]["dates_by_type"][item_date["date_type"]] = item_date
        item["resource"]["extent"]["temporal"]["period"]["start"] = {
            "value": item["resource"]["extent"]["temporal"]["period"]["start"],
            # TODO: Detect if datetime has hours/minutes/seconds - if not treat as date and hide times
            "display_value": item["resource"]["extent"]["temporal"]["period"]["start"].isoformat(),
        }
        item["resource"]["extent"]["temporal"]["period"]["end"] = {
            "value": item["resource"]["extent"]["temporal"]["period"]["end"],
            # TODO: Detect if datetime has hours/minutes/seconds - if not treat as date and hide times
            "display_value": item["resource"]["extent"]["temporal"]["period"]["end"].isoformat(),
        }

        # TODO: Include other periodic terms
        if "maintenance" not in item["resource"].keys():
            item["resource"]["maintenance"] = {}
        item["resource"]["maintenance"]["status"] = "unknown"
        if "maintenance_frequency" in item["resource"]["maintenance"].keys():
            if item["resource"]["maintenance"]["maintenance_frequency"] == "asNeeded":
                item["resource"]["maintenance"]["status"] = "current"
            elif item["resource"]["maintenance"]["maintenance_frequency"] == "biannually":
                item["resource"]["maintenance"]["status"] = "overdue"
                next_release_expected = item["resource"]["dates_by_type"]["released"]["date"] + relativedelta(months=+6)
                if datetime.today() <= next_release_expected:
                    item["resource"]["maintenance"]["status"] = "current"

        for index, contact in enumerate(item["resource"]["contacts"]):
            if "organisation" in contact and "name" in contact["organisation"]:
                contact["organisation"]["display_name"] = contact["organisation"]["name"]
                if (
                    contact["organisation"]["name"]
                    == "Mapping and Geographic Information Centre, British Antarctic Survey"
                ):
                    contact["organisation"]["display_name"] = "Mapping and Geographic Information Centre (MAGIC)"
            item["resource"]["contacts"][index] = contact

        item["resource"]["contacts_by_role"] = {}
        for item_contact in item["resource"]["contacts"]:
            for item_contact_role in item_contact["role"]:
                if item_contact_role not in list(item["resource"]["contacts_by_role"].keys()):
                    item["resource"]["contacts_by_role"][item_contact_role] = []
                item["resource"]["contacts_by_role"][item_contact_role].append(item_contact)

        item["resource"]["identifiers_by_type"] = {}
        if "identifiers" in item["resource"].keys():
            for item_identifier in item["resource"]["identifiers"]:
                if "title" in item_identifier.keys():
                    item["resource"]["identifiers_by_type"][item_identifier["title"]] = item_identifier

        if "constraints" in item["resource"].keys():
            for item_constraint in item["resource"]["constraints"]["usage"]:
                if "copyright_licence" in item_constraint:
                    # https://gitlab.data.bas.ac.uk/uk-pdc/metadata-infrastructure/metadata-standards/issues/150 patch
                    if item_constraint["copyright_licence"]["href"] == "https://creativecommons.org/licenses/by/4.0/":
                        item_constraint["copyright_licence"]["code"] = "cc-by-4.0"
                    item_constraint["copyright_licence"]["reformat_statement"] = False
                    if (
                        item_constraint["copyright_licence"]["statement"]
                        == "This information is licensed under the Create Commons Attribution 4.0 International "
                        "Licence (CC BY 4.0). To view this licence, visit https://creativecommons.org/licenses/by/4.0/"
                    ):
                        item_constraint["copyright_licence"]["reformat_statement"] = True
                    item["resource"]["constraints"]["copyright"] = item_constraint["copyright_licence"]

                if "required_citation" in item_constraint:
                    # TODO: Need proper way to detect non-standard citations
                    item_constraint["required_citation"]["reformat_statement"] = True
                    item["resource"]["constraints"]["citation"] = item_constraint["required_citation"]

                    # Huge hack because candidate record doesn't have a proper DOI
                    # TODO: Remove this first if clause
                    if (
                        "doi" in list(item["resource"]["identifiers_by_type"].keys())
                        and item["file_identifier"] == "86bd7a1a-845d-48a9-8d71-59fdf7290556"
                    ):
                        item["resource"]["constraints"]["citation"]["elements"] = {
                            "id": "https://doi.org/10.5285/86bd7a1a-845d-48a9-8d71-59fdf7290556",
                            "author": [{"family": "Watson", "given": "Constance"}],
                            "abstract": "Coastline of Antarctica encoded as a polygon. This abstract, and the dataset to "
                            "which it belongs, is fictitious. This is a candidate record to develop and validate discovery "
                            "level metadata for SCAR Antarctic Digital Database (ADD) datasets. See the ADD website for "
                            "real datasets (https://add.scar.org).",
                            "DOI": "10.5285/86BD7A1A-845D-48A9-8D71-59FDF7290556",
                            "publisher": "Mapping and Geographic Information Centre, British Antarctic Survey",
                            "title": "Antarctic Coastline (Polygon) - (MAGIC ADD candidate metadata record)",
                            "URL": "https://data.bas.ac.uk/item/86bd7a1a-845d-48a9-8d71-59fdf7290556",
                        }
                    elif "doi" in list(item["resource"]["identifiers_by_type"].keys()):
                        cite_proc = requests.get(
                            item["resource"]["identifiers_by_type"]["doi"]["href"],
                            headers={"accept": "application/vnd.citationstyles.csl+json"},
                        )
                        cite_proc.raise_for_status()
                        item["resource"]["constraints"]["citation"]["elements"] = cite_proc.json

        iso_topic_keywords = {
            "terms": [],
            "type": "theme",
            "thesaurus": {"title": {"value": "ISO Topics"}},
        }
        for iso_topic in item["resource"]["topics"]:
            iso_topic_keywords["terms"].append({"term": str(iso_topic).capitalize()})
        item["resource"]["keywords"].append(iso_topic_keywords)

        item["resource"]["special_keywords"] = {}
        descriptive_keywords_indexes_to_remove = []
        for index, keywords in enumerate(item["resource"]["keywords"]):
            if (
                "thesaurus" in keywords
                and "title" in keywords["thesaurus"]
                and "href" in keywords["thesaurus"]["title"]
            ):
                if keywords["thesaurus"]["title"]["href"] == "http://www.eionet.europa.eu/gemet/inspire_themes":
                    keywords["thesaurus"]["title"]["display_value"] = "INSPIRE Themes"
                elif (
                    keywords["thesaurus"]["title"]["href"]
                    == "https://earthdata.nasa.gov/about/gcmd/global-change-master-directory-gcmd-keywords"
                ):
                    if keywords["type"] == "theme":
                        keywords["thesaurus"]["title"]["display_value"] = "GCMD Science Keywords"
                    elif keywords["type"] == "place":
                        keywords["thesaurus"]["title"]["display_value"] = "GCMD Location Keywords"
                elif keywords["thesaurus"]["title"]["href"] == "http://vocab.nerc.ac.uk/collection/T01/1/":
                    descriptive_keywords_indexes_to_remove.append(index)
                    item["resource"]["special_keywords"]["topic"] = {"display_value": keywords["terms"][0]["term"]}
                elif keywords["thesaurus"]["title"]["href"] == "http://vocab.nerc.ac.uk/collection/T02/1/":
                    descriptive_keywords_indexes_to_remove.append(index)
                    item["resource"]["special_keywords"]["collection"] = {"display_value": keywords["terms"][0]["term"]}
                    if (
                        keywords["terms"][0]["href"]
                        == "http://vocab.nerc.ac.uk/collection/T02/1/8e91de62-b6e3-402e-b11f-73d2c1f37cff/"
                    ):
                        item["resource"]["special_keywords"]["collection"][
                            "href"
                        ] = "http://data.bas.ac.uk/collections/e74543c0-4c4e-4b41-aa33-5bb2f67df389/"
            elif (
                "thesaurus" in keywords
                and "title" in keywords["thesaurus"]
                and "value" in keywords["thesaurus"]["title"]
                and keywords["thesaurus"]["title"]["value"] == "ISO Topics"
            ):
                keywords["thesaurus"]["title"]["display_value"] = "ISO Topics"
        for index_to_remove in sorted(descriptive_keywords_indexes_to_remove, reverse=True):
            item["resource"]["keywords"].pop(index_to_remove)

        item["resource"]["keywords_by_type"] = {}
        for item_keywords in item["resource"]["keywords"]:
            if item_keywords["type"] not in list(item["resource"]["keywords_by_type"].keys()):
                item["resource"]["keywords_by_type"][item_keywords["type"]] = []
            item["resource"]["keywords_by_type"][item_keywords["type"]].append(item_keywords)

        item["metadata_links"] = {
            "iso_xml": url_for(".view_record", record_format="iso-xml", record_id=item["file_identifier"],),
            "iso_html": url_for(".view_record", record_format="iso-html", record_id=item["file_identifier"],),
            "iso_rubric": url_for(".view_record", record_format="iso-rubric", record_id=item["file_identifier"],),
        }

        # TODO: Extract to issue for defining what open access is
        # _open_access = {
        #     "code": "open-access",
        #     "code_space": "data.bas.ac.uk",
        #     "title": {"value": "data.bas.ac.uk open access measure"},
        #     "dates": [{"date": date(2020, 4, 14), "date_type": "publication"}],
        #     "pass": False,
        # }
        # if (
        #     "released" in item["resource"]["dates_by_type"]
        #     and datetime.today() >= item["resource"]["dates_by_type"]["released"]["date"]
        #     and "copyright" in item["resource"]["constraints"]
        #     and item["resource"]["constraints"]["copyright"]["code"] == "cc-by-4.0"
        # ):
        #     _open_access["pass"] = True
        # item["resource"]["measures"].append(_open_access)

        item["resource"]["measures_by_code"] = {}
        if "measures" in item["resource"].keys():
            for item_measure in item["resource"]["measures"]:
                item["resource"]["measures_by_code"][
                    f"{item_measure['code_space']}-{item_measure['code']}"
                ] = item_measure

        if "transfer_options" in item["resource"].keys():
            # TODO: We will link formats to transfer options using IDs in future, but for now formats are ignored/faked
            # TODO: In the future use HEAD request and use content-type header to determine format properly
            for index, transfer_option in enumerate(item["resource"]["transfer_options"]):
                transfer_option["format"] = {"format": None, "version": None}

                if "online_resource" in transfer_option and "title" in transfer_option["online_resource"]:
                    if transfer_option["online_resource"]["title"] == "GeoPackage":
                        transfer_option["format"]["format"] = "gpkg"
                    elif transfer_option["online_resource"]["title"] == "Shapefile":
                        transfer_option["format"]["format"] = "shp"
                    elif transfer_option["online_resource"]["title"] == "PDF":
                        transfer_option["format"]["format"] = "pdf"
                    elif transfer_option["online_resource"]["title"] == "Web Map Service (WMS)":
                        transfer_option["format"]["format"] = "wms"
                        url_parsed = url_parse(transfer_option["online_resource"]["href"])
                        query_string_parsed = query_string_parse(url_parsed.query)
                        transfer_option["format"][
                            "endpoint"
                        ] = f"{url_parsed.scheme}://{url_parsed.netloc}{url_parsed.path}"
                        transfer_option["format"]["layer"] = None
                        if "layer" in query_string_parsed and len(query_string_parsed["layer"]) == 1:
                            transfer_option["format"]["layer"] = query_string_parsed["layer"][0]

                item["resource"]["transfer_options"][index] = transfer_option

            # TODO: Formalise preference logic
            item_formats = []
            formats_preference = ["wms", "gpkg", "shp", "csv"]
            for transfer_option in item["resource"]["transfer_options"]:
                if "format" in transfer_option and "format" in transfer_option["format"]:
                    if transfer_option["format"]["format"] not in item_formats:
                        item_formats.append(transfer_option["format"]["format"])
            for preferred_format in formats_preference:
                if preferred_format in item_formats:
                    item["resource"]["preferred_transfer_option_format"] = preferred_format
                    break

        # noinspection PyUnresolvedReferences
        return render_template(f"app/item-details.j2", item_id=item_id, item=item)

    @freezer.register_generator
    def view_item():
        # TODO: Consolidate code
        app.logger.info(f"Requesting all records from CSW endpoint [{app.config['CSW_ENDPOINT_PUBLISHED']}]")
        csw = CatalogueServiceWeb(app.config["CSW_ENDPOINT_PUBLISHED"])
        csw.getrecords2(
            typenames="gmd:MD_Metadata",
            esn="brief",
            resulttype="results",
            outputschema="http://www.isotc211.org/2005/gmd",
            maxrecords=100,
        )
        app.logger.info(f"Collecting all record IDs from CSW response")
        record_ids = []
        for record in csw.records.values():
            record_xml = record.xml.decode()
            record_xml = fromstring(record_xml)
            record_ids.append(
                record_xml.xpath(
                    "/gmd:MD_Metadata/gmd:fileIdentifier/gco:CharacterString/text()", namespaces=record_xml.nsmap
                )[0]
            )
        items = []
        for record_id in record_ids:
            items.append({"item_id": record_id})
        return items

    @app.route("/records/<record_format>/<uuid:record_id>.xml")
    def view_record(
        record_format: str, record_id: str,
    ):
        """Displays a CSW record in a given format"""
        record_format = markup_escape(record_format)
        record_id = markup_escape(record_id)

        app.logger.info(f"Requesting record [{record_id}] from CSW endpoint [{app.config['CSW_ENDPOINT_PUBLISHED']}]")
        csw = CatalogueServiceWeb(app.config["CSW_ENDPOINT_PUBLISHED"])
        csw.getrecordbyid(id=[record_id], outputschema="http://www.isotc211.org/2005/gmd")
        if len(csw.records) != 1:
            # TODO: Add specific error
            # noinspection PyUnresolvedReferences
            return render_template("app/errors/404.j2"), 404

        record_xml = csw.records[record_id].xml.decode()
        if record_format == "iso-xml":
            app.logger.info(f"Return CSW response as ISO XML")
            return Response(record_xml, mimetype="text/xml", content_type="text/xml; charset=utf-8")
        elif record_format == "iso-html":
            app.logger.info(f"Return CSW response as ISO HTML (NOAA ISO XML to HTML stylesheet)")
            record_iso_html = ElementTree(fromstring(record_xml))
            record_iso_html_root = record_iso_html.getroot()
            record_iso_html_root.addprevious(
                ProcessingInstruction(
                    "xml-stylesheet", 'type="text/xsl" href="/static/xsl/iso-html/xml-to-html-ISO.xsl"',
                )
            )
            record_iso_html_xml = tostring(record_iso_html, pretty_print=True, xml_declaration=True, encoding="utf-8",)
            return Response(record_iso_html_xml, mimetype="text/xml", content_type="text/xml; charset=utf-8",)
        elif record_format == "iso-rubric":
            app.logger.info(f"Return CSW response as ISO Rubric (NOAA ISO SpiralTracker Rubric stylesheet)")
            record_iso_rubric = ElementTree(fromstring(record_xml))
            record_iso_rubric_root = record_iso_rubric.getroot()
            record_iso_rubric_root.addprevious(
                ProcessingInstruction(
                    "xml-stylesheet", 'type="text/xsl" href="/static/xsl/iso-rubric/isoRubricHTML.xsl"',
                )
            )
            record_iso_rubric_xml = tostring(
                record_iso_rubric, pretty_print=True, xml_declaration=True, encoding="utf-8",
            )
            return Response(record_iso_rubric_xml, mimetype="text/xml", content_type="text/xml; charset=utf-8",)

        # TODO: Add specific error
        # noinspection PyUnresolvedReferences
        return render_template("app/errors/404.j2"), 404

    @freezer.register_generator
    def view_record():
        # TODO: Consolidate code
        app.logger.info(f"Requesting all records from CSW endpoint [{app.config['CSW_ENDPOINT_PUBLISHED']}]")
        csw = CatalogueServiceWeb(app.config["CSW_ENDPOINT_PUBLISHED"])
        csw.getrecords2(
            typenames="gmd:MD_Metadata",
            esn="brief",
            resulttype="results",
            outputschema="http://www.isotc211.org/2005/gmd",
            maxrecords=100,
        )
        app.logger.info(f"Collecting all record IDs from CSW response")
        record_ids = []
        for record in csw.records.values():
            record_xml = record.xml.decode()
            record_xml = fromstring(record_xml)
            record_ids.append(
                record_xml.xpath(
                    "/gmd:MD_Metadata/gmd:fileIdentifier/gco:CharacterString/text()", namespaces=record_xml.nsmap
                )[0]
            )
        items = []
        for record_id in record_ids:
            items.append({"record_id": record_id, "record_format": "iso-xml"})
            items.append({"record_id": record_id, "record_format": "iso-html"})
            items.append({"record_id": record_id, "record_format": "iso-rubric"})
        return items

    # TODO: Now, have one CSW route with a path parameter for a catalogue
    # TODO: Later, Merge unpublished and published catalogues together with optional auth.
    # If unauthenticated, prevent transactions and use virtual catalogue where published date is set and past today

    @app.route("/csw/unpublished", methods=["GET", "POST"])
    @auth("Records.Read.All")
    def csw_server_unpublished():
        """embedded PyCSW instance for unpublished records"""
        app.logger.info(f"Running pycsw version: {pycsw_version}")

        app.logger.info("Katy")

        # TODO: Create our own CSW Server and Client classes
        csw = Csw(rtconfig=app.config["CSW_CONFIG_UNPUBLISHED"], env=request.environ, version="2.0.2",)

        app.logger.info("Joss")

        app.logger.info(request.data)

        if request.method == "GET":
            csw.requesttype = "GET"
            csw.kvp = request.args.to_dict()
        elif request.method == "POST":
            csw.requesttype = "POST"
            csw.request = request.data

            # Detect CSW transaction
            # TODO: Replace this with proper XML parsing
            if "csw:Transaction" in csw.request.decode():
                # Long term this will be replaced by [1]
                # [1] https://gitlab.data.bas.ac.uk/web-apps/flask-extensions/flask-azure-oauth/issues/17
                # TODO: Move scope value to config value
                if "Records.ReadWrite.All" not in current_token.scopes:
                    raise ApiAuthTokenScopesInsufficient().response()

        # http_status_code, response = csw.dispatch_wsgi()
        http_status_code, response = csw.dispatch()

        response = response.decode()

        app.logger.info("Lois")
        app.logger.info(response)

        return response, http_status_code, {"Content-type": csw.contenttype}

    # TODO: Require additional scopes for write operations
    @app.route("/csw/published", methods=["GET", "POST"])
    @auth(optional=True)
    def csw_server_published():
        """embedded PyCSW instance for published records"""
        app.logger.info(f"Running pycsw version: {pycsw_version}")

        csw = Csw(rtconfig=app.config["CSW_CONFIG_PUBLISHED"], env=request.environ, version="2.0.2",)
        if request.method == "GET":
            csw.requesttype = "GET"
            csw.kvp = request.args.to_dict()
        elif request.method == "POST":
            csw.requesttype = "POST"
            csw.request = request.data

            # Detect CSW transaction
            # TODO: Replace this with proper XML parsing
            if "csw:Transaction" in csw.request.decode():
                # Long term this will be replaced by [1]
                # [1] https://gitlab.data.bas.ac.uk/web-apps/flask-extensions/flask-azure-oauth/issues/17
                # TODO: Move scope value to config value
                if "Records.Publish.All" not in current_token.scopes:
                    app.logger.info("No scope to publish")
                    app.logger.info(current_token.scopes)
                    raise ApiAuthTokenScopesInsufficient().response()

        http_status_code, response = csw.dispatch()
        return response, http_status_code, {"Content-type": csw.contenttype}

    return app
