import json

import pytest

from lantern.lib.metadata_library.models.record.elements.common import Contact as RecordContact
from lantern.lib.metadata_library.models.record.elements.common import (
    ContactIdentity,
    Identifier,
    Identifiers,
    OnlineResource,
    Series,
)
from lantern.lib.metadata_library.models.record.elements.common import Contacts as RecordContacts
from lantern.lib.metadata_library.models.record.elements.data_quality import DataQuality, Lineage
from lantern.lib.metadata_library.models.record.elements.distribution import Distribution, TransferOption
from lantern.lib.metadata_library.models.record.elements.identification import (
    Aggregation,
    Aggregations,
    BoundingBox,
    Constraint,
    Constraints,
    ExtentGeographic,
    GraphicOverview,
    GraphicOverviews,
)
from lantern.lib.metadata_library.models.record.elements.identification import Extent as RecordExtent
from lantern.lib.metadata_library.models.record.elements.identification import Extents as RecordExtents
from lantern.lib.metadata_library.models.record.elements.projection import Code, ReferenceSystemInfo
from lantern.lib.metadata_library.models.record.enums import (
    AggregationAssociationCode,
    AggregationInitiativeCode,
    ConstraintRestrictionCode,
    ConstraintTypeCode,
    ContactRoleCode,
    HierarchyLevelCode,
    OnlineResourceFunctionCode,
)
from lantern.lib.metadata_library.models.record.presets.projections import EPSG_4326
from lantern.models.item.base import ItemBase
from lantern.models.item.base.elements import Contact, Contacts, Extent, Extents
from lantern.models.item.base.enums import AccessLevel
from lantern.models.record.revision import RecordRevision


