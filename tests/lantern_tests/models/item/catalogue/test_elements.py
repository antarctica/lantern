from datetime import UTC, date, datetime

import pytest

from lantern.lib.metadata_library.models.record.elements.common import (
    Date,
    Identifier,
)
from lantern.lib.metadata_library.models.record.elements.common import Dates as RecordDates
from lantern.lib.metadata_library.models.record.elements.common import Identifiers as RecordIdentifiers
from lantern.lib.metadata_library.models.record.elements.common import (
    Maintenance as RecordMaintenance,
)
from lantern.lib.metadata_library.models.record.elements.identification import (
    Aggregation,
    BoundingBox,
    ExtentGeographic,
    ExtentTemporal,
    GraphicOverview,
    TemporalPeriod,
)
from lantern.lib.metadata_library.models.record.elements.identification import Aggregations as RecordAggregations
from lantern.lib.metadata_library.models.record.elements.identification import Extent as RecordExtent
from lantern.lib.metadata_library.models.record.enums import (
    AggregationAssociationCode,
    AggregationInitiativeCode,
    DatePrecisionCode,
    DateTypeCode,
    HierarchyLevelCode,
    MaintenanceFrequencyCode,
    ProgressCode,
)
from lantern.lib.metadata_library.models.record.utils.admin import AdministrationKeys
from lantern.models.item.base.elements import Extent as ItemExtent
from lantern.models.item.base.elements import Link
from lantern.models.item.base.enums import ResourceTypeIcon, ResourceTypeLabel
from lantern.models.item.base.item import ItemBase
from lantern.models.item.catalogue.const import CONTAINER_SUPER_TYPES
from lantern.models.item.catalogue.elements import (
    Aggregations,
    Dates,
    Extent,
    FormattedDate,
    Identifiers,
    ItemCatalogueSummary,
    Maintenance,
    PageHeader,
    PageSummary,
)
from lantern.models.item.catalogue.enums import ItemSuperType
from lantern.models.record.const import ALIAS_NAMESPACE, CATALOGUE_NAMESPACE
from tests.conftest import _admin_meta_keys, _select_record


class TestFormattedDate:
    """Test Catalogue Item formatted dates."""

    def test_init(self):
        """Can create a FormattedDate element."""
        fd = FormattedDate(datetime="x", value="x")

        assert fd.datetime == "x"
        assert fd.value == "x"

    @pytest.mark.parametrize(
        ("value", "exp_value", "exp_dt"),
        [
            (Date(date=date(2014, 1, 1), precision=DatePrecisionCode.YEAR), "2014", "2014"),
            (Date(date=date(2014, 6, 1), precision=DatePrecisionCode.MONTH), "June 2014", "2014-06"),
            (Date(date=date(2014, 6, 30)), "30 June 2014", "2014-06-30"),
            (
                Date(date=datetime(2014, 6, 30, 13, tzinfo=UTC)),
                "30 June 2014 13:00:00 UTC",
                "2014-06-30T13:00:00+00:00",
            ),
            (Date(date=datetime(2014, 6, 29, 1, tzinfo=UTC)), "29 June 2014", "2014-06-29"),
        ],
    )
    def test_from_record_date(self, value: Date, exp_value: str, exp_dt: str):
        """Can create a FormattedDate from a Record Date."""
        now = datetime(2014, 6, 30, 14, 30, second=45, tzinfo=UTC)
        result = FormattedDate.from_rec_date(value, relative_to=now)

        assert result.value == exp_value
        assert result.datetime == exp_dt

    def test_invalid_date(self):
        """Cannot process an invalid value."""
        now = datetime(2014, 6, 30, 14, 30, second=45, tzinfo=UTC)
        with pytest.raises(TypeError):
            FormattedDate.from_rec_date("", relative_to=now)


