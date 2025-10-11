from datetime import UTC, datetime

import pytest

from lantern.lib.metadata_library.models.record.elements.common import (
    Address,
    Citation,
    ContactIdentity,
    Date,
    Identifier,
    OnlineResource,
    Series,
)
from lantern.lib.metadata_library.models.record.elements.common import Contact as RecordContact
from lantern.lib.metadata_library.models.record.elements.common import Dates as RecordDates
from lantern.lib.metadata_library.models.record.elements.common import Identifiers as RecordIdentifiers
from lantern.lib.metadata_library.models.record.elements.data_quality import DomainConsistency
from lantern.lib.metadata_library.models.record.elements.distribution import Distribution as RecordDistribution
from lantern.lib.metadata_library.models.record.elements.distribution import Format, TransferOption
from lantern.lib.metadata_library.models.record.elements.identification import (
    Aggregation,
    BoundingBox,
    Constraint,
    ExtentGeographic,
)
from lantern.lib.metadata_library.models.record.elements.identification import Aggregations as RecordAggregations
from lantern.lib.metadata_library.models.record.elements.identification import Extent as RecordExtent
from lantern.lib.metadata_library.models.record.elements.identification import Maintenance as RecordMaintenance
from lantern.lib.metadata_library.models.record.elements.metadata import MetadataStandard
from lantern.lib.metadata_library.models.record.enums import (
    AggregationAssociationCode,
    AggregationInitiativeCode,
    ConstraintRestrictionCode,
    ConstraintTypeCode,
    ContactRoleCode,
    HierarchyLevelCode,
    MaintenanceFrequencyCode,
    OnlineResourceFunctionCode,
    ProgressCode,
)
from lantern.models.item.base.elements import Contact, Contacts, Link
from lantern.models.item.base.elements import Extent as ItemExtent
from lantern.models.item.base.enums import AccessLevel, ResourceTypeLabel
from lantern.models.item.catalogue.distributions import ArcGisFeatureLayer
from lantern.models.item.catalogue.elements import (
    Aggregations,
    Dates,
    Extent,
    FormattedDate,
    Identifiers,
    ItemCatalogueSummary,
    Maintenance,
)
from lantern.models.item.catalogue.enums import Licence
from lantern.models.item.catalogue.tabs import (
    AdditionalInfoTab,
    AuthorsTab,
    ContactTab,
    DataTab,
    ExtentTab,
    InvalidItemContactError,
    ItemsTab,
    LicenceTab,
    LineageTab,
    RelatedTab,
)
from lantern.models.record.const import CATALOGUE_NAMESPACE
from tests.conftest import _get_record


class TestItemsTab:
    """Test items tab."""

    def test_init(self):
        """Can create items tab."""
        aggregations = Aggregations(
            aggregations=RecordAggregations(
                [
                    Aggregation(
                        identifier=Identifier(identifier="x", href="x", namespace=CATALOGUE_NAMESPACE),
                        association_type=AggregationAssociationCode.IS_COMPOSED_OF,
                        initiative_type=AggregationInitiativeCode.COLLECTION,
                    )
                ]
            ),
            get_record=_get_record,
        )

        tab = ItemsTab(aggregations=aggregations)

        assert tab.enabled is True
        assert len(tab.items) == 1
        # cov
        assert tab.title != ""
        assert tab.icon != ""


