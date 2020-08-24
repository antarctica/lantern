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

import sys
import warnings
import logging

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
)
from bas_metadata_library.standards.iso_19115_common import Namespaces

warnings.simplefilter(action="ignore", category=FutureWarning)
from pycsw.server import Csw as _Csw

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


# class Csw(_Csw):
class CSWServer(_Csw):
    """
    PyCSW instance using the modified `setup_logging` method

    Long term the logging destination should be a configuration option in PyCSW.
    """

    def __init__(self, rtconfig=None, env=None, version="3.0.0"):
        with mock.patch("pycsw.core.log.setup_logger", side_effect=setup_logger()):
            super().__init__(rtconfig, env, version)


class CSWAuth(Authentication):
    """
    Extended OWSLib authentication class to support token based auth

    This adds an additional credential type (token, in addition to username/passwords and certificates) to OWSLib's
    existing authentication support.

    Long term, this extended class should be upstreamed to OWSLib.
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

            # print("Hotel")

            self.response = http_post(request_url, self.request, self.lang, self.timeout, auth=self.auth)

            # debug
            # print("invoke 2")
            # print(self.response[0:100])

        # debug
        # print("parse")
        # print(self.response[0:100])
        # print(self.response)

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

    # noinspection PyDefaultArgument
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

        # print("Delta")
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

    # TODO: Keep this method for use in CSW abstraction class or merge into an overriden version of `getrecords2()`?

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

    record_xml = tostring(ElementTree(gmi_xml_element), pretty_print=True, xml_declaration=False, encoding="utf-8",)
    return record_xml.decode()
