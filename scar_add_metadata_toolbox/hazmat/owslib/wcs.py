# -*- coding: ISO-8859-15 -*-
# =================================================================
#
# Changes, which are local to this dependency, within this package,
# have been made to this file, in order to improve compatibility,
# add functionality, or address bugs that are not present, or not
# addressed in the upstream package.
#
# See the README for the SCAR ADD Metadata Toolbox (this package)
# for more information about why these changes have been made.
#
# Summary of changes made to this file:
# - rewriting imports to allow this package to be used as a
#   vendored dependency
# =================================================================

# =============================================================================
# Copyright (c) 2004, 2006 Sean C. Gillies
# Copyright (c) 2007 STFC <http://www.stfc.ac.uk>
#
# Authors :
#          Dominic Lowe <d.lowe@rl.ac.uk>
#
# Contact email: d.lowe@rl.ac.uk
# =============================================================================

"""
Web Coverage Server (WCS) methods and metadata. Factory function.
"""

from . import etree
from .coverage import wcs100, wcs110, wcs111, wcsBase, wcs200, wcs201
from scar_add_metadata_toolbox.hazmat.owslib.util import clean_ows_url, Authentication, openURL


def WebCoverageService(url, version=None, xml=None, cookies=None, timeout=30, auth=None):
    ''' wcs factory function, returns a version specific WebCoverageService object '''

    if not auth:
        auth = Authentication()

    if version is None:
        if xml is None:
            reader = wcsBase.WCSCapabilitiesReader(auth=auth)
            request = reader.capabilities_url(url)
            xml = openURL(
                request, cookies=cookies, timeout=timeout, auth=auth).read()

        capabilities = etree.etree.fromstring(xml)
        version = capabilities.get('version')
        del capabilities

    clean_url = clean_ows_url(url)

    if version == '1.0.0':
        return wcs100.WebCoverageService_1_0_0.__new__(
            wcs100.WebCoverageService_1_0_0, clean_url, xml, cookies, auth=auth)
    elif version == '1.1.0':
        return wcs110.WebCoverageService_1_1_0.__new__(
            wcs110.WebCoverageService_1_1_0, url, xml, cookies, auth=auth)
    elif version == '1.1.1':
        return wcs111.WebCoverageService_1_1_1.__new__(
            wcs111.WebCoverageService_1_1_1, url, xml, cookies, auth=auth)
    elif version == '2.0.0':
        return wcs200.WebCoverageService_2_0_0.__new__(
            wcs200.WebCoverageService_2_0_0, url, xml, cookies, auth=auth)
    elif version == '2.0.1':
        return wcs201.WebCoverageService_2_0_1.__new__(
            wcs201.WebCoverageService_2_0_1, url, xml, cookies, auth=auth)
