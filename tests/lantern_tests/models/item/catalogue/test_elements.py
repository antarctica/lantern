from datetime import UTC, date, datetime

import pytest

from lantern.lib.metadata_library.models.record.elements.administration import Administration
from lantern.lib.metadata_library.models.record.elements.common import Date, Identifier
from lantern.lib.metadata_library.models.record.elements.common import Dates as RecordDates
from lantern.lib.metadata_library.models.record.elements.common import Identifiers as RecordIdentifiers
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
from lantern.lib.metadata_library.models.record.elements.identification import Maintenance as RecordMaintenance
from lantern.lib.metadata_library.models.record.enums import (
    AggregationAssociationCode,
    AggregationInitiativeCode,
    DatePrecisionCode,
    DateTypeCode,
    HierarchyLevelCode,
    MaintenanceFrequencyCode,
    ProgressCode,
)
from lantern.lib.metadata_library.models.record.presets.admin import OPEN_ACCESS
from lantern.lib.metadata_library.models.record.utils.admin import AdministrationKeys, set_admin
from lantern.models.item.base.elements import Extent as ItemExtent
from lantern.models.item.base.elements import Link
from lantern.models.item.base.enums import ResourceTypeLabel
from lantern.models.item.base.item import ItemBase
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
from lantern.models.item.catalogue.enums import ResourceTypeIcon
from lantern.models.record.const import ALIAS_NAMESPACE, CATALOGUE_NAMESPACE
from tests.conftest import _admin_meta_keys, _get_record


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
            # noinspection PyTypeChecker
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
        expected_record = _get_record("x")
        record_aggregations = RecordAggregations([expected_aggregation])

        aggregations = Aggregations(
            admin_meta_keys=fx_admin_meta_keys, aggregations=record_aggregations, get_record=_get_record
        )

        assert isinstance(aggregations, Aggregations)
        assert len(aggregations) == 1
        assert aggregations._aggregations[0] == expected_aggregation
        assert aggregations._summaries["x"]._record == expected_record

    def test_peer_collections(self, fx_admin_meta_keys: AdministrationKeys):
        """Can get any collection aggregations (item is part of)."""
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
            admin_meta_keys=fx_admin_meta_keys, aggregations=record_aggregations, get_record=_get_record
        )

        assert len(aggregations.peer_collections) > 0

    def test_peer_cross_reference(self, fx_admin_meta_keys: AdministrationKeys):
        """Can get any cross-reference not related to another context (e.g. collections)."""
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
            ]
        )
        aggregations = Aggregations(
            admin_meta_keys=fx_admin_meta_keys, aggregations=record_aggregations, get_record=_get_record
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
            admin_meta_keys=fx_admin_meta_keys, aggregations=record_aggregations, get_record=_get_record
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
            admin_meta_keys=fx_admin_meta_keys, aggregations=record_aggregations, get_record=_get_record
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
            admin_meta_keys=fx_admin_meta_keys, aggregations=record_aggregations, get_record=_get_record
        )

        assert len(aggregations.parent_collections) > 0

    def test_child_items(self, fx_admin_meta_keys: AdministrationKeys):
        """Can get any item aggregations (item is made up of)."""
        record_aggregations = RecordAggregations(
            [
                Aggregation(
                    identifier=Identifier(identifier="x", href="x", namespace=CATALOGUE_NAMESPACE),
                    association_type=AggregationAssociationCode.IS_COMPOSED_OF,
                    initiative_type=AggregationInitiativeCode.COLLECTION,
                )
            ]
        )
        aggregations = Aggregations(
            admin_meta_keys=fx_admin_meta_keys, aggregations=record_aggregations, get_record=_get_record
        )

        assert len(aggregations.child_items) > 0

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
            admin_meta_keys=fx_admin_meta_keys, aggregations=record_aggregations, get_record=_get_record
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
        expected = {"Item created": FormattedDate.from_rec_date(date_)}

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
        expected = f"https://example.com/?theme=bsk1&bbox={expected_bbox}&globe-overview"

        extent = Extent(extent=item_extent, embedded_maps_endpoint="https://example.com")
        assert extent.map_iframe == expected


