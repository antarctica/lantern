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
    PRODUCT = "PRODUCT (MAP)"
    PAPER_MAP_PRODUCT = "PRODUCT (PAPER MAP)"
