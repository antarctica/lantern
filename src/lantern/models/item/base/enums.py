from enum import Enum


class AccessLevel(Enum):
    """
    Item access levels.

    Where:
    - 'NONE' is a fallback value that should not be needed (as items with no access would not be catalogued)
    - 'UNKNOWN' represents undefined access that will be resolved when accessing the item (legacy measure)
    - 'BAS_STAFF' represents general access by staff employed by UKRI at BAS
    - 'PUBLIC' represents unrestricted public access
    """

    NONE = "none"
    UNKNOWN = "unknown"
    BAS_STAFF = "bas_staff"
    PUBLIC = "public"


class ResourceTypeLabel(Enum):
    """Partial mapping of the Hierarchy Level code list to friendlier terms."""

    COLLECTION = "COLLECTION"
    DATASET = "DATASET"
    INITIATIVE = "INITIATIVE (PROJECT)"
    PRODUCT = "PRODUCT"
    MAP_PRODUCT = "PRODUCT (MAP)"
    PAPER_MAP_PRODUCT = "PRODUCT (PAPER MAP)"
    WEB_MAP_PRODUCT = "PRODUCT (WEB MAP)"


class Licence(Enum):
    """Supported resource licences."""

    OGL_UK_3_0 = "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/"
    CC_BY_4_0 = "https://creativecommons.org/licenses/by/4.0/"
    COPERNICUS_SENTINEL_DATA_1 = "https://cds.climate.copernicus.eu/licences/ec-sentinel"
    X_ALL_RIGHTS_RESERVED_1 = "https://metadata-resources.data.bas.ac.uk/licences/all-rights-reserved-v1/"
    X_OPERATIONS_MAPPING_1 = "https://metadata-resources.data.bas.ac.uk/licences/operations-mapping-v1/"
    X_MAGIC_PRODUCTS_1 = "https://metadata-resources.data.bas.ac.uk/licences/magic-products-v1/"
