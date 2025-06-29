from assets_tracking_service.lib.bas_data_catalogue.models.record.elements.identification import Aggregation
from assets_tracking_service.lib.bas_data_catalogue.models.record.enums import (
    AggregationAssociationCode,
    AggregationInitiativeCode,
)
from assets_tracking_service.lib.bas_data_catalogue.models.record.presets.identifiers import (
    make_bas_cat as make_bas_cat_id,
)


def make_bas_cat(
    item_id: str, association: AggregationAssociationCode, initiative: AggregationInitiativeCode | None = None
) -> Aggregation:
    """An item within BAS Data Catalogue."""  # noqa: D401
    return Aggregation(
        identifier=make_bas_cat_id(item_id),
        association_type=association,
        initiative_type=initiative,
    )


def make_in_bas_cat_collection(collection_id: str) -> Aggregation:
    """
    Resource within a collection.

    Inverse of `make_bas_cat_collection_member`.
    """
    return make_bas_cat(
        collection_id, AggregationAssociationCode.LARGER_WORK_CITATION, AggregationInitiativeCode.COLLECTION
    )


def make_bas_cat_collection_member(item_id: str) -> Aggregation:
    """
    Member of collection.

    Inverse of `make_in_bas_cat_collection()`.
    """
    return make_bas_cat(item_id, AggregationAssociationCode.IS_COMPOSED_OF, AggregationInitiativeCode.COLLECTION)
