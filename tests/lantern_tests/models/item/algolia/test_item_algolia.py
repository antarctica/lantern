import json
from copy import deepcopy
from datetime import UTC, date, datetime

import pytest
from bas_metadata_library.standards.magic_administration.v1 import AdministrationMetadata
from bas_metadata_library.standards.magic_administration.v1.utils import AdministrationKeys

from lantern.lib.metadata_library.models.record.elements.common import Constraint, ContactIdentity, Date, Identifier
from lantern.lib.metadata_library.models.record.elements.identification import Aggregation, GraphicOverview
from lantern.lib.metadata_library.models.record.enums import (
    AggregationAssociationCode,
    ConstraintRestrictionCode,
    ConstraintTypeCode,
)
from lantern.lib.metadata_library.models.record.presets.admin import OPEN_ACCESS
from lantern.lib.metadata_library.models.record.utils.admin import set_admin
from lantern.models.item.algolia.item import ItemAlgolia, ObjectRecord
from lantern.models.record.const import CATALOGUE_NAMESPACE
from lantern.models.record.record import Record
from lantern.models.record.revision import RecordRevision
from lantern.models.site import SiteMeta


class TestItemAlgolia:
    """Test Algolia search item."""

    def test_init_record_revision(
        self, fx_site_meta: SiteMeta, fx_revision_model_min: RecordRevision, fx_admin_meta_keys: AdministrationKeys
    ):
        """Can create an ItemAlgolia from a Catalogue record revision."""
        fx_revision_model_min.identification.supplemental_information = "x"

        item = ItemAlgolia(record=fx_revision_model_min, admin_keys=fx_admin_meta_keys)
        assert isinstance(item, ItemAlgolia)
        assert item.record.file_identifier == fx_revision_model_min.file_identifier
        assert item.record.identification.supplemental_information is None

    def test_init_object(self, fx_site_meta: SiteMeta, fx_item_algolia_object_min: ObjectRecord):
        """Can create an ItemAlgolia from an Algolia search index object."""
        item = ItemAlgolia(algolia_object=fx_item_algolia_object_min, admin_keys=None)
        assert isinstance(item, ItemAlgolia)
        assert isinstance(item.record, RecordRevision)

    @pytest.mark.cov()
    def test_init_record(self, fx_site_meta: SiteMeta, fx_record_model_min: Record):
        """Cannot create an ItemAlgolia from a record without a revision."""
        with pytest.raises(TypeError, match=r"Record must be a RecordRevision."):
            # noinspection PyTypeChecker
            _ = ItemAlgolia(record=fx_record_model_min, admin_keys=None)

    @pytest.mark.cov()
    def test_init_empty(self, fx_site_meta: SiteMeta):
        """Cannot create an ItemAlgolia without a record or index object."""
        with pytest.raises(TypeError, match=r"Catalogue record revision or an Algolia object must be provided."):
            ItemAlgolia()

    @pytest.mark.parametrize("poc_type", ["o", "i"])
    @pytest.mark.parametrize("unrestricted", [False, True])
    def test_loads_from_algolia_object(
        self, fx_item_algolia_object_min: ObjectRecord, poc_type: str, unrestricted: bool
    ):
        """Can create a minimal record from an Algolia search object."""
        record_data = json.loads(fx_item_algolia_object_min["objectRecData"])
        record_data[0] = poc_type
        fx_item_algolia_object_min["objectRecData"] = json.dumps(record_data, ensure_ascii=False)
        if unrestricted:
            fx_item_algolia_object_min["restricted"] = False
        exp_restriction = (
            ConstraintRestrictionCode.UNRESTRICTED if unrestricted else ConstraintRestrictionCode.RESTRICTED
        )

        result = ItemAlgolia._loads_from_algolia_object(fx_item_algolia_object_min)
        assert isinstance(result, RecordRevision)
        result.validate()

        _poc_org = result.metadata.contacts[0].organisation
        _poc_inv = result.metadata.contacts[0].individual
        if poc_type == "o":
            assert _poc_org is not None
            assert _poc_inv is None
        elif poc_type == "i":
            assert _poc_org is None
            assert _poc_inv is not None
        assert len(result.identification.constraints.filter(restrictions=exp_restriction)) == 1

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            (date(2014, 6, 30), 1404086400),  # 2014-06-30 00:00:00
            (datetime(2014, 6, 30, 14, 20, 45, tzinfo=UTC), 1404138045),
        ],
    )
    def test_to_timestamp(self, value: date | datetime, expected: int):
        """Can encode date(time) as a Unix timestamp."""
        assert ItemAlgolia._to_timestamp(value) == expected

    @pytest.mark.parametrize("poc_type", ["o", "i"])
    def test_record_data(self, fx_revision_model_min: RecordRevision, poc_type: str):
        """Can generate JSON encoded tuple for additional information from record."""
        expected_name = "x" if poc_type == "o" else "xx"
        expected_poc_email = "e"
        expected_creation = "2014-06-30"

        if poc_type == "i":
            fx_revision_model_min.identification.contacts[0].organisation = None
            fx_revision_model_min.identification.contacts[0].individual = ContactIdentity(name=expected_name)
        fx_revision_model_min.identification.contacts[0].email = expected_poc_email

        item = ItemAlgolia(record=fx_revision_model_min, admin_keys=None)
        result = item._record_data
        data = json.loads(result)

        assert isinstance(data, list)  # Tuples become lists in JSON
        assert len(data) == 4
        assert data[0] == poc_type
        assert data[1] == expected_name
        assert data[2] == expected_poc_email
        assert data[3] == expected_creation

    @pytest.mark.parametrize("unrestricted", [False, True])
    @pytest.mark.parametrize("has_purpose", [False, True])
    @pytest.mark.parametrize("has_publication", [False, True])
    @pytest.mark.parametrize("has_edition", [False, True])
    @pytest.mark.parametrize("has_graphic", [False, True])
    @pytest.mark.parametrize("has_children", [False, True])
    def test_object(
        self,
        fx_revision_model_min: RecordRevision,
        fx_item_algolia_object_min: ObjectRecord,
        fx_admin_meta_keys: AdministrationKeys,
        unrestricted: bool,
        has_purpose: bool,
        has_publication: bool,
        has_edition: bool,
        has_graphic: bool,
        has_children: bool,
    ):
        """Can create an Algolia search object from a record."""
        fx_revision_model_min.identification.title = "_x_"

        if unrestricted:
            set_admin(
                keys=fx_admin_meta_keys,
                record=fx_revision_model_min,
                admin_meta=AdministrationMetadata(
                    id=fx_revision_model_min.file_identifier,
                    metadata_permissions=[OPEN_ACCESS],
                    resource_permissions=[OPEN_ACCESS],
                ),
            )
            fx_item_algolia_object_min["restricted"] = False
        if has_purpose:
            fx_revision_model_min.identification.purpose = "_x_"
            fx_item_algolia_object_min["summaryHtml"] = "<p><em>x</em></p>"
        if has_publication:
            fx_revision_model_min.identification.dates.publication = Date(date=date(2014, 6, 30))
            fx_item_algolia_object_min["date"] = "30 June 2014"
            fx_item_algolia_object_min["objectDate"] = 1404086400
        if has_edition:
            fx_revision_model_min.identification.edition = "X"
            fx_item_algolia_object_min["edition"] = "Ed. X"
        if has_graphic:
            fx_revision_model_min.identification.graphic_overviews.append(
                GraphicOverview(identifier="overview", href="x.jpg", mime_type="x")
            )
            fx_item_algolia_object_min["imageUrl"] = "x.jpg"
        if has_children:
            fx_revision_model_min.identification.aggregations.append(
                Aggregation(
                    identifier=Identifier(identifier="x", namespace=CATALOGUE_NAMESPACE),
                    association_type=AggregationAssociationCode.IS_COMPOSED_OF,
                )
            )
            fx_item_algolia_object_min["childrenCountFmt"] = "1 item"

        item = ItemAlgolia(record=fx_revision_model_min, admin_keys=fx_admin_meta_keys)
        result = item.object
        assert result == fx_item_algolia_object_min

    @pytest.mark.cov()
    def test_object_from_object(self, fx_item_algolia_object_min: ObjectRecord):
        """Cannot create an Algolia search object from an existing object."""
        item = ItemAlgolia(algolia_object=fx_item_algolia_object_min)
        with pytest.raises(ValueError, match=r"Creating Algolia objects requires a record."):
            _ = item.object

    def test_min_loop(self, fx_revision_model_min: RecordRevision):
        """
        Can convert from minimal record to Algolia search object and back.

        This is only lossless for a minimal record.
        """
        item = ItemAlgolia(record=fx_revision_model_min, admin_keys=None)
        obj_from_record = item.object
        record_from_obj = item._loads_from_algolia_object(obj_from_record)

        expected = deepcopy(fx_revision_model_min)
        # reconstructed records have an 'empty' abstract
        expected.identification.abstract = "-"
        # reconstructed records include email in metadata PoC
        expected.metadata.contacts[0].email = expected.identification.contacts[0].email
        # reconstructed records include an access constraint representing admin metadata resource permissions (or lack of)
        expected.identification.constraints.append(
            Constraint(type=ConstraintTypeCode.ACCESS, restriction_code=ConstraintRestrictionCode.RESTRICTED)
        )
        assert record_from_obj == expected