class TestAggregations:
    """Test Catalogue Item aggregations."""

    def test_init(self, fx_admin_meta_keys: AdministrationKeys):
        """Can create an Aggregations collection."""
        expected_aggregation = Aggregation(
            identifier=Identifier(identifier="x", href="x", namespace=CATALOGUE_NAMESPACE),
            association_type=AggregationAssociationCode.LARGER_WORK_CITATION,
            initiative_type=AggregationInitiativeCode.COLLECTION,
        )
        expected_record = _select_record("x")
        record_aggregations = RecordAggregations([expected_aggregation])

        aggregations = Aggregations(
            admin_meta_keys=fx_admin_meta_keys, aggregations=record_aggregations, select_record=_select_record
        )

        assert isinstance(aggregations, Aggregations)
        assert len(aggregations) == 1
        assert aggregations._aggregations[0] == expected_aggregation
        assert aggregations._summaries["x"]._record == expected_record

    def test_peer_collections(self, fx_admin_meta_keys: AdministrationKeys):
        """Can get any collection aggregations (item is a sibling of)."""
        record_aggregations = RecordAggregations(
            [
                Aggregation(
                    identifier=Identifier(identifier="x", href="x", namespace=CATALOGUE_NAMESPACE),
                    association_type=AggregationAssociationCode.CROSS_REFERENCE,
                    initiative_type=AggregationInitiativeCode.COLLECTION,
                )
            ]
        )
        aggregations = Aggregations(
            admin_meta_keys=fx_admin_meta_keys, aggregations=record_aggregations, select_record=_select_record
        )

        assert len(aggregations.peer_collections) > 0

    def test_peer_projects(self, fx_admin_meta_keys: AdministrationKeys):
        """Can get any project aggregations (item is a sibling of)."""
        record_aggregations = RecordAggregations(
            [
                Aggregation(
                    identifier=Identifier(identifier="x", href="x", namespace=CATALOGUE_NAMESPACE),
                    association_type=AggregationAssociationCode.CROSS_REFERENCE,
                    initiative_type=AggregationInitiativeCode.PROJECT,
                )
            ]
        )
        aggregations = Aggregations(
            admin_meta_keys=fx_admin_meta_keys, aggregations=record_aggregations, select_record=_select_record
        )

        assert len(aggregations.peer_projects) > 0

    def test_peer_cross_reference(self, fx_admin_meta_keys: AdministrationKeys):
        """Can get any cross-reference not related to another context (e.g. collections, projects)."""
        record_aggregations = RecordAggregations(
            [
                Aggregation(
                    identifier=Identifier(identifier="x", href="x", namespace=CATALOGUE_NAMESPACE),
                    association_type=AggregationAssociationCode.CROSS_REFERENCE,
                ),
                Aggregation(
                    identifier=Identifier(identifier="y", href="y", namespace=CATALOGUE_NAMESPACE),
                    association_type=AggregationAssociationCode.CROSS_REFERENCE,
                    initiative_type=AggregationInitiativeCode.COLLECTION,
                ),
                Aggregation(
                    identifier=Identifier(identifier="y", href="y", namespace=CATALOGUE_NAMESPACE),
                    association_type=AggregationAssociationCode.CROSS_REFERENCE,
                    initiative_type=AggregationInitiativeCode.PROJECT,
                ),
            ]
        )
        aggregations = Aggregations(
            admin_meta_keys=fx_admin_meta_keys, aggregations=record_aggregations, select_record=_select_record
        )

        assert len(aggregations.peer_cross_reference) == 1

    def test_peer_superseded(self, fx_admin_meta_keys: AdministrationKeys):
        """Can get any superseded items."""
        record_aggregations = RecordAggregations(
            [
                Aggregation(
                    identifier=Identifier(identifier="x", href="x", namespace=CATALOGUE_NAMESPACE),
                    association_type=AggregationAssociationCode.REVISION_OF,
                ),
            ]
        )
        aggregations = Aggregations(
            admin_meta_keys=fx_admin_meta_keys, aggregations=record_aggregations, select_record=_select_record
        )

        assert len(aggregations.peer_supersedes) > 0

    def test_peer_opposite_side(self, fx_admin_meta_keys: AdministrationKeys):
        """Can get any item that forms the opposite side of a published map."""
        record_aggregations = RecordAggregations(
            [
                Aggregation(
                    identifier=Identifier(identifier="x", href="x", namespace=CATALOGUE_NAMESPACE),
                    association_type=AggregationAssociationCode.PHYSICAL_REVERSE_OF,
                    initiative_type=AggregationInitiativeCode.PAPER_MAP,
                )
            ]
        )
        aggregations = Aggregations(
            admin_meta_keys=fx_admin_meta_keys, aggregations=record_aggregations, select_record=_select_record
        )

        assert aggregations.peer_opposite_side is not None

    def test_parent_collections(self, fx_admin_meta_keys: AdministrationKeys):
        """Can get any collection aggregations (item is part of)."""
        record_aggregations = RecordAggregations(
            [
                Aggregation(
                    identifier=Identifier(identifier="x", href="x", namespace=CATALOGUE_NAMESPACE),
                    association_type=AggregationAssociationCode.LARGER_WORK_CITATION,
                    initiative_type=AggregationInitiativeCode.COLLECTION,
                )
            ]
        )
        aggregations = Aggregations(
            admin_meta_keys=fx_admin_meta_keys, aggregations=record_aggregations, select_record=_select_record
        )

        assert len(aggregations.parent_collections) > 0

    def test_parent_projects(self, fx_admin_meta_keys: AdministrationKeys):
        """Can get any project aggregations (item is part of)."""
        record_aggregations = RecordAggregations(
            [
                Aggregation(
                    identifier=Identifier(identifier="x", href="x", namespace=CATALOGUE_NAMESPACE),
                    association_type=AggregationAssociationCode.LARGER_WORK_CITATION,
                    initiative_type=AggregationInitiativeCode.PROJECT,
                )
            ]
        )
        aggregations = Aggregations(
            admin_meta_keys=fx_admin_meta_keys, aggregations=record_aggregations, select_record=_select_record
        )

        assert len(aggregations.parent_projects) > 0

    def test_child_items(self, fx_admin_meta_keys: AdministrationKeys):
        """Can get any item aggregations (item is made up of)."""
        record_aggregations = RecordAggregations(
            [
                Aggregation(
                    identifier=Identifier(identifier="x", href="x", namespace=CATALOGUE_NAMESPACE),
                    association_type=AggregationAssociationCode.IS_COMPOSED_OF,
                    initiative_type=AggregationInitiativeCode.COLLECTION,
                ),
                Aggregation(
                    identifier=Identifier(identifier="y", href="y", namespace=CATALOGUE_NAMESPACE),
                    association_type=AggregationAssociationCode.IS_COMPOSED_OF,
                    initiative_type=AggregationInitiativeCode.PROJECT,
                ),
            ]
        )
        aggregations = Aggregations(
            admin_meta_keys=fx_admin_meta_keys, aggregations=record_aggregations, select_record=_select_record
        )

        assert len(aggregations.child_items) == len(record_aggregations)

    def test_parent_printed_map(self, fx_admin_meta_keys: AdministrationKeys):
        """Can get printed map item that this item is a side of."""
        record_aggregations = RecordAggregations(
            [
                Aggregation(
                    identifier=Identifier(identifier="x", href="x", namespace=CATALOGUE_NAMESPACE),
                    association_type=AggregationAssociationCode.LARGER_WORK_CITATION,
                    initiative_type=AggregationInitiativeCode.PAPER_MAP,
                )
            ]
        )
        aggregations = Aggregations(
            admin_meta_keys=fx_admin_meta_keys, aggregations=record_aggregations, select_record=_select_record
        )

        assert aggregations.parent_printed_map is not None


