"""
OGC Catalogue Services for the Web (CSW) classes/methods

Warning: Here be dragons!

These classes/methods are considered 'hazardous material' meaning they are experimental, inefficient and inelegant.
They are intended to workaround limitations in other packages (in this case PyCSW and OWSLib) and from these, determine
changes needed within these packages.

As these classes/methods can change frequently, and are not intended for long term use, they are not covered by tests
and exempted from code coverage (see `.coverage`). As these classes/methods are used to workaround issues, they often
use awkward, non-ideal or 'risky' code that's frowned upon and doesn't follow best practices. For example mocking
methods that are usually reserved for testing environments are used in normal operation to workaround limitations in
3rd party packages.

Once a solution to a problem is found it should be upstreamed into the relevant package and removed from here. It's
expected that all 'hazmat' classes/methods will eventually be removed as time allows.
"""
import os
import sys
import warnings
import logging
from urllib.parse import urlencode

import requests

from unittest import mock

# noinspection PyPackageRequirements
# Exempting Bandit security issue (Using Element to parse untrusted XML data is known to be vulnerable to XML attacks)
#
# We don't currently allow untrusted/user-provided XML so this is not a risk
from lxml.etree import tostring, fromstring, ElementTree, Element  # nosec
from owslib.util import Authentication
from owslib.csw import (
    CatalogueServiceWeb as _CatalogueServiceWeb,
    namespaces as csw_namespaces,
    namespaces,
    schema_location,
    outputformat,
)
from bas_metadata_library.standards.iso_19115_common import Namespaces

# For overloaded CSW class
import inspect
from io import BytesIO
from owslib.etree import etree
from owslib import util as owslib_util
from owslib import ows
from owslib.util import cleanup_namespaces, bind_url, add_namespaces, openURL, http_post
from owslib import fes
from owslib.util import OrderedDict
from owslib.csw import (
    outputformat as csw_outputformat,
    schema_location as csw_schema_location,
)
from owslib.iso import MD_Metadata, FC_FeatureCatalogue
from pycsw.server import Csw as _Csw, LOGGER
from pycsw.plugins.profiles import profile as pprofile
from pycsw.core import util as pycsw_util
from pycsw.ogc.csw.csw2 import Csw2 as _Csw2
from pycsw.core import metadata

warnings.simplefilter(action="ignore", category=FutureWarning)

"""
Wrapped requests (request/request_post)

These methods use mocking to patch OWSLib calls to the requests library in order to add a bearer authorisation header 
if passed into the request.

Long term, this change should be made directly with OWSLib to support token based auth.
"""

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

    # print("November")
    # print(args)
    # print(kwargs)
    _ = original_request(*args, **kwargs)
    # print("request")
    # print(_.content[0:100])
    # print(_.content)
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

    # print("India")
    # print(args)
    # print(kwargs)

    _ = original_post(*args, **kwargs)
    # print("request 2")
    # print(_.content[0:100])
    return _


# noinspection PyUnusedLocal
def setup_logger(config=None):
    """
    Changes PyCSW logging destination to use stdout rather than a file

    This is for consistency with other components that use stdout and to follow the logging conventions for containers.

    Long term the logging destination should be a configuration option in PyCSW.
    """
    logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)