class TestDataTab:
    """Test data tab."""

    def test_init(self):
        """Can create data tab."""
        distributions = [
            RecordDistribution(
                distributor=RecordContact(organisation=ContactIdentity(name="x"), role={ContactRoleCode.DISTRIBUTOR}),
                transfer_option=TransferOption(
                    online_resource=OnlineResource(href="x", function=OnlineResourceFunctionCode.DOWNLOAD)
                ),
            )
        ]

        tab = DataTab(access_level=AccessLevel.PUBLIC, distributions=distributions)

        assert tab.enabled is False
        # cov
        assert tab.title != ""
        assert tab.icon != ""

    def test_enable(self):
        """Can enable data tab with supported distribution options."""
        distributions = [
            RecordDistribution(
                distributor=RecordContact(organisation=ContactIdentity(name="x"), role={ContactRoleCode.DISTRIBUTOR}),
                format=Format(
                    format="x",
                    href="https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+layer+feature",
                ),
                transfer_option=TransferOption(
                    online_resource=OnlineResource(href="x", function=OnlineResourceFunctionCode.DOWNLOAD)
                ),
            ),
            RecordDistribution(
                distributor=RecordContact(organisation=ContactIdentity(name="x"), role={ContactRoleCode.DISTRIBUTOR}),
                format=Format(
                    format="x",
                    href="https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+service+feature",
                ),
                transfer_option=TransferOption(
                    online_resource=OnlineResource(href="x", function=OnlineResourceFunctionCode.DOWNLOAD)
                ),
            ),
        ]
        tab = DataTab(access_level=AccessLevel.PUBLIC, distributions=distributions)
        assert tab.enabled is True

    def test_items(self):
        """Can get processed distribution options."""
        access_type = AccessLevel.PUBLIC
        distributions = [
            RecordDistribution(
                distributor=RecordContact(organisation=ContactIdentity(name="x"), role={ContactRoleCode.DISTRIBUTOR}),
                format=Format(
                    format="x",
                    href="https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+layer+feature",
                ),
                transfer_option=TransferOption(
                    online_resource=OnlineResource(href="x", function=OnlineResourceFunctionCode.DOWNLOAD)
                ),
            ),
            RecordDistribution(
                distributor=RecordContact(organisation=ContactIdentity(name="x"), role={ContactRoleCode.DISTRIBUTOR}),
                format=Format(
                    format="x",
                    href="https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+service+feature",
                ),
                transfer_option=TransferOption(
                    online_resource=OnlineResource(href="x", function=OnlineResourceFunctionCode.DOWNLOAD)
                ),
            ),
        ]
        expected = ArcGisFeatureLayer(distributions[0], [distributions[1]], access_type=access_type)
        tab = DataTab(access_level=access_type, distributions=distributions)

        assert tab.items[0].format_type == expected.format_type
        assert tab.items[0].action.href == expected.action.href

    def test_access(self):
        """Can get item access type."""
        expected = AccessLevel.PUBLIC
        tab = DataTab(access_level=expected, distributions=[])
        assert tab.access == expected


class TestExtentTab:
    """Test extent tab."""

    def test_init(self):
        """Can create extent tab."""
        extent = Extent(
            extent=ItemExtent(
                RecordExtent(
                    identifier="bounding",
                    geographic=ExtentGeographic(
                        bounding_box=BoundingBox(
                            west_longitude=1.0, east_longitude=1.0, south_latitude=1.0, north_latitude=1.0
                        )
                    ),
                )
            ),
            embedded_maps_endpoint="x",
        )

        tab = ExtentTab(extent=extent)

        assert tab.enabled is True
        assert tab.bounding_box == extent.bounding_box
        # cov
        assert str(tab) != ""  # to test __getattribute__ conditional logic
        assert tab.title != ""
        assert tab.icon != ""

    def test_none(self):
        """Can create extent tab without an extent."""
        tab = ExtentTab(extent=None)

        assert tab.enabled is False


class TestAuthorsTab:
    """Test authors tab."""

    def test_init(self):
        """Can create authors tab."""
        contacts = Contacts(
            [Contact(RecordContact(organisation=ContactIdentity(name="x"), role={ContactRoleCode.AUTHOR}))]
        )

        tab = AuthorsTab(item_type=HierarchyLevelCode.PRODUCT, authors=contacts)

        assert tab.enabled is True
        assert tab.items == contacts
        # cov
        assert tab.title != ""
        assert tab.icon != ""

    @pytest.mark.parametrize(
        ("item_type", "has_authors", "expected"),
        [
            (HierarchyLevelCode.PRODUCT, True, True),
            (HierarchyLevelCode.PRODUCT, False, False),
            (HierarchyLevelCode.COLLECTION, True, False),
        ],
    )
    def test_disabled(self, item_type: HierarchyLevelCode, has_authors: bool, expected: bool):
        """Can disable authors tab based on item type and if item has any authors."""
        contact = Contact(RecordContact(organisation=ContactIdentity(name="x"), role={ContactRoleCode.AUTHOR}))
        contacts = Contacts([])
        if has_authors:
            contacts.append(contact)

        tab = AuthorsTab(item_type=item_type, authors=contacts)

        assert tab.enabled == expected