class TestDates:
    """Test Catalogue Item dates."""

    def test_init(self):
        """Can create a Dates collection."""
        record_dates = RecordDates(
            creation=Date(date=datetime(2014, 6, 30, 14, 30, second=45, tzinfo=UTC)),
        )

        dates = Dates(dates=record_dates)

        assert isinstance(dates, Dates)

    def test_formatting(self):
        """Can get a formatted date when accessed."""
        date_ = Date(date=datetime(2014, 6, 30, 14, 30, second=45, tzinfo=UTC))
        expected = FormattedDate.from_rec_date(date_)

        dates = Dates(dates=RecordDates(creation=date_))

        assert dates.creation == expected

    def test_as_dict_enum(self):
        """Can get dates as a DateTypeCode indexed dict."""
        date_ = Date(date=datetime(2014, 6, 30, 14, 30, second=45, tzinfo=UTC))
        dates = Dates(dates=RecordDates(creation=date_))
        expected = {DateTypeCode.CREATION: FormattedDate.from_rec_date(date_)}

        assert dates.as_dict_enum() == expected

    def test_as_dict_labeled(self):
        """Can get dates as a dict with human formatted keys."""
        date_ = Date(date=datetime(2014, 6, 30, 14, 30, second=45, tzinfo=UTC))
        dates = Dates(dates=RecordDates(creation=date_))
        expected = {"Item Created": FormattedDate.from_rec_date(date_)}

        assert dates.as_dict_labeled() == expected