class CSWServer(_Csw):
    """
    PyCSW instance using the modified `setup_logging` method

    Long term the logging destination should be a configuration option in PyCSW.
    """

    def __init__(self, rtconfig=None, env=None, version="3.0.0"):
        with mock.patch("pycsw.core.log.setup_logger", side_effect=setup_logger()):
            super().__init__(rtconfig, env, version)

    def dispatch(self, writer=sys.stdout, write_headers=True):
        """ Handle incoming HTTP request """

        error = 0
        if self.requesttype == "GET":
            self.kvp = self.normalize_kvp(self.kvp)
            version_202 = "version" in self.kvp and self.kvp["version"] == "2.0.2"
            accept_version_202 = "acceptversions" in self.kvp and "2.0.2" in self.kvp["acceptversions"]
            if version_202 or accept_version_202:
                self.request_version = "2.0.2"
        elif self.requesttype == "POST":
            if self.request.find(b"cat/csw/2.0.2") != -1:
                self.request_version = "2.0.2"
            elif self.request.find(b"cat/csw/3.0") != -1:
                self.request_version = "3.0.0"

        if not isinstance(self.kvp, str) and "mode" in self.kvp and self.kvp["mode"] == "sru":
            self.mode = "sru"
            self.request_version = "2.0.2"
            LOGGER.info("SRU mode detected; processing request")
            self.kvp = self.sru().request_sru2csw(self.kvp)

        # noinspection PyTypeChecker
        if not isinstance(self.kvp, str) and "mode" in self.kvp and self.kvp["mode"] == "oaipmh":
            self.mode = "oaipmh"
            self.request_version = "2.0.2"
            LOGGER.info("OAI-PMH mode detected; processing request.")
            # noinspection PyAttributeOutsideInit
            self.oaiargs = dict((k, v) for k, v in self.kvp.items() if k)
            self.kvp = self.oaipmh().request(self.kvp)

        if self.request_version == "2.0.2":
            self.iface = Csw2(server_csw=self)
            self.context.set_model("csw")

        # configure transaction support, if specified in config
        self._gen_manager()

        # noinspection PyShadowingNames
        namespaces = self.context.namespaces
        ops = self.context.model["operations"]
        constraints = self.context.model["constraints"]
        # generate domain model
        # NOTE: We should probably avoid this sort of mutable state for WSGI
        if "GetDomain" not in ops:
            ops["GetDomain"] = self.context.gen_domains()

        # generate distributed search model, if specified in config
        if self.config.has_option("server", "federatedcatalogues"):
            LOGGER.info("Configuring distributed search")

            constraints["FederatedCatalogues"] = {"values": []}

            for fedcat in self.config.get("server", "federatedcatalogues").split(","):
                LOGGER.debug("federated catalogue: %s", fedcat)
                constraints["FederatedCatalogues"]["values"].append(fedcat)

        for key, value in self.outputschemas.items():
            get_records_params = ops["GetRecords"]["parameters"]
            get_records_params["outputSchema"]["values"].append(value.NAMESPACE)
            get_records_by_id_params = ops["GetRecordById"]["parameters"]
            get_records_by_id_params["outputSchema"]["values"].append(value.NAMESPACE)
            if "Harvest" in ops:
                harvest_params = ops["Harvest"]["parameters"]
                harvest_params["ResourceType"]["values"].append(value.NAMESPACE)

        LOGGER.info("Setting MaxRecordDefault")
        if self.config.has_option("server", "maxrecords"):
            constraints["MaxRecordDefault"]["values"] = [self.config.get("server", "maxrecords")]

        # load profiles
        if self.config.has_option("server", "profiles"):
            self.profiles = pprofile.load_profiles(
                os.path.join("pycsw", "plugins", "profiles"), pprofile.Profile, self.config.get("server", "profiles")
            )

            for prof in self.profiles["plugins"].keys():
                tmp = self.profiles["plugins"][prof](self.context.model, namespaces, self.context)

                key = tmp.outputschema  # to ref by outputschema
                self.profiles["loaded"][key] = tmp
                self.profiles["loaded"][key].extend_core(self.context.model, namespaces, self.config)

            LOGGER.debug("Profiles loaded: %s" % list(self.profiles["loaded"].keys()))

        # init repository
        # look for tablename, set 'records' as default
        if not self.config.has_option("repository", "table"):
            self.config.set("repository", "table", "records")

        repo_filter = None
        if self.config.has_option("repository", "filter"):
            repo_filter = self.config.get("repository", "filter")

        if self.config.has_option("repository", "source"):  # load custom repository
            rs = self.config.get("repository", "source")
            rs_modname, rs_clsname = rs.rsplit(".", 1)

            rs_mod = __import__(rs_modname, globals(), locals(), [rs_clsname])
            rs_cls = getattr(rs_mod, rs_clsname)

            try:
                self.repository = rs_cls(self.context, repo_filter)
                LOGGER.debug("Custom repository %s loaded (%s)", rs, self.repository.dbtype)
            except Exception as err:
                msg = "Could not load custom repository %s: %s" % (rs, err)
                LOGGER.exception(msg)
                error = 1
                code = "NoApplicableCode"
                locator = "service"
                text = "Could not initialize repository. Check server logs"

        else:  # load default repository
            self.orm = "sqlalchemy"
            from pycsw.core import repository

            try:
                LOGGER.info("Loading default repository")
                # noinspection PyAttributeOutsideInit
                self.repository = repository.Repository(
                    self.config.get("repository", "database"),
                    self.context,
                    self.environ.get("local.app_root", None),
                    self.config.get("repository", "table"),
                    repo_filter,
                )
                LOGGER.debug("Repository loaded (local): %s." % self.repository.dbtype)
            except Exception as err:
                msg = "Could not load repository (local): %s" % err
                LOGGER.exception(msg)
                error = 1
                code = "NoApplicableCode"
                locator = "service"
                text = "Could not initialize repository. Check server logs"

        if self.requesttype == "POST":
            LOGGER.debug("HTTP POST request")
            LOGGER.debug("CSW version: %s", self.iface.version)
            self.kvp = self.iface.parse_postdata(self.request)

        if isinstance(self.kvp, str):  # it's an exception
            error = 1
            locator = "service"
            text = self.kvp
            if self.kvp.find("the document is not valid") != -1 or self.kvp.find("document not well-formed") != -1:
                code = "NoApplicableCode"
            else:
                code = "InvalidParameterValue"

        LOGGER.debug("HTTP Headers:\n%s.", self.environ)
        LOGGER.debug("Parsed request parameters: %s", self.kvp)

        if not isinstance(self.kvp, str) and "mode" in self.kvp and self.kvp["mode"] == "opensearch":
            self.mode = "opensearch"
            LOGGER.info("OpenSearch mode detected; processing request.")
            self.kvp["outputschema"] = "http://www.w3.org/2005/Atom"

        if (len(self.kvp) == 0 and self.request_version == "3.0.0") or (len(self.kvp) == 1 and "config" in self.kvp):
            LOGGER.info("Turning on default csw30:Capabilities for base URL")
            self.kvp = {"service": "CSW", "acceptversions": "3.0.0", "request": "GetCapabilities"}
            http_accept = self.environ.get("HTTP_ACCEPT", "")
            if "application/opensearchdescription+xml" in http_accept:
                self.mode = "opensearch"
                self.kvp["outputschema"] = "http://www.w3.org/2005/Atom"

        if error == 0:
            # test for the basic keyword values (service, version, request)
            basic_options = ["service", "request"]
            request = self.kvp.get("request", "")
            own_version_integer = pycsw_util.get_version_integer(self.request_version)
            if self.request_version == "2.0.2":
                basic_options.append("version")
            if self.request_version == "3.0.0" and "version" not in self.kvp and self.requesttype == "POST":
                if "service" not in self.kvp:
                    self.kvp["service"] = "CSW"
                    basic_options.append("service")
                self.kvp["version"] = self.request_version
                basic_options.append("version")

            for k in basic_options:
                if k not in self.kvp:
                    if k in ["version", "acceptversions"] and request == "GetCapabilities":
                        pass
                    else:
                        error = 1
                        locator = k
                        code = "MissingParameterValue"
                        text = "Missing keyword: %s" % k
                        break

            # test each of the basic keyword values
            if error == 0:
                # test service
                if self.kvp["service"] != "CSW":
                    error = 1
                    locator = "service"
                    code = "InvalidParameterValue"
                    text = (
                        "Invalid value for service: %s.\
                    Value MUST be CSW"
                        % self.kvp["service"]
                    )

                # test version
                kvp_version = self.kvp.get("version", "")
                # noinspection PyBroadException
                try:
                    kvp_version_integer = pycsw_util.get_version_integer(kvp_version)
                except Exception as err:
                    kvp_version_integer = "invalid_value"
                if request != "GetCapabilities" and kvp_version_integer != own_version_integer:
                    error = 1
                    locator = "version"
                    code = "InvalidParameterValue"
                    text = "Invalid value for version: %s. Value MUST be " "2.0.2 or 3.0.0" % kvp_version

                # check for GetCapabilities acceptversions
                if "acceptversions" in self.kvp:
                    for vers in self.kvp["acceptversions"].split(","):
                        vers_integer = pycsw_util.get_version_integer(vers)
                        if vers_integer == own_version_integer:
                            break
                        else:
                            error = 1
                            locator = "acceptversions"
                            code = "VersionNegotiationFailed"
                            text = (
                                "Invalid parameter value in "
                                "acceptversions: %s. Value MUST be "
                                "2.0.2 or 3.0.0" % self.kvp["acceptversions"]
                            )

                # test request
                if self.kvp["request"] not in self.context.model["operations"]:
                    error = 1
                    locator = "request"
                    if request in ["Transaction", "Harvest"]:
                        code = "OperationNotSupported"
                        text = "%s operations are not supported" % request
                    else:
                        code = "InvalidParameterValue"
                        text = "Invalid value for request: %s" % request

        if error == 1:  # return an ExceptionReport
            # noinspection PyUnboundLocalVariable
            LOGGER.error("basic service options error: %s, %s, %s", code, locator, text)
            self.response = self.iface.exceptionreport(code, locator, text)

        else:  # process per the request value

            if "responsehandler" in self.kvp:
                # set flag to process asynchronously
                import threading

                self.asynchronous = True
                request_id = self.kvp.get("requestid", None)
                if request_id is None:
                    import uuid

                    self.kvp["requestid"] = str(uuid.uuid4())

            if self.kvp["request"] == "GetCapabilities":
                self.response = self.iface.getcapabilities()
            elif self.kvp["request"] == "DescribeRecord":
                self.response = self.iface.describerecord()
            elif self.kvp["request"] == "GetDomain":
                self.response = self.iface.getdomain()
            elif self.kvp["request"] == "GetRecords":
                if self.asynchronous:  # process asynchronously
                    # noinspection PyUnboundLocalVariable
                    threading.Thread(target=self.iface.getrecords).start()
                    # noinspection PyProtectedMember
                    self.response = self.iface._write_acknowledgement()
                else:
                    self.response = self.iface.getrecords()
            elif self.kvp["request"] == "GetRecordById":
                self.response = self.iface.getrecordbyid()
            elif self.kvp["request"] == "GetRepositoryItem":
                self.response = self.iface.getrepositoryitem()
            elif self.kvp["request"] == "Transaction":
                self.response = self.iface.transaction()
            elif self.kvp["request"] == "Harvest":
                if self.asynchronous:  # process asynchronously
                    # noinspection PyUnboundLocalVariable
                    threading.Thread(target=self.iface.harvest).start()
                    # noinspection PyProtectedMember
                    self.response = self.iface._write_acknowledgement()
                else:
                    self.response = self.iface.harvest()
            else:
                self.response = self.iface.exceptionreport(
                    "InvalidParameterValue", "request", "Invalid request parameter: %s" % self.kvp["request"]
                )

        LOGGER.info("Request processed")
        if self.mode == "sru":
            LOGGER.info("SRU mode detected; processing response.")
            self.response = self.sru().response_csw2sru(self.response, self.environ)
        elif self.mode == "opensearch":
            LOGGER.info("OpenSearch mode detected; processing response.")
            self.response = self.opensearch().response_csw2opensearch(self.response, self.config)

        elif self.mode == "oaipmh":
            LOGGER.info("OAI-PMH mode detected; processing response.")
            self.response = self.oaipmh().response(
                self.response, self.oaiargs, self.repository, self.config.get("server", "url")
            )

        return self._write_response()