class TestLicenceTab:
    """Test licence tab."""

    def test_init(self):
        """Can create licence tab."""
        constraint = Constraint(
            type=ConstraintTypeCode.USAGE,
            restriction_code=ConstraintRestrictionCode.LICENSE,
            href="https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/",
            statement="x",
        )
        tab = LicenceTab(item_type=HierarchyLevelCode.PRODUCT, licence=constraint)

        assert tab.enabled is True
        # cov
        assert tab.title != ""
        assert tab.icon != ""

    @pytest.mark.parametrize(
        ("item_type", "has_licence", "expected"),
        [
            (HierarchyLevelCode.PRODUCT, True, True),
            (HierarchyLevelCode.PRODUCT, False, False),
            (HierarchyLevelCode.COLLECTION, True, False),
        ],
    )
    def test_disabled(self, item_type: HierarchyLevelCode, has_licence: bool, expected: bool):
        """Can disable licence tab based on item type and if item has a licence."""
        constraint = Constraint(
            type=ConstraintTypeCode.USAGE,
            restriction_code=ConstraintRestrictionCode.LICENSE,
            href="https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/",
            statement="x",
        )
        licence = constraint if has_licence else None

        tab = LicenceTab(item_type=item_type, licence=licence)

        assert tab.enabled == expected
        if has_licence:
            assert isinstance(tab.slug, Licence)
        else:
            assert tab.slug is None

    @pytest.mark.parametrize(
        ("licence", "href", "expected"),
        [
            (False, None, None),
            (True, None, None),
            (True, "x", None),
            (True, Licence.OGL_UK_3_0.value, Licence.OGL_UK_3_0),
        ],
    )
    def test_slug(self, licence: bool, href: str | None, expected: Licence | None):
        """Can get licence macro name from licence constraint href if set."""
        constraint = Constraint(
            type=ConstraintTypeCode.USAGE,
            restriction_code=ConstraintRestrictionCode.LICENSE,
            href=href,
            statement="x",
        )
        if not licence:
            constraint = None

        tab = LicenceTab(item_type=HierarchyLevelCode.PRODUCT, licence=constraint)

        assert tab.slug == expected

    @pytest.mark.parametrize(
        ("contacts", "expected"),
        [
            (Contacts([]), []),
            (
                Contacts(
                    [
                        Contact(
                            RecordContact(organisation=ContactIdentity(name="x"), role={ContactRoleCode.RIGHTS_HOLDER})
                        ),
                        Contact(
                            RecordContact(individual=ContactIdentity(name="y"), role={ContactRoleCode.RIGHTS_HOLDER})
                        ),
                    ]
                ),
                ["x", "y"],
            ),
            (
                Contacts(
                    [
                        Contact(
                            RecordContact(
                                organisation=ContactIdentity(name="x"),
                                online_resource=OnlineResource(
                                    href="x",
                                    function=OnlineResourceFunctionCode.INFORMATION,
                                ),
                                role={ContactRoleCode.RIGHTS_HOLDER},
                            ),
                        ),
                        Contact(
                            RecordContact(
                                individual=ContactIdentity(name="y"),
                                online_resource=OnlineResource(
                                    href="y",
                                    function=OnlineResourceFunctionCode.INFORMATION,
                                ),
                                role={ContactRoleCode.RIGHTS_HOLDER},
                            ),
                        ),
                    ]
                ),
                [Link(value="x", href="x", external=True), Link(value="y", href="y", external=True)],
            ),
        ],
    )
    def test_copyright_holders(self, contacts: Contacts, expected: list[Link, str]):
        """Can get licence macro name from licence constraint href."""
        tab = LicenceTab(item_type=HierarchyLevelCode.PRODUCT, licence=None, rights_holders=contacts)
        assert tab.copyright_holders == expected