class TestExtent:
    """Test Catalogue Item extent."""

    def test_init(self):
        """Can create an Extent element."""
        item_extent = ItemExtent(
            RecordExtent(
                identifier="bounding",
                geographic=ExtentGeographic(
                    bounding_box=BoundingBox(
                        west_longitude=1.0, east_longitude=1.0, south_latitude=1.0, north_latitude=1.0
                    )
                ),
            )
        )

        extent = Extent(extent=item_extent, embedded_maps_endpoint="x")

        assert isinstance(extent, Extent)

    @pytest.mark.parametrize("has_value", [True, False])
    def test_start_end(self, has_value: bool):
        """Can get formated dates for temporal extent period."""
        date_ = Date(date=datetime(2014, 6, 30, 14, 30, second=45, tzinfo=UTC))
        expected = FormattedDate.from_rec_date(date_) if has_value else None
        record_extent = RecordExtent(
            identifier="bounding",
            geographic=ExtentGeographic(
                bounding_box=BoundingBox(west_longitude=1.0, east_longitude=1.0, south_latitude=1.0, north_latitude=1.0)
            ),
        )
        if has_value:
            record_extent.temporal = ExtentTemporal(period=TemporalPeriod(start=date_, end=date_))
        item_extent = ItemExtent(record_extent)

        extent = Extent(extent=item_extent, embedded_maps_endpoint="x")

        assert extent.start == expected
        assert extent.end == expected

    def test_map_iframe(self):
        """Can get iframe fragment for embedded map of extent."""
        item_extent = ItemExtent(
            RecordExtent(
                identifier="bounding",
                geographic=ExtentGeographic(
                    bounding_box=BoundingBox(
                        west_longitude=1.0, east_longitude=2.0, south_latitude=3.0, north_latitude=4.0
                    )
                ),
            )
        )
        expected_bbox = "[1.0,3.0,2.0,4.0]"
        expected = f"https://example.com/?theme=bsk2&bbox={expected_bbox}&globe-overview"

        extent = Extent(extent=item_extent, embedded_maps_endpoint="https://example.com")
        assert extent.map_iframe == expected