class CSWAuth(Authentication):
    """
    Extended OWSLib authentication class to support token based auth

    This adds an additional credential type (token, in addition to username/passwords and certificates) to OWSLib's
    existing authentication support.

    Long term, this extended class should be upstreamed to OWSLib.
    """

    _TOKEN = None

    def __init__(
        self,
        token=None,
        username=None,
        password=None,
        cert=None,
        verify=True,
        shared=False,
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
            self.__class__.__name__,
            self.shared,
            self.token,
            self.username,
            self.password,
            self.cert,
            self.verify,
        )


class CSWClient(_CatalogueServiceWeb):
    """
    Modified OWSLib CSW client

    Note: Currently this class overrides large and lower-level methods within the CSW Client class. It is hoped this
    can be reduced to overriding higher level methods before being removed/upstreamed entirely.

    Changes in this modified class:
    * using mocked/patched versions of request calls, in order to include token authorisation headers

    Note: In order to support token auth, we currently piggyback on the existing username/password support. This would
    ideally be changed to support tokens as a 1st class citizen.

    Long term, this modified class should be upstreamed to OWSLib.
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

    # TODO: Revert to minimal class above and remove the two methods below.

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

        # print("Echo")

        if isinstance(self.request, str):  # GET KVP
            # print("Foxtrot")

            self.request = "%s%s" % (bind_url(request_url), self.request)
            self.response = openURL(self.request, None, "Get", timeout=self.timeout, auth=self.auth).read()

            # debug
            # print("invoke")
            # print(self.response[0:100])
        else:
            # print("Golf")
            # print(tostring(self.request))

            self.request = cleanup_namespaces(self.request)
            # Add any namespaces used in the "typeNames" attribute of the
            # csw:Query element to the query's xml namespaces.
            # noinspection PyUnresolvedReferences
            for query in self.request.findall(pycsw_util.nspath_eval("csw:Query", csw_namespaces)):
                ns = query.get("typeNames", None)
                if ns is not None:
                    # Pull out "gmd" from something like "gmd:MD_Metadata" from the list
                    # of typenames
                    ns_keys = [x.split(":")[0] for x in ns.split(" ")]
                    self.request = add_namespaces(self.request, ns_keys)
            self.request = add_namespaces(self.request, "ows")

            self.request = owslib_util.element_to_string(self.request, encoding="utf-8")

            # print("Hotel")

            self.response = http_post(request_url, self.request, self.lang, self.timeout, auth=self.auth)

            # debug
            # print("invoke 2")
            # print(self.response[0:100])
            # print(self.response)

        # debug
        # print("parse")
        # print(self.response[0:100])
        # print(self.response)

        # parse result see if it's XML
        self._exml = etree.parse(BytesIO(self.response))

        # it's XML.  Attempt to decipher whether the XML response is CSW-ish """
        valid_xpaths = [
            owslib_util.nspath_eval("ows:ExceptionReport", csw_namespaces),
            owslib_util.nspath_eval("csw:Capabilities", csw_namespaces),
            owslib_util.nspath_eval("csw:DescribeRecordResponse", csw_namespaces),
            owslib_util.nspath_eval("csw:GetDomainResponse", csw_namespaces),
            owslib_util.nspath_eval("csw:GetRecordsResponse", csw_namespaces),
            owslib_util.nspath_eval("csw:GetRecordByIdResponse", csw_namespaces),
            owslib_util.nspath_eval("csw:HarvestResponse", csw_namespaces),
            owslib_util.nspath_eval("csw:TransactionResponse", csw_namespaces),
        ]

        if self._exml.getroot().tag not in valid_xpaths:
            raise RuntimeError("Document is XML, but not CSW-ish")

        # check if it's an OGC Exception
        val = self._exml.find(owslib_util.nspath_eval("ows:Exception", csw_namespaces))
        if val is not None:
            raise ows.ExceptionReport(self._exml, self.owscommon.namespace)
        else:
            self.exceptionreport = None

    # noinspection PyDefaultArgument,PyShadowingBuiltins,PyAttributeOutsideInit
    def getrecordbyid(self, id=[], esn="full", outputschema=namespaces["csw"], format=outputformat):
        """

        Construct and process a GetRecordById request

        Parameters
        ----------

        - id: the list of Ids
        - esn: the ElementSetName 'full', 'brief' or 'summary' (default is 'full')
        - outputschema: the outputSchema (default is 'http://www.opengis.net/cat/csw/2.0.2')
        - format: the outputFormat (default is 'application/xml')

        """

        # construct request
        data = {
            "service": self.service,
            "version": self.version,
            "request": "GetRecordById",
            "outputFormat": format,
            "outputSchema": outputschema,
            "elementsetname": esn,
            "id": ",".join(id),
        }

        self.request = urlencode(data)

        self._invoke()

        if self.exceptionreport is None:
            self.results = {}
            self.records = OrderedDict()
            self._parserecords(outputschema, esn)

    # noinspection PyDefaultArgument,PyShadowingBuiltins
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
        if xml is not None:
            self.request = etree.fromstring(xml)
            val = self.request.find(owslib_util.nspath_eval("csw:Query/csw:ElementSetName", csw_namespaces))
            if val is not None:
                esn = owslib_util.testXMLValue(val)
            val = self.request.attrib.get("outputSchema")
            if val is not None:
                outputschema = owslib_util.testXMLValue(val, True)
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
                owslib_util.nspath_eval("xsi:schemaLocation", csw_namespaces),
                csw_schema_location,
            )

            node1 = etree.SubElement(node0, owslib_util.nspath_eval("csw:Query", csw_namespaces))
            node1.set("typeNames", typenames)

            etree.SubElement(node1, owslib_util.nspath_eval("csw:ElementSetName", csw_namespaces)).text = esn

            if any([len(constraints) > 0, cql is not None]):
                node2 = etree.SubElement(node1, owslib_util.nspath_eval("csw:Constraint", csw_namespaces))
                node2.set("version", "1.1.0")
                flt = fes.FilterRequest()
                if len(constraints) > 0:
                    node2.append(flt.setConstraintList(constraints))
                # Now add a CQL filter if passed in
                elif cql is not None:
                    etree.SubElement(node2, owslib_util.nspath_eval("csw:CqlText", csw_namespaces)).text = cql

            if sortby is not None and isinstance(sortby, fes.SortBy):
                node1.append(sortby.toXML())

            self.request = node0

        # print("Delta")
        self._invoke()

        if self.exceptionreport is None:
            # noinspection PyAttributeOutsideInit
            self.results = {}

            # process search results attributes
            val = self._exml.find(owslib_util.nspath_eval("csw:SearchResults", csw_namespaces)).attrib.get(
                "numberOfRecordsMatched"
            )
            self.results["matches"] = int(owslib_util.testXMLValue(val, True))
            val = self._exml.find(owslib_util.nspath_eval("csw:SearchResults", csw_namespaces)).attrib.get(
                "numberOfRecordsReturned"
            )
            self.results["returned"] = int(owslib_util.testXMLValue(val, True))
            val = self._exml.find(owslib_util.nspath_eval("csw:SearchResults", csw_namespaces)).attrib.get("nextRecord")
            if val is not None:
                # noinspection PyTypedDict
                self.results["nextrecord"] = int(owslib_util.testXMLValue(val, True))
            else:
                warnings.warn(
                    """CSW Server did not supply a nextRecord value (it is optional), so the client
                should page through the results in another way."""
                )
                # For more info, see:
                # https://github.com/geopython/OWSLib/issues/100
                self.results["nextrecord"] = None

            # process list of matching records
            # noinspection PyAttributeOutsideInit
            self.records = OrderedDict()

            self._parserecords(outputschema, esn)

    # noinspection PyDefaultArgument
    def transaction(
        self,
        ttype=None,
        typename="csw:Record",
        record=None,
        propertyname=None,
        propertyvalue=None,
        bbox=None,
        keywords=[],
        cql=None,
        identifier=None,
    ):
        """
        Construct and process a Transaction request

        Parameters
        ----------

        - ttype: the type of transaction 'insert, 'update', 'delete'
        - typename: the typename to describe (default is 'csw:Record')
        - record: the XML record to insert
        - propertyname: the RecordProperty/PropertyName to Filter against
        - propertyvalue: the RecordProperty Value to Filter against (for updates)
        - bbox: the bounding box of the spatial query in the form [minx,miny,maxx,maxy]
        - keywords: list of keywords
        - cql: common query language text.  Note this overrides bbox, qtype, keywords
        - identifier: record identifier.  Note this overrides bbox, qtype, keywords, cql

        This method has been modified as part of HazMat to fix the construction of transaction requests.
        - handling records as unicode strings

        """

        # append additional ISO namespaces to transaction
        namespaces["gss"] = "http://www.isotc211.org/2005/gss"
        namespaces["gsr"] = "http://www.isotc211.org/2005/gsr"

        # construct request
        node0 = self._setrootelement("csw:Transaction")
        node0.set("version", self.version)
        node0.set("service", self.service)
        node0.set(owslib_util.nspath_eval("xsi:schemaLocation", namespaces), schema_location)

        validtransactions = ["insert", "update", "delete"]

        if ttype not in validtransactions:  # invalid transaction
            raise RuntimeError("Invalid transaction '%s'." % ttype)

        node1 = etree.SubElement(node0, owslib_util.nspath_eval("csw:%s" % ttype.capitalize(), namespaces))

        if ttype != "update":
            node1.set("typeName", typename)

        if ttype == "insert":
            if record is None:
                raise RuntimeError("Nothing to insert.")
            if isinstance(record, str):
                record = record.encode()
            record = etree.fromstring(record)
            del record.attrib["{http://www.w3.org/2001/XMLSchema-instance}schemaLocation"]
            node1.append(record)

        if ttype == "update":
            if record is not None:
                node1.append(etree.fromstring(record))
            else:
                if propertyname is not None and propertyvalue is not None:
                    node2 = etree.SubElement(node1, owslib_util.nspath_eval("csw:RecordProperty", namespaces))
                    etree.SubElement(node2, owslib_util.nspath_eval("csw:Name", namespaces)).text = propertyname
                    etree.SubElement(node2, owslib_util.nspath_eval("csw:Value", namespaces)).text = propertyvalue
                    self._setconstraint(node1, None, propertyname, keywords, bbox, cql, identifier)

        if ttype == "delete":
            self._setconstraint(node1, None, propertyname, keywords, bbox, cql, identifier)

        node0 = etree.fromstring(bytes(etree.tostring(node0).decode(), encoding="UTF-8"))

        self.request = node0

        self._invoke()
        # noinspection PyAttributeOutsideInit
        self.results = {}

        if self.exceptionreport is None:
            self._parsetransactionsummary()
            self._parseinsertresult()

    def _parserecords(self, outputschema, esn):
        if outputschema == namespaces["gmd"]:  # iso 19139
            for i in self._exml.findall(
                ".//" + owslib_util.nspath_eval("gmd:MD_Metadata", namespaces)
            ) or self._exml.findall(".//" + owslib_util.nspath_eval("gmi:MI_Metadata", namespaces)):
                val = i.find(owslib_util.nspath_eval("gmd:fileIdentifier/gco:CharacterString", namespaces))
                identifier = self._setidentifierkey(owslib_util.testXMLValue(val))

                # fix trailing tags
                i_str = etree.tostring(i).decode()
                i_str = i_str.replace("</csw:SearchResults>", "")
                i_str = i_str.replace("</csw:GetRecordsResponse>", "")
                i_str = i_str.replace("</csw:GetRecordByIdResponse>", "")
                i = etree.fromstring(i_str)

                self.records[identifier] = MD_Metadata(i)
            for i in self._exml.findall(".//" + owslib_util.nspath_eval("gfc:FC_FeatureCatalogue", namespaces)):
                identifier = self._setidentifierkey(owslib_util.testXMLValue(i.attrib["uuid"], attrib=True))
                self.records[identifier] = FC_FeatureCatalogue(i)
        else:
            super()._parserecords(outputschema=outputschema, esn=esn)


