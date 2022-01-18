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
# OWSLib. Copyright (C) 2005 Sean C. Gillies
#
# Contact email: sgillies@frii.com
# =============================================================================

from scar_add_metadata_toolbox.hazmat.owslib.namespaces import Namespaces


def patch_well_known_namespaces(etree_module):
    """Monkey patches the etree module to add some well-known namespaces."""

    ns = Namespaces()

    try:
        register_namespace = etree_module.register_namespace
    except AttributeError:
        etree_module._namespace_map

        def register_namespace(prefix, uri):
            etree_module._namespace_map[uri] = prefix

    for k, v in list(ns.get_namespaces().items()):
        register_namespace(k, v)


# try to find lxml or elementtree
try:
    from lxml import etree
    from lxml.etree import ParseError
    ElementType = etree._Element
except ImportError:
    import xml.etree.ElementTree as etree
    ElementType = etree.Element
    try:
        from xml.etree.ElementTree import ParseError
    except ImportError:
        from xml.parsers.expat import ExpatError as ParseError

patch_well_known_namespaces(etree)