class TestItemCatalogueSummary:
    """
    Test Catalogue Item summary.

    Used for showing summaries of other items.
    """

    @pytest.mark.parametrize("has_date", [True, False])
    def test_date_fmt(self, fx_item_base_model_min: ItemBase, has_date: bool):
        """Can get formatted date if set."""
        record = fx_item_base_model_min._record
        publication = Date(date=datetime(2014, 6, 30, tzinfo=UTC).date())
        expected = "30 June 2014" if has_date else None
        if has_date:
            record.identification.dates.publication = publication

        summary = ItemCatalogueSummary(record=record, admin_keys=fx_item_base_model_min._admin_keys)
        if has_date:
            assert isinstance(summary.date_fmt, FormattedDate)
            assert summary.date_fmt.value == expected
        else:
            assert summary.date_fmt is None

    def test_title_no_fmt(self, fx_item_base_model_min: ItemBase):
        """Can get title without any formatting."""
        record = fx_item_base_model_min._record
        record.identification.title = "_x_"

        summary = ItemCatalogueSummary(record=record, admin_keys=fx_item_base_model_min._admin_keys)
        assert summary.title_no_fmt == "x"

    @pytest.mark.parametrize(
        ("resource_type", "count", "expected"),
        [
            (HierarchyLevelCode.PRODUCT, 0, None),
            (HierarchyLevelCode.COLLECTION, 0, None),
            (HierarchyLevelCode.COLLECTION, 1, "1 item"),
            (HierarchyLevelCode.COLLECTION, 2, "2 items"),
            (HierarchyLevelCode.PAPER_MAP_PRODUCT, 1, "1 side"),
            (HierarchyLevelCode.PAPER_MAP_PRODUCT, 2, "2 sides"),
        ],
    )
    def test_children(
        self, fx_item_base_model_min: ItemBase, resource_type: HierarchyLevelCode, count: int, expected: int
    ):
        """Can get formatted count of parent -> child relations."""
        record = fx_item_base_model_min._record
        record.hierarchy_level = resource_type
        for _ in range(count):
            aggregation = Aggregation(
                identifier=Identifier(identifier="x", namespace="x"),
                association_type=AggregationAssociationCode.IS_COMPOSED_OF,
                initiative_type=AggregationInitiativeCode.PAPER_MAP
                if HierarchyLevelCode.PAPER_MAP_PRODUCT
                else AggregationInitiativeCode.COLLECTION,
            )
            record.identification.aggregations.append(aggregation)

        summary = ItemCatalogueSummary(record=record, admin_keys=fx_item_base_model_min._admin_keys)
        assert summary.children == expected

    def test_fragments(self, fx_item_base_model_min: ItemBase, fx_admin_meta_keys: AdministrationKeys):
        """Can get fragments to use as part of item summary UI."""
        summary = ItemCatalogueSummary(record=fx_item_base_model_min.record, admin_keys=fx_admin_meta_keys)
        assert summary.fragments["item_type_label"] is not None

    @pytest.mark.parametrize(
        ("href", "expected"),
        [
            ("x", ("x", "x")),
            (
                None,
                (
                    "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAALQAAAC0CAMAAAAKE/YAAAAC+lBMVEUAAADu7u739/fz8/Pt7e3w",
                    "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAALQAAAC0CAMAAAAKE/YAAAADAFBMVEUAAAAODg4qKiozMzMBAQEVF",
                ),
            ),
        ],
    )
    def test_graphic_href(self, fx_item_base_model_min: ItemBase, href: str | None, expected: tuple[str, str]):
        """
        Can get light and dark graphic from item or using default.

        If present in a record the same image is returned twice as a light and dark image.
        """
        record = fx_item_base_model_min._record
        if href is not None:
            record.identification.graphic_overviews.append(
                GraphicOverview(identifier="overview", href=href, mime_type="x")
            )

        summary = ItemCatalogueSummary(record=record, admin_keys=fx_item_base_model_min._admin_keys)
        if href is not None:
            assert summary.graphic_href == expected
        else:
            assert summary.graphic_href[0].startswith(expected[0])
            assert summary.graphic_href[1].startswith(expected[1])