class Csw2(_Csw2):
    # noinspection PySingleQuotedDocstring
    """ CSW 2.x server """

    def __init__(self, server_csw):
        # noinspection PySingleQuotedDocstring
        """ Initialize CSW2 """

        self.parent = server_csw
        self.version = "2.0.2"

    def transaction(self):
        # noinspection PySingleQuotedDocstring
        """ Handle Transaction request """

        try:
            # noinspection PyProtectedMember
            self.parent._test_manager()
        except Exception as err:
            return self.exceptionreport("NoApplicableCode", "transaction", str(err))

        inserted = 0
        updated = 0
        deleted = 0

        insertresults = []

        LOGGER.debug("Transaction list: %s", self.parent.kvp["transactions"])

        for ttype in self.parent.kvp["transactions"]:
            if ttype["type"] == "insert":
                try:
                    record = metadata.parse_record(self.parent.context, ttype["xml"], self.parent.repository)[0]
                except Exception as err:
                    LOGGER.exception("Transaction (insert) failed")
                    return self.exceptionreport(
                        "NoApplicableCode",
                        "insert",
                        "Transaction (insert) failed: record parsing failed: %s" % str(err),
                    )

                LOGGER.debug("Transaction operation: %s", record)

                if not hasattr(record, self.parent.context.md_core_model["mappings"]["pycsw:Identifier"]):
                    return self.exceptionreport("NoApplicableCode", "insert", "Record requires an identifier")

                # insert new record
                try:
                    self.parent.repository.insert(record, "local", pycsw_util.get_today_and_now())

                    inserted += 1
                    insertresults.append(
                        {
                            "identifier": getattr(
                                record, self.parent.context.md_core_model["mappings"]["pycsw:Identifier"]
                            ),
                            "title": getattr(record, self.parent.context.md_core_model["mappings"]["pycsw:Title"]),
                        }
                    )
                except Exception as err:
                    return self.exceptionreport(
                        "NoApplicableCode", "insert", "Transaction (insert) failed: %s." % str(err)
                    )

            elif ttype["type"] == "update":
                if "constraint" not in ttype:
                    # update full existing resource in repository
                    try:
                        record = metadata.parse_record(self.parent.context, ttype["xml"], self.parent.repository)[0]
                        identifier = getattr(record, self.parent.context.md_core_model["mappings"]["pycsw:Identifier"])
                    except Exception as err:
                        return self.exceptionreport(
                            "NoApplicableCode",
                            "insert",
                            "Transaction (update) failed: record parsing failed: %s" % str(err),
                        )

                    # query repository to see if record already exists
                    LOGGER.info("checking if record exists (%s)", identifier)

                    results = self.parent.repository.query_ids(ids=[identifier])

                    if len(results) == 0:
                        LOGGER.debug("id %s does not exist in repository", identifier)
                    else:  # existing record, it's an update
                        try:
                            self.parent.repository.update(record)
                            updated += 1
                        except Exception as err:
                            return self.exceptionreport(
                                "NoApplicableCode", "update", "Transaction (update) failed: %s." % str(err)
                            )
                else:  # update by record property and constraint
                    # get / set XPath for property names
                    for rp in ttype["recordproperty"]:
                        if rp["name"] not in self.parent.repository.queryables["_all"]:
                            # is it an XPath?
                            if rp["name"].find("/") != -1:
                                # scan outputschemas; if match, bind
                                for osch in self.parent.outputschemas.values():
                                    for key, value in osch.XPATH_MAPPINGS.items():
                                        if value == rp["name"]:  # match
                                            rp["rp"] = {"xpath": value, "name": key}
                                            rp["rp"]["dbcol"] = self.parent.repository.queryables["_all"][key]
                                            break
                            else:
                                return self.exceptionreport(
                                    "NoApplicableCode",
                                    "update",
                                    "Transaction (update) failed: invalid property2: %s." % str(rp["name"]),
                                )
                        else:
                            rp["rp"] = self.parent.repository.queryables["_all"][rp["name"]]

                    LOGGER.debug("Record Properties: %s.", ttype["recordproperty"])
                    try:
                        updated += self.parent.repository.update(
                            record=None, recprops=ttype["recordproperty"], constraint=ttype["constraint"]
                        )
                    except Exception as err:
                        LOGGER.exception("Transaction (updated) failed")
                        return self.exceptionreport(
                            "NoApplicableCode", "update", "Transaction (update) failed: %s." % str(err)
                        )

            elif ttype["type"] == "delete":
                deleted += self.parent.repository.delete(ttype["constraint"])

        node = etree.Element(
            pycsw_util.nspath_eval("csw:TransactionResponse", self.parent.context.namespaces),
            nsmap=self.parent.context.namespaces,
            version="2.0.2",
        )

        node.attrib[
            pycsw_util.nspath_eval("xsi:schemaLocation", self.parent.context.namespaces)
        ] = "%s %s/csw/2.0.2/CSW-publication.xsd" % (
            self.parent.context.namespaces["csw"],
            self.parent.config.get("server", "ogc_schemas_base"),
        )

        node.append(self._write_transactionsummary(inserted=inserted, updated=updated, deleted=deleted))

        if len(insertresults) > 0 and self.parent.kvp["verboseresponse"]:
            # show insert result identifiers
            node.append(self._write_verboseresponse(insertresults))

        return node

    def parse_postdata(self, postdata):
        # noinspection PySingleQuotedDocstring
        """ Parse POST XML """

        request = {}
        try:
            LOGGER.info("Parsing %s", postdata)
            doc = etree.fromstring(postdata, self.parent.context.parser)
        except Exception as err:
            errortext = "Exception: document not well-formed.\nError: %s." % str(err)
            LOGGER.exception(errortext)
            return errortext

        # if this is a SOAP request, get to SOAP-ENV:Body/csw:*
        if doc.tag == pycsw_util.nspath_eval("soapenv:Envelope", self.parent.context.namespaces):
            LOGGER.debug("SOAP request specified")
            self.parent.soap = True

            # noinspection PyUnresolvedReferences
            doc = doc.find(pycsw_util.nspath_eval("soapenv:Body", self.parent.context.namespaces)).xpath("child::*")[0]

        if doc.tag in [
            pycsw_util.nspath_eval("csw:Transaction", self.parent.context.namespaces),
            pycsw_util.nspath_eval("csw:Harvest", self.parent.context.namespaces),
        ]:
            schema = os.path.join(
                self.parent.config.get("server", "home"),
                "core",
                "schemas",
                "ogc",
                "csw",
                "2.0.2",
                "CSW-publication.xsd",
            )
        else:
            schema = os.path.join(
                self.parent.config.get("server", "home"), "core", "schemas", "ogc", "csw", "2.0.2", "CSW-discovery.xsd"
            )

        try:
            # it is virtually impossible to validate a csw:Transaction
            # csw:Insert|csw:Update (with single child) XML document.
            # Only validate non csw:Transaction XML

            if (
                doc.find(".//%s" % pycsw_util.nspath_eval("csw:Insert", self.parent.context.namespaces)) is None
                and len(doc.xpath("//csw:Update/child::*", namespaces=self.parent.context.namespaces)) == 0
            ):

                LOGGER.info("Validating %s", postdata)
                schema = etree.XMLSchema(file=schema)
                parser = etree.XMLParser(schema=schema, resolve_entities=False)
                if hasattr(self.parent, "soap") and self.parent.soap:
                    # validate the body of the SOAP request
                    doc = etree.fromstring(etree.tostring(doc), parser)
                else:  # validate the request normally
                    doc = etree.fromstring(postdata, parser)
                LOGGER.debug("Request is valid XML.")
            else:  # parse Transaction without validation
                doc = etree.fromstring(postdata, self.parent.context.parser)
        except Exception as err:
            errortext = "Exception: the document is not valid.\nError: %s" % str(err)
            LOGGER.exception(errortext)
            return errortext

        request["request"] = etree.QName(doc).localname
        LOGGER.debug("Request operation %s specified.", request["request"])
        tmp = doc.find(".").attrib.get("service")
        if tmp is not None:
            request["service"] = tmp

        tmp = doc.find(".").attrib.get("version")
        if tmp is not None:
            request["version"] = tmp

        tmp = doc.find(".//%s" % pycsw_util.nspath_eval("ows:Version", self.parent.context.namespaces))

        if tmp is not None:
            request["version"] = tmp.text

        tmp = doc.find(".").attrib.get("updateSequence")
        if tmp is not None:
            request["updatesequence"] = tmp

        # GetCapabilities
        if request["request"] == "GetCapabilities":
            tmp = doc.find(pycsw_util.nspath_eval("ows:Sections", self.parent.context.namespaces))
            if tmp is not None:
                request["sections"] = ",".join(
                    [
                        section.text
                        for section in doc.findall(
                            pycsw_util.nspath_eval("ows:Sections/ows:Section", self.parent.context.namespaces)
                        )
                    ]
                )

        # DescribeRecord
        if request["request"] == "DescribeRecord":
            request["typename"] = [
                typename.text
                for typename in doc.findall(pycsw_util.nspath_eval("csw:TypeName", self.parent.context.namespaces))
            ]

            tmp = doc.find(".").attrib.get("schemaLanguage")
            if tmp is not None:
                request["schemalanguage"] = tmp

            tmp = doc.find(".").attrib.get("outputFormat")
            if tmp is not None:
                request["outputformat"] = tmp

        # GetDomain
        if request["request"] == "GetDomain":
            tmp = doc.find(pycsw_util.nspath_eval("csw:ParameterName", self.parent.context.namespaces))
            if tmp is not None:
                request["parametername"] = tmp.text

            tmp = doc.find(pycsw_util.nspath_eval("csw:PropertyName", self.parent.context.namespaces))
            if tmp is not None:
                request["propertyname"] = tmp.text

        # GetRecords
        if request["request"] == "GetRecords":
            tmp = doc.find(".").attrib.get("outputSchema")
            request["outputschema"] = tmp if tmp is not None else self.parent.context.namespaces["csw"]

            tmp = doc.find(".").attrib.get("resultType")
            request["resulttype"] = tmp if tmp is not None else None

            tmp = doc.find(".").attrib.get("outputFormat")
            request["outputformat"] = tmp if tmp is not None else "application/xml"

            tmp = doc.find(".").attrib.get("startPosition")
            request["startposition"] = tmp if tmp is not None else 1

            tmp = doc.find(".").attrib.get("requestId")
            request["requestid"] = tmp if tmp is not None else None

            tmp = doc.find(".").attrib.get("maxRecords")
            if tmp is not None:
                request["maxrecords"] = tmp

            tmp = doc.find(pycsw_util.nspath_eval("csw:DistributedSearch", self.parent.context.namespaces))
            if tmp is not None:
                request["distributedsearch"] = True
                hopcount = tmp.attrib.get("hopCount")
                request["hopcount"] = int(hopcount) - 1 if hopcount is not None else 1
            else:
                request["distributedsearch"] = False

            tmp = doc.find(pycsw_util.nspath_eval("csw:ResponseHandler", self.parent.context.namespaces))
            if tmp is not None:
                request["responsehandler"] = tmp.text

            tmp = doc.find(pycsw_util.nspath_eval("csw:Query/csw:ElementSetName", self.parent.context.namespaces))
            request["elementsetname"] = tmp.text if tmp is not None else None

            tmp = doc.find(pycsw_util.nspath_eval("csw:Query", self.parent.context.namespaces)).attrib.get("typeNames")
            request["typenames"] = tmp.split() if tmp is not None else "csw:Record"

            request["elementname"] = [
                elname.text
                for elname in doc.findall(
                    pycsw_util.nspath_eval("csw:Query/csw:ElementName", self.parent.context.namespaces)
                )
            ]

            # noinspection PyTypedDict
            request["constraint"] = {}
            tmp = doc.find(pycsw_util.nspath_eval("csw:Query/csw:Constraint", self.parent.context.namespaces))

            if tmp is not None:
                request["constraint"] = self._parse_constraint(tmp)
                if isinstance(request["constraint"], str):  # parse error
                    return "Invalid Constraint: %s" % request["constraint"]
            else:
                LOGGER.debug(
                    "No csw:Constraint (ogc:Filter or csw:CqlText) \
                specified"
                )

            tmp = doc.find(pycsw_util.nspath_eval("csw:Query/ogc:SortBy", self.parent.context.namespaces))
            if tmp is not None:
                LOGGER.debug("Sorted query specified")
                # noinspection PyTypedDict
                request["sortby"] = {}

                try:
                    elname = tmp.find(
                        pycsw_util.nspath_eval("ogc:SortProperty/ogc:PropertyName", self.parent.context.namespaces)
                    ).text

                    # noinspection PyUnresolvedReferences
                    request["sortby"]["propertyname"] = self.parent.repository.queryables["_all"][elname]["dbcol"]

                    if elname.find("BoundingBox") != -1 or elname.find("Envelope") != -1:
                        # it's a spatial sort
                        # noinspection PyUnresolvedReferences
                        request["sortby"]["spatial"] = True
                except Exception as err:
                    errortext = "Invalid ogc:SortProperty/ogc:PropertyName: %s" % str(err)
                    LOGGER.exception(errortext)
                    return errortext

                tmp2 = tmp.find(
                    pycsw_util.nspath_eval("ogc:SortProperty/ogc:SortOrder", self.parent.context.namespaces)
                )
                # noinspection PyUnresolvedReferences
                request["sortby"]["order"] = tmp2.text if tmp2 is not None else "ASC"
            else:
                request["sortby"] = None

        # GetRecordById
        if request["request"] == "GetRecordById":
            request["id"] = [
                id1.text for id1 in doc.findall(pycsw_util.nspath_eval("csw:Id", self.parent.context.namespaces))
            ]

            tmp = doc.find(pycsw_util.nspath_eval("csw:ElementSetName", self.parent.context.namespaces))
            request["elementsetname"] = tmp.text if tmp is not None else "summary"

            tmp = doc.find(".").attrib.get("outputSchema")
            request["outputschema"] = tmp if tmp is not None else self.parent.context.namespaces["csw"]

            tmp = doc.find(".").attrib.get("outputFormat")
            if tmp is not None:
                request["outputformat"] = tmp

        # Transaction
        if request["request"] == "Transaction":
            request["verboseresponse"] = True
            tmp = doc.find(".").attrib.get("verboseResponse")
            if tmp is not None:
                if tmp in ["false", "0"]:
                    request["verboseresponse"] = False

            tmp = doc.find(".").attrib.get("requestId")
            request["requestid"] = tmp if tmp is not None else None

            request["transactions"] = []

            for ttype in doc.xpath("//csw:Insert", namespaces=self.parent.context.namespaces):
                tname = ttype.attrib.get("typeName")

                for mdrec in ttype.xpath("child::*"):
                    # fix trailing tags
                    mdrec = (
                        etree.tostring(mdrec)
                        .decode()
                        .replace("</gmi:MI_Metadata></csw:Insert></csw:Transaction>", "</gmi:MI_Metadata>")
                    )
                    mdrec = etree.fromstring(mdrec)

                    xml = mdrec
                    request["transactions"].append({"type": "insert", "typename": tname, "xml": xml})

            for ttype in doc.xpath("//csw:Update", namespaces=self.parent.context.namespaces):
                child = ttype.xpath("child::*")
                update = {"type": "update"}

                if len(child) == 1:  # it's a wholesale update
                    update["xml"] = child[0]
                else:  # it's a RecordProperty with Constraint Update
                    update["recordproperty"] = []

                    for recprop in ttype.findall(
                        pycsw_util.nspath_eval("csw:RecordProperty", self.parent.context.namespaces)
                    ):
                        rpname = recprop.find(pycsw_util.nspath_eval("csw:Name", self.parent.context.namespaces)).text
                        rpvalue = recprop.find(pycsw_util.nspath_eval("csw:Value", self.parent.context.namespaces)).text

                        update["recordproperty"].append({"name": rpname, "value": rpvalue})

                    update["constraint"] = self._parse_constraint(
                        ttype.find(pycsw_util.nspath_eval("csw:Constraint", self.parent.context.namespaces))
                    )

                request["transactions"].append(update)

            for ttype in doc.xpath("//csw:Delete", namespaces=self.parent.context.namespaces):
                tname = ttype.attrib.get("typeName")
                constraint = self._parse_constraint(
                    ttype.find(pycsw_util.nspath_eval("csw:Constraint", self.parent.context.namespaces))
                )

                if isinstance(constraint, str):  # parse error
                    return "Invalid Constraint: %s" % constraint

                request["transactions"].append({"type": "delete", "typename": tname, "constraint": constraint})

        # Harvest
        if request["request"] == "Harvest":
            request["source"] = doc.find(pycsw_util.nspath_eval("csw:Source", self.parent.context.namespaces)).text

            request["resourcetype"] = doc.find(
                pycsw_util.nspath_eval("csw:ResourceType", self.parent.context.namespaces)
            ).text

            tmp = doc.find(pycsw_util.nspath_eval("csw:ResourceFormat", self.parent.context.namespaces))
            if tmp is not None:
                request["resourceformat"] = tmp.text
            else:
                request["resourceformat"] = "application/xml"

            tmp = doc.find(pycsw_util.nspath_eval("csw:HarvestInterval", self.parent.context.namespaces))
            if tmp is not None:
                request["harvestinterval"] = tmp.text

            tmp = doc.find(pycsw_util.nspath_eval("csw:ResponseHandler", self.parent.context.namespaces))
            if tmp is not None:
                request["responsehandler"] = tmp.text
        return request


