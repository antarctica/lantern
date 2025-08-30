from lantern.lib.metadata_library.models.record.elements.common import Identifier
from lantern.models.record.const import CATALOGUE_NAMESPACE


def make_bas_cat(item_id: str) -> Identifier:
    """Item within BAS Data Catalogue."""
    if item_id is None:
        msg = "Item identifier is required"
        raise ValueError(msg) from None

    return Identifier(
        identifier=item_id, href=f"https://{CATALOGUE_NAMESPACE}/items/{item_id}", namespace=CATALOGUE_NAMESPACE
    )