class TestItemCatalogueSummaryCatalogue:
    """
    Test Catalogue Item summary.

    Used for showing summaries of other items.
    """

    def test_init(self, fx_item_base_model_min: ItemBase):
        """Can create an ItemCatalogueSummaryCatalogue."""
        summary = ItemCatalogueSummary(
            record=fx_item_base_model_min._record, admin_meta_keys=fx_item_base_model_min._admin_keys
        )

        assert isinstance(summary, ItemCatalogueSummary)
        assert summary._record == fx_item_base_model_min._record
        assert isinstance(summary._admin_keys, AdministrationKeys)

    def test_init_invalid_admin_keys(self, fx_item_base_model_min: ItemBase):
        """Cannot create an ItemCatalogueSummaryCatalogue if admin keys are not provided."""
        with pytest.raises(TypeError, match=r"administration metadata keys must be provided"):
            # noinspection PyTypeChecker
            _ = ItemCatalogueSummary(record=fx_item_base_model_min._record, admin_meta_keys=None)

    def test_resource_type_icon(self, fx_item_base_model_min: ItemBase):
        """Can get icon for resource type."""
        summary = ItemCatalogueSummary(
            record=fx_item_base_model_min._record, admin_meta_keys=fx_item_base_model_min._admin_keys
        )
        assert summary._resource_type_icon == ResourceTypeIcon[summary.resource_type.name].value

    @pytest.mark.parametrize(("value", "expected"), [(None, ""), ("x", "<p>x</p>"), ("_x_", "<p><em>x</em></p>")])
    def test_summary_html(self, fx_item_base_model_min: ItemBase, value: str, expected: str):
        """Can get summary with Markdown formatting encoded as HTML if present, or a blank string."""
        record = fx_item_base_model_min._record
        record.identification.purpose = value
        summary = ItemCatalogueSummary(record=record, admin_meta_keys=fx_item_base_model_min._admin_keys)

        assert summary.summary_html == expected

    @pytest.mark.parametrize("has_date", [True, False])
    def test_date(self, fx_item_base_model_min: ItemBase, has_date: bool):
        """Can get formatted publication date if set."""
        record = fx_item_base_model_min._record
        publication = Date(date=datetime(2014, 6, 30, tzinfo=UTC).date())
        expected = "30 June 2014" if has_date else None
        if has_date:
            record.identification.dates.publication = publication
        summary = ItemCatalogueSummary(record=record, admin_meta_keys=fx_item_base_model_min._admin_keys)
        if has_date:
            assert summary._date.value == expected
        else:
            assert summary._date is None

    @pytest.mark.parametrize(
        (
            "restricted",
            "resource_type",
            "edition",
            "exp_edition",
            "has_pub",
            "exp_published",
            "child_count",
            "exp_child_count",
        ),
        [
            (False, HierarchyLevelCode.PRODUCT, "x", "Ed. x", True, "30 June 2014", 0, None),
            (False, HierarchyLevelCode.PRODUCT, "x", "Ed. x", False, None, 0, None),
            (False, HierarchyLevelCode.PRODUCT, None, None, True, "30 June 2014", 0, None),
            (False, HierarchyLevelCode.PAPER_MAP_PRODUCT, None, None, True, "30 June 2014", 0, None),
            (False, HierarchyLevelCode.DATASET, "X", "vX", False, None, 0, None),
            (False, HierarchyLevelCode.COLLECTION, "x", None, True, None, 0, None),
            (False, HierarchyLevelCode.COLLECTION, "x", None, False, None, 0, None),
            (False, HierarchyLevelCode.COLLECTION, None, None, False, None, 0, None),
            (False, HierarchyLevelCode.COLLECTION, None, None, False, None, 1, "1 item"),
            (False, HierarchyLevelCode.COLLECTION, None, None, False, None, 2, "2 items"),
            (False, HierarchyLevelCode.PAPER_MAP_PRODUCT, None, None, False, None, 1, "1 side"),
            (False, HierarchyLevelCode.PAPER_MAP_PRODUCT, None, None, False, None, 2, "2 sides"),
            (True, HierarchyLevelCode.PRODUCT, None, None, False, None, 0, None),
        ],
    )
    def test_fragments(
        self,
        fx_item_base_model_min: ItemBase,
        restricted: bool,
        resource_type: HierarchyLevelCode,
        edition: str | None,
        exp_edition: str | None,
        has_pub: bool,
        exp_published: FormattedDate | None,
        child_count: int,
        exp_child_count: str | None,
    ):
        """Can get fragments to use as part of item summary UI."""
        record = fx_item_base_model_min._record
        if not restricted:
            admin_meta = Administration(id=record.file_identifier, access_permissions=[OPEN_ACCESS])
            set_admin(keys=fx_item_base_model_min._admin_keys, record=record, admin_meta=admin_meta)
        exp_resource_type = ResourceTypeLabel[resource_type.name]
        record.hierarchy_level = resource_type
        record.identification.edition = edition
        if has_pub:
            record.identification.dates.publication = Date(date=datetime(2014, 6, 30, tzinfo=UTC).date())
        for _ in range(child_count):
            aggregation = Aggregation(
                identifier=Identifier(identifier="x", namespace="x"),
                association_type=AggregationAssociationCode.IS_COMPOSED_OF,
                initiative_type=AggregationInitiativeCode.COLLECTION,
            )
            if resource_type.name == HierarchyLevelCode.PAPER_MAP_PRODUCT:
                aggregation = Aggregation(
                    identifier=Identifier(identifier="x", namespace="x"),
                    association_type=AggregationAssociationCode.IS_COMPOSED_OF,
                    initiative_type=AggregationInitiativeCode.PAPER_MAP,
                )
            record.identification.aggregations.append(aggregation)
        record.child_aggregations_count = child_count

        summary = ItemCatalogueSummary(record=record, admin_meta_keys=fx_item_base_model_min._admin_keys)
        result = summary.fragments

        assert result.restricted == restricted
        assert result.item_type == exp_resource_type.value
        assert result.edition == exp_edition
        if exp_published is not None:
            assert result.published.value == exp_published
        else:
            assert result.published is None
        assert result.children == exp_child_count

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
    def test_href_graphic(self, fx_item_base_model_min: ItemBase, href: str | None, expected: tuple[str, str]):
        """
        Can get href graphics.

        If present in a record the same image is returned twice as a light and dark image.
        """
        record = fx_item_base_model_min._record
        if href is not None:
            record.identification.graphic_overviews.append(
                GraphicOverview(identifier="overview", href=href, mime_type="x")
            )

        summary = ItemCatalogueSummary(record=record, admin_meta_keys=fx_item_base_model_min._admin_keys)

        if href is not None:
            assert summary.href_graphic == expected
        else:
            assert summary.href_graphic[0].startswith(expected[0])
            assert summary.href_graphic[1].startswith(expected[1])


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
                [Identifier(identifier="x/x", href="https://data.bas.ac.uk/x/x", namespace=ALIAS_NAMESPACE)],
                [Link(value="x/x", href="/x/x", external=False)],
            ),
        ],
    )
    def test_aliases(self, identifiers: list[Identifier], expected: list[str]):
        """Can get any aliases."""
        identifiers = Identifiers(RecordIdentifiers(identifiers))
        result = identifiers.aliases
        assert result == expected

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
                    get_record=_get_record,
                ),
                False,
                "x",
            ),
            (
                HierarchyLevelCode.PRODUCT,
                None,
                None,
                Aggregations(
                    admin_meta_keys=_admin_meta_keys(), aggregations=RecordAggregations([]), get_record=_get_record
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
                    get_record=_get_record,
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
        collections = [Link(value=summary.title_html, href=summary.href) for summary in aggregations.parent_collections]
        items_count = len(aggregations.child_items)

        summary = PageSummary(
            item_type=item_type,
            edition=edition,
            published_date=published,
            revision_date=None,
            aggregations=aggregations,
            restricted=restricted,
            citation=citation,
            abstract="x",
        )

        assert summary.abstract == "x"
        assert summary.collections == collections
        assert summary.items_count == items_count
        assert summary.restricted == restricted

        if item_type != HierarchyLevelCode.COLLECTION:
            assert summary.edition == edition
            assert summary.published == published
            assert summary.citation == citation
        else:
            assert summary.edition is None
            assert summary.published is None
            assert summary.citation is None

    @pytest.mark.parametrize(
        ("item_type", "edition", "published", "restricted", "aggregations", "expected"),
        [
            (
                HierarchyLevelCode.PRODUCT,
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
                        ]
                    ),
                    get_record=_get_record,
                ),
                True,
            ),
            (
                HierarchyLevelCode.PRODUCT,
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
                    get_record=_get_record,
                ),
                True,
            ),
            (
                HierarchyLevelCode.PRODUCT,
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
                                initiative_type=AggregationInitiativeCode.COLLECTION,
                            )
                        ]
                    ),
                    get_record=_get_record,
                ),
                True,
            ),
            (
                HierarchyLevelCode.PRODUCT,
                None,
                None,
                False,
                Aggregations(
                    admin_meta_keys=_admin_meta_keys(), aggregations=RecordAggregations([]), get_record=_get_record
                ),
                False,
            ),
            (
                HierarchyLevelCode.COLLECTION,
                "1",
                "x",
                False,
                Aggregations(
                    admin_meta_keys=_admin_meta_keys(), aggregations=RecordAggregations([]), get_record=_get_record
                ),
                False,
            ),
            (
                HierarchyLevelCode.COLLECTION,
                "1",
                "x",
                True,
                Aggregations(
                    admin_meta_keys=_admin_meta_keys(), aggregations=RecordAggregations([]), get_record=_get_record
                ),
                True,
            ),
        ],
    )
    def test_grid_enabled(
        self,
        item_type: HierarchyLevelCode,
        edition: str | None,
        published: str | None,
        restricted: bool,
        aggregations: Aggregations,
        expected: bool,
    ):
        """Can show combination of publication and revision date if relevant."""
        summary = PageSummary(
            item_type=item_type,
            edition=edition,
            published_date=published,
            revision_date=None,
            restricted=restricted,
            aggregations=aggregations,
            citation=None,
            abstract="x",
        )

        assert summary.grid_enabled == expected

    @pytest.mark.parametrize(
        ("item_type", "published", "revision", "expected"),
        [
            (HierarchyLevelCode.PRODUCT, None, None, None),
            (
                HierarchyLevelCode.PRODUCT,
                FormattedDate(datetime="x", value="x"),
                None,
                FormattedDate(datetime="x", value="x"),
            ),
            (HierarchyLevelCode.PRODUCT, None, "x", None),
            (
                HierarchyLevelCode.PRODUCT,
                FormattedDate(datetime="x", value="x"),
                FormattedDate(datetime="x", value="x"),
                FormattedDate(datetime="x", value="x"),
            ),
            (
                HierarchyLevelCode.PRODUCT,
                FormattedDate(datetime="x", value="x"),
                FormattedDate(datetime="y", value="y"),
                FormattedDate(datetime="x", value="x (last updated: y)"),
            ),
            (
                HierarchyLevelCode.COLLECTION,
                FormattedDate(datetime="x", value="x"),
                FormattedDate(datetime="y", value="y"),
                None,
            ),
        ],
    )
    def test_published(
        self,
        fx_admin_meta_keys: AdministrationKeys,
        item_type: HierarchyLevelCode,
        published: FormattedDate | None,
        revision: FormattedDate | None,
        expected: str,
    ):
        """Can show combination of publication and revision date if relevant."""
        summary = PageSummary(
            item_type=item_type,
            edition=None,
            published_date=published,
            revision_date=revision,
            restricted=False,
            aggregations=Aggregations(
                admin_meta_keys=fx_admin_meta_keys, aggregations=RecordAggregations([]), get_record=_get_record
            ),
            citation=None,
            abstract="x",
        )

        assert summary.published == expected

    @pytest.mark.parametrize(
        ("item_type", "has_aggregation"),
        [(HierarchyLevelCode.PRODUCT, False), (HierarchyLevelCode.PRODUCT, True)],
    )
    def test_physical_map(
        self, fx_admin_meta_keys: AdministrationKeys, item_type: HierarchyLevelCode, has_aggregation: bool
    ):
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
            item_type=item_type,
            aggregations=Aggregations(
                admin_meta_keys=fx_admin_meta_keys,
                aggregations=RecordAggregations(aggregations),
                get_record=_get_record,
            ),
            restricted=False,
            edition=None,
            published_date=None,
            revision_date=None,
            citation=None,
            abstract="x",
        )

        physical_parent = summary.physical_parent

        if has_aggregation:
            assert physical_parent == Link(value="<p>x</p>", href="/items/x/", external=False)
        if not has_aggregation:
            assert physical_parent is None