def convert_csw_brief_gmd_to_gmi_xml(record_xml: str) -> str:
    """
    Method to convert CSW GetRecord(s) requests using the 'brief' element set name from ISO-19115(-0) to ISO 19115-2

    Where GetRecord or GetRecords requests use element set names other than 'full', PyCSW needs to derive summarised
    representations of records. As the PyCSW profile for ISO 19115 was written for the original ISO 19115:2003 standard,
    derived representations use this version. This is an issue if newer editions of 19115 are used, notably 19115-2 and
    19115-3 (19115-1).

    As the BAS Metadata Library is sensitive to each edition (as the namespace and elements differ between editions),
    this means that a 'brief' version of an ISO 19115-2 record can't be parsed as it will use the ISO 19115 namespace
    (GMD rather than GMI).

    To prevent needing to use different edition implementations depending on the element set used, this method will
    'covert' a record using the GMD namespace to the GMI namespace. This is a crude conversion, as it simply creates a
    new root level element (using the GMI namespace) and copies all direct children of the original GMD root element.

    The effect is to replace the root element with the expected namespace to allow records to be parsed as expected.
    This is possible because ISO 19115-2 is a superset and extension of the original ISO 19115 standard. It would not
    be possible to do this in the same way with ISO 19115-3, as it uses a different conceptual model.

    # TODO: Keep this method for use in CSW abstraction class or merge into an overridden version of `getrecords2()`?

    Long term it is unclear how this should be resolved.
    """
    iso_ns = Namespaces()

    gmd_xml_element = ElementTree(fromstring(record_xml))
    gmd_sub_elements = gmd_xml_element.getroot().xpath(f"/gmd:MD_Metadata/*", namespaces=iso_ns.nsmap())
    gmi_xml_element = Element(
        f"{{{iso_ns.gmi}}}MI_Metadata",
        attrib={f"{{{iso_ns.xsi}}}schemaLocation": iso_ns.schema_locations()},
        nsmap=iso_ns.nsmap(),
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
