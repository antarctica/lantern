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

from scar_add_metadata_toolbox.hazmat.owslib.waterml.wml import SitesResponse, TimeSeriesResponse, VariablesResponse, namespaces
from scar_add_metadata_toolbox.hazmat.owslib.etree import etree, ElementType


def ns(namespace):
    return namespaces.get(namespace)


class WaterML_1_0(object):
    def __init__(self, element):

        if isinstance(element, ElementType):
            self._root = element
        else:
            self._root = etree.fromstring(element)

        if hasattr(self._root, 'getroot'):
            self._root = self._root.getroot()

        self._ns = 'wml1.0'

    @property
    def response(self):
        try:
            if self._root.tag == str(ns(self._ns) + 'variablesResponse'):
                return VariablesResponse(self._root, self._ns)
            elif self._root.tag == str(ns(self._ns) + 'timeSeriesResponse'):
                return TimeSeriesResponse(self._root, self._ns)
            elif self._root.tag == str(ns(self._ns) + 'sitesResponse'):
                return SitesResponse(self._root, self._ns)
        except Exception:
            raise

        raise ValueError('Unable to determine response type from xml')
