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
# Copyright (c) 2015 Luís de Sousa
#
# Authors :
#          Luís de Sousa <luis.a.de.sousa@gmail.com>
#
# Contact email: luis.a.de.sousa@gmail.com
# =============================================================================

from scar_add_metadata_toolbox.hazmat.owslib.coverage import wcs110


class Namespaces_1_1_1():

    def WCS(self, tag):
        return '{http://www.opengis.net/wcs/1.1.1}' + tag

    def WCS_OWS(self, tag):
        return '{http://www.opengis.net/wcs/1.1.1/ows}' + tag

    def OWS(self, tag):
        return '{http://www.opengis.net/ows/1.1}' + tag


class WebCoverageService_1_1_1(wcs110.WebCoverageService_1_1_0):
    """Abstraction for OGC Web Coverage Service (WCS), version 1.1.1
    Implements IWebCoverageService.
    """
    version = '1.1.1'
    ns = Namespaces_1_1_1()
