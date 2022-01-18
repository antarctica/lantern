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