class TestLineageTab:
    """Test lineage tab."""

    def test_init(self):
        """Can create lineage tab."""
        expected = "x"

        tab = LineageTab(statement=expected)

        assert tab.enabled is True
        assert tab.statement == expected
        # cov
        assert tab.title != ""
        assert tab.icon != ""


class TestRelatedTab:
    """Test related tab."""

    def test_init(self):
        """Can create related tab."""
        aggregations = Aggregations(
            aggregations=RecordAggregations(
                [
                    Aggregation(
                        identifier=Identifier(identifier="x", href="x", namespace=CATALOGUE_NAMESPACE),
                        association_type=AggregationAssociationCode.LARGER_WORK_CITATION,
                        initiative_type=AggregationInitiativeCode.COLLECTION,
                    )
                ]
            ),
            get_record=_get_record,
        )

        tab = RelatedTab(aggregations=aggregations, item_type=HierarchyLevelCode.PRODUCT)

        assert tab.enabled is True
        assert len(tab.parent_collections) > 0
        assert all(isinstance(collection, ItemCatalogueSummary) for collection in tab.parent_collections)
        # cov
        assert tab.title != ""
        assert tab.icon != ""

    @pytest.mark.parametrize(
        ("level", "value", "expected"),
        [
            (HierarchyLevelCode.DATASET, RecordAggregations([]), False),
            (
                HierarchyLevelCode.DATASET,
                RecordAggregations(
                    [
                        Aggregation(
                            identifier=Identifier(identifier="x", href="x", namespace=CATALOGUE_NAMESPACE),
                            association_type=AggregationAssociationCode.LARGER_WORK_CITATION,
                            initiative_type=AggregationInitiativeCode.COLLECTION,
                        )
                    ]
                ),
                True,
            ),
            (
                HierarchyLevelCode.COLLECTION,
                RecordAggregations(
                    [
                        Aggregation(
                            identifier=Identifier(identifier="x", href="x", namespace=CATALOGUE_NAMESPACE),
                            association_type=AggregationAssociationCode.IS_COMPOSED_OF,
                            initiative_type=AggregationInitiativeCode.COLLECTION,
                        )
                    ]
                ),
                False,
            ),
            (
                HierarchyLevelCode.COLLECTION,
                RecordAggregations(
                    [
                        Aggregation(
                            identifier=Identifier(identifier="x", href="x", namespace=CATALOGUE_NAMESPACE),
                            association_type=AggregationAssociationCode.CROSS_REFERENCE,
                            initiative_type=AggregationInitiativeCode.COLLECTION,
                        )
                    ]
                ),
                True,
            ),
        ],
    )
    def test_enabled(self, level: HierarchyLevelCode, value: RecordAggregations, expected: bool):
        """Can disable related tab if not applicable."""
        aggregations = Aggregations(aggregations=value, get_record=_get_record)
        tab = RelatedTab(aggregations=aggregations, item_type=level)
        assert tab.enabled is expected


