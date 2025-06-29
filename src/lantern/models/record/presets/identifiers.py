from lantern.models.record.elements.common import Identifier


def make_bas_cat(item_id: str) -> Identifier:
    """Item within BAS Data Catalogue."""
    if item_id is None:
        msg = "Item identifier is required"
        raise ValueError(msg) from None

    return Identifier(identifier=item_id, href=f"https://data.bas.ac.uk/items/{item_id}", namespace="data.bas.ac.uk")