class TestIdentifiers:
    """Test Catalogue Item identifiers."""

    def test_init(self):
        """Can create an Identifiers element."""
        identifiers = Identifiers(RecordIdentifiers([]))
        assert isinstance(identifiers, Identifiers)

    @pytest.mark.parametrize(
        ("identifiers", "expected"),
        [
            ([], []),
            (
                [Identifier(identifier="x/x", href="https://lantern.data.bas.ac.uk/x/x", namespace=ALIAS_NAMESPACE)],
                [Link(value="x/x", href="/x/x", external=False)],
            ),
        ],
    )
    def test_aliases(self, identifiers: list[Identifier], expected: list[str]):
        """Can get any aliases as relative links."""
        identifiers = Identifiers(RecordIdentifiers(identifiers))
        result = identifiers.aliases
        assert result == expected

    def test_aliases_no_url(self):
        """Cannot get aliases if any don't include a URL."""
        identifiers = Identifiers(RecordIdentifiers([Identifier(identifier="x/x", namespace=ALIAS_NAMESPACE)]))
        with pytest.raises(ValueError, match=r"Aliases must have a href."):
            _ = identifiers.aliases

    @pytest.mark.parametrize(
        ("identifiers", "expected"),
        [
            ([], []),
            (
                [
                    Identifier(
                        identifier="10.123/30825673-6276-4e5a-8a97-f97f2094cd25",
                        href="https://doi.org/10.123/30825673-6276-4e5a-8a97-f97f2094cd25",
                        namespace="doi",
                    )
                ],
                [
                    Link(
                        value="10.123/30825673-6276-4e5a-8a97-f97f2094cd25",
                        href="https://doi.org/10.123/30825673-6276-4e5a-8a97-f97f2094cd25",
                        external=True,
                    )
                ],
            ),
        ],
    )
    def test_doi(self, identifiers: list[Identifier], expected: list[str]):
        """Can get any DOIs."""
        identifiers = Identifiers(RecordIdentifiers(identifiers))
        result = identifiers.doi
        assert result == expected

    @pytest.mark.parametrize(
        ("identifiers", "expected"),
        [([], []), ([Identifier(identifier="978-0-85665-230-1", namespace="isbn")], ["978-0-85665-230-1"])],
    )
    def test_isbn(self, identifiers: list[Identifier], expected: list[str]):
        """Can get any ISBNs."""
        identifiers = Identifiers(RecordIdentifiers(identifiers))
        result = identifiers.isbn
        assert result == expected


class TestMaintenance:
    """Test Catalogue Item maintenance."""

    def test_init(self):
        """Can create a maintenance element."""
        maintenance = Maintenance(RecordMaintenance())
        assert isinstance(maintenance, Maintenance)

    @pytest.mark.parametrize(
        ("progress", "expected"),
        [
            (None, None),
            (ProgressCode.HISTORICAL_ARCHIVE, "Item has been archived and may be outdated"),
        ],
    )
    def test_status(self, progress: ProgressCode | None, expected: ProgressCode | None):
        """Can get formatted progress code as status if set."""
        maintenance = Maintenance(RecordMaintenance(progress=progress))
        assert maintenance.status == expected

    @pytest.mark.parametrize(
        ("frequency", "expected"), [(None, None), (MaintenanceFrequencyCode.IRREGULAR, "Item is updated irregularly")]
    )
    def test_frequency(self, frequency: MaintenanceFrequencyCode | None, expected: ProgressCode | None):
        """Can get formatted update frequency code as frequency if set."""
        maintenance = Maintenance(RecordMaintenance(maintenance_frequency=frequency))
        assert maintenance.frequency == expected


class TestPageHeader:
    """Test Catalogue Item page header."""

    def test_init(self):
        """Can create a page header element."""
        expected_title = "x"
        title = f"<p>{expected_title}</p>"
        type_ = HierarchyLevelCode.PAPER_MAP_PRODUCT
        expected_type_label = ResourceTypeLabel[type_.name].value
        expected_type_icon = ResourceTypeIcon[type_.name].value

        header = PageHeader(title=title, item_type=type_)

        assert header.title == expected_title
        assert header.subtitle == (expected_type_label, expected_type_icon)