class TestAdditionalInfoTab:
    """Test additional information tab."""

    def test_init(self):
        """Can create additional information tab."""
        item_id = "x"
        item_type = HierarchyLevelCode.PRODUCT
        identifiers = Identifiers(RecordIdentifiers([]))
        dates = Dates(dates=RecordDates(creation=Date(date=datetime(2014, 6, 30, 14, 30, second=45, tzinfo=UTC))))
        datestamp = datetime(2014, 6, 30, 14, 30, second=45, tzinfo=UTC).date()

        xml_href = f"/records/{item_id}.xml"
        html_href = f"/records/{item_id}.html"
        json_href = f"/records/{item_id}.json"

        tab = AdditionalInfoTab(
            item_id=item_id,
            item_type=item_type,
            identifiers=identifiers,
            dates=dates,
            datestamp=datestamp,
            kv={},
            revision=None,
        )

        assert tab.enabled is True
        assert tab.item_id == item_id
        assert tab.item_type == ResourceTypeLabel[item_type.name].value
        assert tab.item_type_icon == "fa-fw far fa-map"
        assert isinstance(tab.dates, dict)
        assert tab.datestamp == FormattedDate.from_rec_date(Date(date=datestamp))
        assert tab.record_link_xml.href == xml_href
        assert tab.record_link_html.href == html_href
        assert tab.record_link_json.href == json_href
        assert len(tab.record_links) == 3
        # cov
        assert tab.title != ""
        assert tab.icon != ""

    @pytest.mark.parametrize(("value", "expected"), [(None, None), (1, "1:1"), (1234567890, "1:1,234,567,890")])
    def test_format_scale(self, value: int | None, expected: str | None):
        """Can get descriptive series if set."""
        assert AdditionalInfoTab._format_scale(value) == expected

    @pytest.mark.parametrize(
        ("series", "expected"), [(Series(name=None), None), (Series(name="x", page="y", edition="z"), "x")]
    )
    def test_series_name(
        self, fx_item_cat_info_tab_minimal: AdditionalInfoTab, series: Series | None, expected: str | None
    ):
        """Can get descriptive series name if set."""
        fx_item_cat_info_tab_minimal._series = series
        assert fx_item_cat_info_tab_minimal.series_name == expected

    @pytest.mark.parametrize(
        ("series", "expected"), [(Series(name=None), None), (Series(name="x", page="y", edition="z"), "y")]
    )
    def test_sheet_number(
        self, fx_item_cat_info_tab_minimal: AdditionalInfoTab, series: Series | None, expected: str | None
    ):
        """Can get descriptive series sheet number if set."""
        fx_item_cat_info_tab_minimal._series = series
        assert fx_item_cat_info_tab_minimal.sheet_number == expected

    def test_scale(self, fx_item_cat_info_tab_minimal: AdditionalInfoTab):
        """Can get scale if set."""
        fx_item_cat_info_tab_minimal._scale = 2
        assert fx_item_cat_info_tab_minimal.scale == "1:2"

    @pytest.mark.parametrize(
        ("identifier", "expected"),
        [
            (None, None),
            (
                Identifier(
                    identifier="EPSG:4326",
                    href="http://www.opengis.net/def/crs/EPSG/0/4326",
                    namespace="epsg",
                ),
                Link(
                    value="EPSG:4326",
                    href="https://spatialreference.org/ref/epsg/4326/",
                    external=True,
                ),
            ),
        ],
    )
    def test_projection(
        self, fx_item_cat_info_tab_minimal: AdditionalInfoTab, identifier: Identifier | None, expected: Link | None
    ):
        """Can get projection code if set."""
        fx_item_cat_info_tab_minimal._projection = identifier
        assert fx_item_cat_info_tab_minimal.projection == expected

    @pytest.mark.parametrize(
        ("kv", "expected"),
        [
            ({"physical_size_width_mm": 1}, None),
            ({"physical_size_height_mm": 1}, None),
            ({"physical_size_width_mm": 1, "physical_size_height_mm": 1}, "1 x 1 mm (width x height)"),
            ({"physical_size_width_mm": 210, "physical_size_height_mm": 297}, "A4 Portrait"),
            ({"physical_size_width_mm": 297, "physical_size_height_mm": 210}, "A4 Landscape"),
            ({"physical_size_width_mm": 420, "physical_size_height_mm": 594}, "A3 Portrait"),
            ({"physical_size_width_mm": 594, "physical_size_height_mm": 420}, "A3 Landscape"),
        ],
    )
    def test_page_size(self, fx_item_cat_info_tab_minimal: AdditionalInfoTab, kv: dict | None, expected: str | None):
        """Can get page size if set."""
        fx_item_cat_info_tab_minimal._kv = kv
        assert fx_item_cat_info_tab_minimal.page_size == expected

    @pytest.mark.parametrize(
        ("identifiers", "expected"),
        [
            (RecordIdentifiers([]), []),
            (
                RecordIdentifiers(
                    [
                        Identifier(
                            identifier="10.123/30825673-6276-4e5a-8a97-f97f2094cd25",
                            href="https://doi.org/10.123/30825673-6276-4e5a-8a97-f97f2094cd25",
                            namespace="doi",
                        )
                    ]
                ),
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
    def test_doi(
        self, fx_item_cat_info_tab_minimal: AdditionalInfoTab, identifiers: RecordIdentifiers, expected: list[Link]
    ):
        """Can get any DOIs if set."""
        fx_item_cat_info_tab_minimal._identifiers = Identifiers(identifiers)
        assert fx_item_cat_info_tab_minimal.doi == expected

    @pytest.mark.parametrize(
        ("identifiers", "expected"),
        [
            (RecordIdentifiers([]), []),
            (RecordIdentifiers([Identifier(identifier="978-0-85665-230-1", namespace="isbn")]), ["978-0-85665-230-1"]),
        ],
    )
    def test_isbn(
        self, fx_item_cat_info_tab_minimal: AdditionalInfoTab, identifiers: RecordIdentifiers, expected: list[str]
    ):
        """Can get any ISBNs if set."""
        fx_item_cat_info_tab_minimal._identifiers = Identifiers(identifiers)
        assert fx_item_cat_info_tab_minimal.isbn == expected

    @pytest.mark.parametrize(
        ("identifiers", "expected"),
        [
            (RecordIdentifiers([]), []),
            (
                RecordIdentifiers(
                    [
                        Identifier(
                            identifier="https://gitlab.data.bas.ac.uk/MAGIC/foo/-/issues/123",
                            href="https://gitlab.data.bas.ac.uk/MAGIC/foo/-/issues/123",
                            namespace="gitlab.data.bas.ac.uk",
                        )
                    ]
                ),
                ["MAGIC/foo#123"],
            ),
        ],
    )
    def test_gitlab_issues(
        self, fx_item_cat_info_tab_minimal: AdditionalInfoTab, identifiers: RecordIdentifiers, expected: list[str]
    ):
        """Can get any resource GitLab issue references if set."""
        fx_item_cat_info_tab_minimal._identifiers = Identifiers(identifiers)
        assert fx_item_cat_info_tab_minimal.gitlab_issues == expected

    @pytest.mark.parametrize(
        ("maintenance", "expected_progress", "expected_frequency"),
        [
            (None, None, None),
            (
                Maintenance(RecordMaintenance(progress=ProgressCode.HISTORICAL_ARCHIVE)),
                "Item has been archived and may be outdated",
                None,
            ),
            (
                Maintenance(RecordMaintenance(maintenance_frequency=MaintenanceFrequencyCode.IRREGULAR)),
                None,
                "Item is updated irregularly",
            ),
        ],
    )
    def test_maintenance(
        self,
        fx_item_cat_info_tab_minimal: AdditionalInfoTab,
        maintenance: Maintenance,
        expected_progress: str | None,
        expected_frequency: str | None,
    ):
        """Can get resource maintenance progress and update frequency if set."""
        fx_item_cat_info_tab_minimal._maintenance = maintenance
        assert fx_item_cat_info_tab_minimal.status == expected_progress
        assert fx_item_cat_info_tab_minimal.frequency == expected_frequency

    @pytest.mark.parametrize(
        ("standard", "expected_standard", "expected_version"),
        [
            (None, None, None),
            (
                MetadataStandard(),
                "ISO 19115-2 Geographic Information - Metadata - Part 2: Extensions for Imagery and Gridded Data",
                "ISO 19115-2:2009(E)",
            ),
        ],
    )
    def test_standard(
        self,
        fx_item_cat_info_tab_minimal: AdditionalInfoTab,
        standard: MetadataStandard,
        expected_standard: str | None,
        expected_version: str | None,
    ):
        """Can get metadata standard and standard version if set."""
        fx_item_cat_info_tab_minimal._standard = standard
        assert fx_item_cat_info_tab_minimal.standard == expected_standard
        assert fx_item_cat_info_tab_minimal.standard_version == expected_version

    @pytest.mark.parametrize(
        ("profiles", "expected"),
        [
            ([], []),
            (
                [
                    DomainConsistency(
                        specification=Citation(
                            title="x",
                            dates=RecordDates(creation=Date(date=datetime(2014, 6, 30, tzinfo=UTC))),
                            href="x",
                        ),
                        explanation="x",
                        result=True,
                    )
                ],
                [Link(value="x", href="x", external=True)],
            ),
        ],
    )
    def test_profiles(
        self,
        fx_item_cat_info_tab_minimal: AdditionalInfoTab,
        profiles: list[DomainConsistency],
        expected: list[Link],
    ):
        """Can get any data quality profiles if set."""
        fx_item_cat_info_tab_minimal._profiles = profiles
        assert fx_item_cat_info_tab_minimal.profiles == expected

    @pytest.mark.parametrize("expected", [None, Link(value="x", href="x", external=True)])
    def test_revision(self, fx_item_cat_info_tab_minimal: AdditionalInfoTab, expected: Link | None):
        """Can get item revision if set."""
        fx_item_cat_info_tab_minimal._revision = expected
        assert fx_item_cat_info_tab_minimal.revision_link == expected


class TestContactTab:
    """Test contact tab."""

    def test_init(self):
        """Can create contact tab."""
        expected = "x"
        contact = Contact(
            RecordContact(
                organisation=ContactIdentity(name=expected), email=expected, role={ContactRoleCode.POINT_OF_CONTACT}
            )
        )

        tab = ContactTab(contact=contact, item_id=expected, item_title=expected, form_action="x", turnstile_key="x")

        assert tab.enabled is True
        assert tab.subject_default == f"Message about '{expected}'"
        assert tab.team == expected
        assert tab.email == expected
        # cov
        assert tab.title != ""
        assert tab.icon != ""

    @pytest.mark.parametrize(
        ("endpoint", "action", "params"),
        [
            ("x", "://x", {"item-id": "x", "item-poc": "x"}),
            ("https://example.com?x=x", "https://example.com", {"item-id": "x", "item-poc": "x", "x": "x"}),
        ],
    )
    def test_form(self, endpoint: str, action: str, params: dict[str, str]) -> None:
        """Can get contact form action and parameters."""
        contact = Contact(
            RecordContact(organisation=ContactIdentity(name="x"), email="x", role={ContactRoleCode.POINT_OF_CONTACT})
        )

        assert tab.form_action == action
        assert tab.form_params == params
        tab = ContactTab(contact=contact, item_id=item_id, item_title="x", form_action=endpoint, turnstile_key="x")

    @pytest.mark.parametrize("has_value", [True, False])
    def test_phone(self, has_value: bool):
        """Can get phone number if set."""
        expected = "x" if has_value else None
        contact = Contact(
            RecordContact(
                organisation=ContactIdentity(name="x"),
                email="x",
                phone=expected,
                role={ContactRoleCode.POINT_OF_CONTACT},
            )
        )

        tab = ContactTab(contact=contact, item_id="x", item_title="x", form_action="x", turnstile_key="x")
        assert tab.phone == expected

    @pytest.mark.parametrize("has_value", [True, False])
    def test_address(self, has_value: bool):
        """Can get address if set."""
        expected = "x<br/>y<br/>z<br/>a<br/>b<br/>c" if has_value else None
        address = (
            Address(delivery_point="x, y", city="z", administrative_area="a", postal_code="b", country="c")
            if has_value
            else None
        )
        contact = Contact(
            RecordContact(
                organisation=ContactIdentity(name="x"),
                email="x",
                address=address,
                role={ContactRoleCode.POINT_OF_CONTACT},
            )
        )

        tab = ContactTab(contact=contact, item_id="x", item_title="x", form_action="x", turnstile_key="x")
        assert tab.address == expected

    def test_no_team(self):
        """Can't create a contact tab without a Contact with an organisation name."""
        contact = Contact(
            RecordContact(individual=ContactIdentity(name="x"), email="x", role={ContactRoleCode.POINT_OF_CONTACT})
        )
        tab = ContactTab(contact=contact, item_id="x", item_title="x", form_action="x", turnstile_key="x")

        with pytest.raises(InvalidItemContactError):
            _ = tab.team

    def test_no_email(self):
        """Can't create a contact tab without a Contact with an organisation name."""
        contact = Contact(
            RecordContact(organisation=ContactIdentity(name="x"), role={ContactRoleCode.POINT_OF_CONTACT})
        )
        tab = ContactTab(contact=contact, item_id="x", item_title="x", form_action="x", turnstile_key="x")

        with pytest.raises(InvalidItemContactError):
            _ = tab.email
