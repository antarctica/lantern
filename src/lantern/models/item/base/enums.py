from enum import Enum


class AccessType(Enum):
    """
    Item access types.

    Where 'NONE' is a fallback value that should not be needed (as items with no access would not be catalogued).
    Where 'BAS_SOME' represents undefined access that will be resolved when accessing the item.
    """

    NONE = "none"
    PUBLIC = "public"
    BAS_ALL = "bas_all"
    BAS_SOME = "bas_some"