class TestItemBase:
    """Test base item."""

    def test_init(self, fx_revision_model_min: RecordRevision):
        """Can create an ItemBase from a Record."""
        item = ItemBase(fx_revision_model_min)
        assert item._record == fx_revision_model_min

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ("", []),
            ("invalid", []),
            (
                f"#{json.dumps([{'scheme': 'x', 'schemeVersion': 'x'}])}",
                [],
            ),
            (
                f"#{json.dumps([{'scheme': 'ms_graph', 'schemeVersion': '1', 'directoryId': 'x', 'objectId': 'x'}])}",
                [],
            ),
            (
                f"#{json.dumps([{'scheme': 'ms_graph', 'schemeVersion': '1', 'directoryId': 'b311db95-32ad-438f-a101-7ba061712a4e', 'objectId': '6fa3b48c-393c-455f-b787-c006f839b51f'}])}",
                [AccessLevel.BAS_ALL],
            ),
        ],
    )
    def test_parse_permissions(self, value: str, expected: list[AccessLevel]):
        """Can parse permissions string."""
        result = ItemBase._parse_permissions(value)
        assert result == expected

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            (Constraints([]), AccessLevel.NONE),
            (
                Constraints(
                    [
                        Constraint(
                            type=ConstraintTypeCode.ACCESS, restriction_code=ConstraintRestrictionCode.UNRESTRICTED
                        )
                    ]
                ),
                AccessLevel.PUBLIC,
            ),
            (
                Constraints(
                    [
                        Constraint(
                            type=ConstraintTypeCode.ACCESS, restriction_code=ConstraintRestrictionCode.UNRESTRICTED
                        ),
                        Constraint(
                            type=ConstraintTypeCode.ACCESS, restriction_code=ConstraintRestrictionCode.UNRESTRICTED
                        ),
                    ]
                ),
                AccessLevel.NONE,
            ),
            (
                Constraints(
                    [Constraint(type=ConstraintTypeCode.ACCESS, restriction_code=ConstraintRestrictionCode.RESTRICTED)]
                ),
                AccessLevel.BAS_SOME,
            ),
            (
                Constraints(
                    [
                        Constraint(
                            type=ConstraintTypeCode.ACCESS, restriction_code=ConstraintRestrictionCode.RESTRICTED
                        ),
                        Constraint(
                            type=ConstraintTypeCode.ACCESS, restriction_code=ConstraintRestrictionCode.RESTRICTED
                        ),
                    ]
                ),
                AccessLevel.NONE,
            ),
            (
                Constraints(
                    [
                        Constraint(
                            type=ConstraintTypeCode.ACCESS, restriction_code=ConstraintRestrictionCode.UNRESTRICTED
                        ),
                        Constraint(
                            type=ConstraintTypeCode.ACCESS, restriction_code=ConstraintRestrictionCode.RESTRICTED
                        ),
                    ]
                ),
                AccessLevel.NONE,
            ),
            (
                Constraints(
                    [
                        Constraint(
                            type=ConstraintTypeCode.ACCESS,
                            restriction_code=ConstraintRestrictionCode.RESTRICTED,
                            href=f"#{json.dumps([{'scheme': 'ms_graph', 'schemeVersion': '1', 'directoryId': 'b311db95-32ad-438f-a101-7ba061712a4e', 'objectId': '6fa3b48c-393c-455f-b787-c006f839b51f'}])}",
                        ),
                    ]
                ),
                AccessLevel.BAS_ALL,
            ),
            (
                Constraints(
                    [
                        Constraint(
                            type=ConstraintTypeCode.ACCESS,
                            restriction_code=ConstraintRestrictionCode.RESTRICTED,
                            href=f"#{json.dumps([{'scheme': 'ms_graph', 'schemeVersion': '1', 'directoryId': 'b311db95-32ad-438f-a101-7ba061712a4e', 'objectId': '6fa3b48c-393c-455f-b787-c006f839b51f'}])}",
                        ),
                        Constraint(
                            type=ConstraintTypeCode.ACCESS, restriction_code=ConstraintRestrictionCode.UNRESTRICTED
                        ),
                        Constraint(
                            type=ConstraintTypeCode.ACCESS, restriction_code=ConstraintRestrictionCode.RESTRICTED
                        ),
                    ]
                ),
                AccessLevel.BAS_ALL,
            ),
        ],
    )
    def test_parse_access(self, value: Constraints, expected: AccessLevel):
        """Can resolve access type from constraints."""
        result = ItemBase._parse_access(value)
        assert result == expected

    def test_abstract_raw(self, fx_revision_model_min: RecordRevision):
        """Can get aw Abstract."""
        expected = "x"
        fx_revision_model_min.identification.abstract = expected
        item = ItemBase(fx_revision_model_min)

        assert item.abstract_raw == expected

    def test_abstract_md(self, fx_revision_model_min: RecordRevision):
        """Can get abstract with Markdown formatting if present."""
        expected = "x"
        fx_revision_model_min.identification.abstract = expected
        item = ItemBase(fx_revision_model_min)

        assert item.abstract_md == expected

    def test_abstract_html(self, fx_revision_model_min: RecordRevision):
        """Can get abstract with Markdown formatting, if present, encoded as HTML."""
        value = "_x_"
        expected = "<p><em>x</em></p>"
        fx_revision_model_min.identification.abstract = value
        item = ItemBase(fx_revision_model_min)

        assert item.abstract_html == expected

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            (
                Constraint(type=ConstraintTypeCode.ACCESS, restriction_code=ConstraintRestrictionCode.UNRESTRICTED),
                AccessLevel.PUBLIC,
            ),
            (None, AccessLevel.NONE),
        ],
    )
    def test_access(self, fx_revision_model_min: RecordRevision, value: Constraint | None, expected: AccessLevel):
        """Can get optional access constraint and any associated permissions."""
        if value is not None:
            fx_revision_model_min.identification.constraints = Constraints([value])
        item = ItemBase(fx_revision_model_min)

        assert item.access_level == expected

    def test_aggregations(self, fx_revision_model_min: RecordRevision):
        """Can get aggregations from record."""
        expected = Aggregation(
            identifier=Identifier(identifier="x", href="x", namespace="x"),
            association_type=AggregationAssociationCode.LARGER_WORK_CITATION,
            initiative_type=AggregationInitiativeCode.COLLECTION,
        )
        fx_revision_model_min.identification.aggregations = Aggregations([expected])
        item = ItemBase(fx_revision_model_min)

        result = item.aggregations

        assert isinstance(result, Aggregations)
        assert len(result) > 0

    def test_bounding_extent(self, fx_revision_model_min: RecordRevision):
        """Can get bounding extent from record."""
        rec_extent = RecordExtent(
            identifier="bounding",
            geographic=ExtentGeographic(
                bounding_box=BoundingBox(west_longitude=1.0, east_longitude=1.0, south_latitude=1.0, north_latitude=1.0)
            ),
        )
        fx_revision_model_min.identification.extents = RecordExtents([rec_extent])
        expected = Extent(rec_extent)
        item = ItemBase(fx_revision_model_min)

        result = item.bounding_extent
        assert isinstance(result, Extent)
        assert result == expected

    @pytest.mark.parametrize("expected", ["x", None])
    def test_citation_raw(self, fx_revision_model_min: RecordRevision, expected: str | None):
        """Raw citation."""
        fx_revision_model_min.identification.other_citation_details = expected
        item = ItemBase(fx_revision_model_min)

        assert item.citation_raw == expected

    @pytest.mark.parametrize("expected", ["_x_", None])
    def test_citation_md(self, fx_revision_model_min: RecordRevision, expected: str | None):
        """Citation with Markdown formatting if present."""
        fx_revision_model_min.identification.other_citation_details = expected
        item = ItemBase(fx_revision_model_min)

        assert item.citation_md == expected

    @pytest.mark.parametrize(("value", "expected"), [("x", "<p>x</p>"), ("_x_", "<p><em>x</em></p>"), (None, None)])
    def test_citation_html(self, fx_revision_model_min: RecordRevision, value: str | None, expected: str | None):
        """
        Citation with Markdown formatting, if present, encoded as HTML.

        Parameters used to test handling of optional value.
        """
        fx_revision_model_min.identification.other_citation_details = value
        item = ItemBase(fx_revision_model_min)

        if value is None:
            assert item.citation_html is None
        if value is not None:
            assert item.citation_html.startswith("<p>")
            assert item.citation_html.endswith("</p>")
        if value == "_Markdown_":
            assert "<em>Markdown</em>" in item.citation_html

    def test_collections(self, fx_revision_model_min: RecordRevision):
        """Can filter collection aggregations from record."""
        expected = Aggregation(
            identifier=Identifier(identifier="x", href="x", namespace="x"),
            association_type=AggregationAssociationCode.LARGER_WORK_CITATION,
            initiative_type=AggregationInitiativeCode.COLLECTION,
        )
        fx_revision_model_min.identification.aggregations = Aggregations([expected])
        item = ItemBase(fx_revision_model_min)

        result = item.collections

        assert isinstance(result, Aggregations)
        assert len(result) > 0

        assert expected in result
        assert len(result) == 1
        assert result[0] == expected

    def test_contacts(self, fx_revision_model_min: RecordRevision):
        """Can get record contacts as item contacts."""
        rec_contact = RecordContact(
            organisation=ContactIdentity(name="x", title="ror", href="x"), role={ContactRoleCode.POINT_OF_CONTACT}
        )
        fx_revision_model_min.identification.contacts = RecordContacts([rec_contact])
        expected = Contact(rec_contact)
        item = ItemBase(fx_revision_model_min)

        result = item.contacts
        assert isinstance(result, Contacts)
        assert expected in result

        # check underlying record contacts haven't been modified
        assert type(item._record.identification.contacts) is not type(result)
        assert item._record.identification.contacts != result
        assert item._record.identification.contacts[0] != result[0]
        with pytest.raises(AttributeError):
            # noinspection PyUnresolvedReferences
            _ = item._record.identification.contacts[0].ror

    def test_constraints(self, fx_revision_model_min: RecordRevision):
        """Can get constraints from record."""
        expected = Constraint(type=ConstraintTypeCode.ACCESS)
        fx_revision_model_min.identification.constraints = Constraints([expected])
        item = ItemBase(fx_revision_model_min)

        result = item.constraints

        assert isinstance(result, Constraints)
        assert len(result) > 0

    def test_distributions(self, fx_revision_model_min: RecordRevision):
        """Can get record distributions as item distributions."""
        expected = [
            Distribution(
                distributor=RecordContact(organisation=ContactIdentity(name="x"), role={ContactRoleCode.DISTRIBUTOR}),
                transfer_option=TransferOption(
                    online_resource=OnlineResource(href="x", function=OnlineResourceFunctionCode.DOWNLOAD)
                ),
            )
        ]
        fx_revision_model_min.distribution = expected

        item = ItemBase(fx_revision_model_min)

        assert item.distributions == expected

    def test_edition(self, fx_revision_model_min: RecordRevision):
        """Can get edition."""
        expected = "x"
        fx_revision_model_min.identification.edition = "x"
        item = ItemBase(fx_revision_model_min)

        assert item.edition == expected

    def test_extents(self, fx_revision_model_min: RecordRevision):
        """Can get record extents as item extents."""
        rec_extent = RecordExtent(
            identifier="bounding",
            geographic=ExtentGeographic(
                bounding_box=BoundingBox(west_longitude=1.0, east_longitude=1.0, south_latitude=1.0, north_latitude=1.0)
            ),
        )
        fx_revision_model_min.identification.extents = RecordExtents([rec_extent])
        expected = Extent(rec_extent)
        item = ItemBase(fx_revision_model_min)

        result = item.extents
        assert isinstance(result, Extents)
        assert expected in result

        # check underlying record extents haven't been modified
        assert type(item._record.identification.extents) is not type(result)
        assert item._record.identification.extents != result
        assert item._record.identification.extents[0] != result[0]
        with pytest.raises(AttributeError):
            # noinspection PyUnresolvedReferences
            _ = item._record.identification.extents[0].bounding_box

    def test_graphics(self, fx_revision_model_min: RecordRevision):
        """Can get graphic overviews from record."""
        expected = GraphicOverview(identifier="x", href="x", mime_type="x")
        fx_revision_model_min.identification.graphic_overviews = GraphicOverviews([expected])
        item = ItemBase(fx_revision_model_min)

        result = item.graphics

        assert isinstance(result, GraphicOverviews)
        assert len(result) > 0

    def test_href(self, fx_revision_model_min: RecordRevision):
        """Can get item href."""
        expected = f"/items/{fx_revision_model_min.file_identifier}/"
        item = ItemBase(fx_revision_model_min)

        assert item.href == expected

    def test_identifiers(self, fx_revision_model_min: RecordRevision):
        """Can get identifiers from record."""
        expected = Identifier(identifier="x", href="x", namespace="x")
        fx_revision_model_min.identification.identifiers = Identifiers([expected])
        item = ItemBase(fx_revision_model_min)

        result = item.identifiers

        assert isinstance(result, Identifiers)
        assert len(result) > 0

    @pytest.mark.parametrize(
        "value",
        [
            Constraint(
                type=ConstraintTypeCode.USAGE,
                restriction_code=ConstraintRestrictionCode.LICENSE,
                href="x",
                statement="x",
            ),
            None,
        ],
    )
    def test_licence(self, fx_revision_model_min: RecordRevision, value: Constraint | None):
        """Can get optional licence usage constraint."""
        if value is not None:
            fx_revision_model_min.identification.constraints = Constraints([value])
        item = ItemBase(fx_revision_model_min)

        assert item.licence == value

    @pytest.mark.parametrize("expected", ["x", None])
    def test_lineage_raw(self, fx_revision_model_min: RecordRevision, expected: str | None):
        """Can get raw lineage statement."""
        if expected is not None:
            fx_revision_model_min.data_quality = DataQuality(lineage=Lineage(statement=expected))
        item = ItemBase(fx_revision_model_min)

        assert item.lineage_raw == expected

    @pytest.mark.parametrize("expected", ["_x_", None])
    def test_lineage_md(self, fx_revision_model_min: RecordRevision, expected: str | None):
        """Can get lineage statement with Markdown formatting if present."""
        if expected is not None:
            fx_revision_model_min.data_quality = DataQuality(lineage=Lineage(statement=expected))
        item = ItemBase(fx_revision_model_min)

        assert item.lineage_md == expected

    @pytest.mark.parametrize(("value", "expected"), [("x", "<p>x</p>"), ("_x_", "<p><em>x</em></p>"), (None, None)])
    def test_lineage_html(self, fx_revision_model_min: RecordRevision, value: str | None, expected: str | None):
        """Can get lineage statement with Markdown formatting, if present, encoded as HTML."""
        if expected is not None:
            fx_revision_model_min.data_quality = DataQuality(lineage=Lineage(statement=expected))
        item = ItemBase(fx_revision_model_min)

        assert item.lineage_html == expected

    @pytest.mark.parametrize(
        "value",
        [
            GraphicOverviews([]),
            GraphicOverviews([GraphicOverview(identifier="x", href="x", mime_type="x")]),
            GraphicOverviews([GraphicOverview(identifier="overview", href="x", mime_type="x")]),
            GraphicOverviews(
                [
                    GraphicOverview(identifier="overview", href="x", mime_type="x"),
                    GraphicOverview(identifier="overview", href="y", mime_type="y"),
                ]
            ),
        ],
    )
    def test_overview_graphic(self, fx_revision_model_min: RecordRevision, value: GraphicOverviews):
        """Can get graphic overviews from record."""
        fx_revision_model_min.identification.graphic_overviews = value
        item = ItemBase(fx_revision_model_min)

        result = item.overview_graphic

        if len(value) == 0:
            assert result is None
        if len(value) > 0 and value[0].identifier != "overview":
            assert result is None
        if len(value) > 0 and value[0].identifier == "overview":
            assert isinstance(result, GraphicOverview)

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            (None, None),
            (
                ReferenceSystemInfo(
                    code=Code(
                        value="x",
                    )
                ),
                None,
            ),
            (
                EPSG_4326,
                Identifier(identifier="EPSG:4326", href="http://www.opengis.net/def/crs/EPSG/0/4326", namespace="epsg"),
            ),
        ],
    )
    def test_projection(
        self, fx_revision_model_min: RecordRevision, value: ReferenceSystemInfo | None, expected: str | None
    ):
        """Can get projection if present and an EPSG code."""
        fx_revision_model_min.reference_system_info = value
        item = ItemBase(fx_revision_model_min)

        assert item.projection == expected

    def test_resource_id(self, fx_revision_model_min: RecordRevision):
        """Can get resource/file identifier."""
        expected = "x"
        item = ItemBase(fx_revision_model_min)
        item._record.file_identifier = expected

        assert item.resource_id == expected

    def test_resource_revision(self, fx_revision_model_min: RecordRevision):
        """Can get resource/file revision."""
        expected = "x"
        item = ItemBase(fx_revision_model_min)
        item._record.file_revision = expected

        assert item.resource_revision == expected

    def test_resource_type(self, fx_revision_model_min: RecordRevision):
        """Can get resource type / hierarchy level."""
        expected = HierarchyLevelCode.DATASET
        item = ItemBase(fx_revision_model_min)

        assert item.resource_type == expected

    @pytest.mark.parametrize(
        ("series", "sheet", "expected"),
        [
            (None, None, None),
            (Series(name="x", edition="x"), None, Series(name="x", edition="x")),
            (Series(name="x", edition="x"), "x", Series(name="x", page="x", edition="x")),
        ],
    )
    def test_series_descriptive(
        self,
        fx_revision_model_min: RecordRevision,
        series: Series,
        sheet: str | None,
        expected: Series | None,
    ):
        """Can get optional descriptive series including sheet number via workaround."""
        fx_revision_model_min.identification.series = series
        if sheet:
            fx_revision_model_min.identification.supplemental_information = json.dumps({"sheet_number": sheet})
        item = ItemBase(fx_revision_model_min)

        assert item.series_descriptive == expected

    @pytest.mark.parametrize("expected", ["x", None])
    def test_summary_raw(self, fx_revision_model_min: RecordRevision, expected: str | None):
        """Can get optional raw Summary (purpose)."""
        fx_revision_model_min.identification.purpose = expected
        item = ItemBase(fx_revision_model_min)

        assert item.summary_raw == expected

    @pytest.mark.parametrize("expected", ["_x_", None])
    def test_summary_md(self, fx_revision_model_min: RecordRevision, expected: str | None):
        """Can get optional summary (purpose) with Markdown formatting."""
        fx_revision_model_min.identification.purpose = expected
        item = ItemBase(fx_revision_model_min)

        assert item.summary_md == expected

    @pytest.mark.parametrize(("value", "expected"), [("x", "<p>x</p>"), ("_x_", "<p><em>x</em></p>"), (None, None)])
    def test_summary_html(self, fx_revision_model_min: RecordRevision, value: str | None, expected: str | None):
        """Can get summary (purpose) with Markdown formatting, if present, encoded as HTML."""
        if expected is not None:
            fx_revision_model_min.identification.purpose = value
        item = ItemBase(fx_revision_model_min)

        assert item.summary_html == expected

    @pytest.mark.parametrize(("value", "expected"), [("x", "x"), ("_x_", "x")])
    def test_summary_plain(self, fx_revision_model_min: RecordRevision, value: str, expected: str):
        """Can get optional summary (purpose) without Markdown formatting."""
        fx_revision_model_min.identification.purpose = value
        item = ItemBase(fx_revision_model_min)

        assert item.summary_plain == expected

    @pytest.mark.parametrize(("value", "expected"), [(None, {}), ("", {}), ({}, {}), ('{"x":"x"}', {"x": "x"})])
    def test_kv(self, fx_revision_model_min: RecordRevision, value: str | None, expected: dict[str, str]):
        """Can get supplemental information as a key value dict."""
        fx_revision_model_min.identification.supplemental_information = value
        item = ItemBase(fx_revision_model_min)

        assert item.kv == expected

    def test_title_raw(self, fx_revision_model_min: RecordRevision):
        """Can get raw title."""
        item = ItemBase(fx_revision_model_min)

        assert item.title_raw == "x"

    def test_title_md(self, fx_revision_model_min: RecordRevision):
        """Can get title with Markdown formatting."""
        item = ItemBase(fx_revision_model_min)

        assert item.title_md == "x"

    @pytest.mark.parametrize(("value", "expected"), [("x", "x"), ("_x_", "x")])
    def test_title_plain(self, fx_revision_model_min: RecordRevision, value: str, expected: str):
        """Can get title without Markdown formatting."""
        fx_revision_model_min.identification.title = value
        item = ItemBase(fx_revision_model_min)

        assert item.title_plain == expected
