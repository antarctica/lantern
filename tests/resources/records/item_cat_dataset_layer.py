from lantern.lib.metadata_library.models.record.elements.common import Identifier
from lantern.lib.metadata_library.models.record.elements.identification import Aggregation
from lantern.lib.metadata_library.models.record.enums import (
    AggregationAssociationCode,
    AggregationInitiativeCode,
    HierarchyLevelCode,
)
from lantern.models.record.const import CATALOGUE_NAMESPACE
from tests.resources.records.utils import make_record

# An open-access dataset acting as a layer used in a web map product.


record = make_record(
    open_access=True,
    file_identifier="e0743576-e05d-49cd-b7bf-01a0b3ad0430",
    hierarchy_level=HierarchyLevelCode.DATASET,
    title="Test Resource - Web Map Dataset Layer",
    abstract="Item to test a Dataset used as a layer in a Web Map is presented correctly.",
)
# add parent web map
record.identification.aggregations.append(
    Aggregation(
        identifier=Identifier(identifier="a59b5c5b-b099-4f01-b670-3800cb65e666", namespace=CATALOGUE_NAMESPACE),
        association_type=AggregationAssociationCode.LARGER_WORK_CITATION,
        initiative_type=AggregationInitiativeCode.MAP_LAYER,
    )
)
