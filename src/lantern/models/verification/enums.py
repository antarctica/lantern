from enum import Enum


class VerificationResult(Enum):
    """
    Verification Job Result.

    'PENDING' represents jobs that haven't been attempted and their outcome is unknown.

    Enum values (except 'PENDING') are used in the `result_label` Jinja macro to return a relevant coloured label.
    """

    PASS = "passed"  # noqa: S105
    FAIL = "failed"
    SKIP = "skipped"
    PENDING = "-"


class VerificationType(Enum):
    """
    Verification Job Type.

    I.e. the category/class of job. Enum values are displayed to end-users.
    """

    SITE_PAGES = "Site Pages"
    RECORD_PAGES_JSON = "Record Pages (JSON)"
    RECORD_PAGES_XML = "Record Pages (XML)"
    RECORD_PAGES_HTML = "Record Pages (XML HTML)"
    ITEM_PAGES = "Item Pages"
    ALIAS_REDIRECTS = "Aliases Redirects"
    DOI_REDIRECTS = "DOI Redirects"
    ITEM_DOWNLOADS = "Item Downloads"
    DOWNLOADS_OPEN = "Normal Downloads"
    DOWNLOADS_NORA = "NORA Downloads"
    DOWNLOADS_SHAREPOINT = "SharePoint Downloads"
    DOWNLOADS_ARCGIS_LAYERS = "ArcGIS Layers"
    DOWNLOADS_ARCGIS_SERVICES = "ArcGIS Services"
    SAN_REFERENCE = "BAS SAN Reference"


class VerificationDistributionType(Enum):
    """
    Verification Distribution Type.

    Effectively represents the data access system used for distributions, and whether these are directly downloads,
    services, etc. Used internally to guide how to verify each distribution. For example, files hosted in SharePoint
    require authentication to access.

    'UNKNOWN' is a fallback value where a distribution is not understood.
    """

    ARCGIS_LAYER = "arcgis_layer"
    ARCGIS_SERVICE = "arcgis_service"
    FILE = "file"
    NORA = "nora"
    PUBLISHED_MAP = "published_map"
    SHAREPOINT = "sharepoint"
    SAN = "san"