class TestPageSummary:
    """Test Catalogue Item summary panel."""

    @pytest.mark.parametrize(
        ("item_type", "edition", "published", "aggregations", "restricted", "citation"),
        [
            (
                HierarchyLevelCode.PRODUCT,
                "x",
                "x",
                Aggregations(
                    admin_meta_keys=_admin_meta_keys(),
                    aggregations=RecordAggregations(
                        [
                            Aggregation(
                                identifier=Identifier(identifier="x", href="x", namespace="x"),
                                association_type=AggregationAssociationCode.LARGER_WORK_CITATION,
                                initiative_type=AggregationInitiativeCode.COLLECTION,
                            )
                        ]
                    ),
                    select_record=_select_record,
                ),
                False,
                "x",
            ),
            (
                HierarchyLevelCode.PRODUCT,
                None,
                None,
                Aggregations(
                    admin_meta_keys=_admin_meta_keys(),
                    aggregations=RecordAggregations([]),
                    select_record=_select_record,
                ),
                True,
                None,
            ),
            (
                HierarchyLevelCode.COLLECTION,
                "x",
                "x",
                Aggregations(
                    admin_meta_keys=_admin_meta_keys(),
                    aggregations=RecordAggregations(
                        [
                            Aggregation(
                                identifier=Identifier(identifier="x", href="x", namespace="x"),
                                association_type=AggregationAssociationCode.IS_COMPOSED_OF,
                                initiative_type=AggregationInitiativeCode.COLLECTION,
                            )
                        ]
                    ),
                    select_record=_select_record,
                ),
                False,
                "x",
            ),
        ],
    )
    def test_init(
        self,
        item_type: HierarchyLevelCode,
        edition: str | None,
        published: str | None,
        aggregations: Aggregations,
        restricted: bool,
        citation: str | None,
    ):
        """Can create class for summary panel."""
        super_type = ItemSuperType.CONTAINER if item_type in CONTAINER_SUPER_TYPES else ItemSuperType.RESOURCE
        collections = [Link(value=summary.title_fmt, href=summary.href) for summary in aggregations.parent_collections]

        summary = PageSummary(
            item_super_type=super_type,
            edition=edition,
            published_date=published,
            revision_date=None,
            aggregations=aggregations,
            restricted=restricted,
            citation=citation,
            description="x",
        )
        assert summary.collections == collections
        assert summary.edition == edition
        assert summary.restricted == restricted
        assert summary.about == "x"

        if super_type == ItemSuperType.RESOURCE:
            assert summary.citation == citation
        else:
            assert summary.citation is None

    @pytest.mark.parametrize(
        ("edition", "published", "restricted", "aggregations", "expected"),
        [
            # [all triggers]
            (
                "1",
                "x",
                False,
                Aggregations(
                    admin_meta_keys=_admin_meta_keys(),
                    aggregations=RecordAggregations(
                        [
                            Aggregation(
                                identifier=Identifier(identifier="x", href="x", namespace="x"),
                                association_type=AggregationAssociationCode.LARGER_WORK_CITATION,
                                initiative_type=AggregationInitiativeCode.COLLECTION,
                            ),
                            Aggregation(
                                identifier=Identifier(identifier="x", href="x", namespace="x"),
                                association_type=AggregationAssociationCode.IS_COMPOSED_OF,
                                initiative_type=AggregationInitiativeCode.COLLECTION,
                            ),
                            Aggregation(
                                identifier=Identifier(identifier="x", href="x", namespace="x"),
                                association_type=AggregationAssociationCode.IS_COMPOSED_OF,
                                initiative_type=AggregationInitiativeCode.PROJECT,
                            ),
                        ]
                    ),
                    select_record=_select_record,
                ),
                True,
            ),
            # edition & collections
            (
                "1",
                None,
                False,
                Aggregations(
                    admin_meta_keys=_admin_meta_keys(),
                    aggregations=RecordAggregations(
                        [
                            Aggregation(
                                identifier=Identifier(identifier="x", href="x", namespace="x"),
                                association_type=AggregationAssociationCode.LARGER_WORK_CITATION,
                                initiative_type=AggregationInitiativeCode.COLLECTION,
                            )
                        ]
                    ),
                    select_record=_select_record,
                ),
                True,
            ),
            # published & projects
            (
                None,
                "x",
                False,
                Aggregations(
                    admin_meta_keys=_admin_meta_keys(),
                    aggregations=RecordAggregations(
                        [
                            Aggregation(
                                identifier=Identifier(identifier="x", href="x", namespace="x"),
                                association_type=AggregationAssociationCode.IS_COMPOSED_OF,
                                initiative_type=AggregationInitiativeCode.PROJECT,
                            )
                        ]
                    ),
                    select_record=_select_record,
                ),
                True,
            ),
            # [no triggers]
            (
                None,
                None,
                False,
                Aggregations(
                    admin_meta_keys=_admin_meta_keys(),
                    aggregations=RecordAggregations([]),
                    select_record=_select_record,
                ),
                False,
            ),
        ],
    )
    def test_grid_enabled(
        self, edition: str | None, published: str | None, restricted: bool, aggregations: Aggregations, expected: bool
    ):
        """Can determine whether to show item summary grid."""
        summary = PageSummary(
            item_super_type=ItemSuperType.RESOURCE,
            edition=edition,
            published_date=published,
            revision_date=None,
            restricted=restricted,
            aggregations=aggregations,
            citation=None,
            description="x",
        )

        assert summary.grid_enabled == expected

    @pytest.mark.parametrize(
        ("published", "revision", "expected"),
        [
            (None, None, None),
            (FormattedDate(datetime="x", value="x"), None, FormattedDate(datetime="x", value="x")),
            (None, "x", None),
            (
                FormattedDate(datetime="x", value="x"),
                FormattedDate(datetime="x", value="x"),
                FormattedDate(datetime="x", value="x"),
            ),
            (
                FormattedDate(datetime="x", value="x"),
                FormattedDate(datetime="y", value="y"),
                FormattedDate(datetime="x", value="x (last updated: y)"),
            ),
        ],
    )
    def test_published(
        self,
        fx_admin_meta_keys: AdministrationKeys,
        published: FormattedDate | None,
        revision: FormattedDate | None,
        expected: str,
    ):
        """Can show combination of publication and revision date if relevant."""
        summary = PageSummary(
            item_super_type=ItemSuperType.RESOURCE,
            edition=None,
            published_date=published,
            revision_date=revision,
            restricted=False,
            aggregations=Aggregations(
                admin_meta_keys=fx_admin_meta_keys, aggregations=RecordAggregations([]), select_record=_select_record
            ),
            citation=None,
            description="x",
        )

        assert summary.published == expected

    @pytest.mark.parametrize("has_aggregation", [False, True])
    def test_physical_map(self, fx_admin_meta_keys: AdministrationKeys, has_aggregation: bool):
        """Can show combination of publication and revision date if relevant."""
        aggregations = []
        if has_aggregation:
            aggregations.append(
                Aggregation(
                    identifier=Identifier(identifier="x", href="x", namespace=CATALOGUE_NAMESPACE),
                    association_type=AggregationAssociationCode.LARGER_WORK_CITATION,
                    initiative_type=AggregationInitiativeCode.PAPER_MAP,
                )
            )
        summary = PageSummary(
            item_super_type=ItemSuperType.RESOURCE,
            aggregations=Aggregations(
                admin_meta_keys=fx_admin_meta_keys,
                aggregations=RecordAggregations(aggregations),
                select_record=_select_record,
            ),
            restricted=False,
            edition=None,
            published_date=None,
            revision_date=None,
            citation=None,
            description="x",
        )

        physical_parent = summary.physical_parent

        if has_aggregation:
            assert physical_parent == Link(value="x", href="/items/x/", external=False)
        if not has_aggregation:
            assert physical_parent is None
