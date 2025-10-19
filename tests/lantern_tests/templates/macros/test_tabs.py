import json
from copy import deepcopy
from datetime import date
from unittest.mock import PropertyMock

import pytest
from bs4 import BeautifulSoup
from pytest_mock import MockerFixture

from lantern.lib.metadata_library.models.record.elements.administration import Permission
from lantern.lib.metadata_library.models.record.elements.common import (
    Address,
    Citation,
    Contact,
    ContactIdentity,
    Contacts,
    Date,
    Dates,
    Identifier,
    OnlineResource,
    Series,
)
from lantern.lib.metadata_library.models.record.elements.data_quality import DataQuality, DomainConsistency, Lineage
from lantern.lib.metadata_library.models.record.elements.distribution import Distribution, Format, Size, TransferOption
from lantern.lib.metadata_library.models.record.elements.identification import (
    Aggregation,
    Aggregations,
    BoundingBox,
    Constraint,
    Constraints,
    Extent,
    ExtentGeographic,
    Extents,
    ExtentTemporal,
    Maintenance,
    TemporalPeriod,
)
from lantern.lib.metadata_library.models.record.elements.projection import Code, ReferenceSystemInfo
from lantern.lib.metadata_library.models.record.enums import (
    AggregationAssociationCode,
    AggregationInitiativeCode,
    ConstraintRestrictionCode,
    ConstraintTypeCode,
    ContactRoleCode,
    MaintenanceFrequencyCode,
    OnlineResourceFunctionCode,
    ProgressCode,
)
from lantern.lib.metadata_library.models.record.presets.admin import OPEN_ACCESS
from lantern.lib.metadata_library.models.record.utils.admin import AdministrationKeys, get_admin, set_admin
from lantern.models.item.base.enums import AccessLevel
from lantern.models.item.catalogue.enums import Licence
from lantern.models.item.catalogue.item import ItemCatalogue
from lantern.models.item.catalogue.special.physical_map import ItemCataloguePhysicalMap
from lantern.models.record.const import ALIAS_NAMESPACE, CATALOGUE_NAMESPACE
from lantern.models.record.revision import RecordRevision
from tests.conftest import _get_record, render_item_catalogue


class TestItemsTab:
    """Test items tab template macros."""

    @pytest.mark.parametrize(
        "value",
        [
            Aggregations([]),
            Aggregations(
                [
                    Aggregation(
                        identifier=Identifier(identifier="x", href="x", namespace="x"),
                        association_type=AggregationAssociationCode.IS_COMPOSED_OF,
                        initiative_type=AggregationInitiativeCode.COLLECTION,
                    )
                ]
            ),
        ],
    )
    def test_enabled(self, fx_item_cat_model_min: ItemCatalogue, value: Aggregations):
        """Can get items tab if enabled in item."""
        fx_item_cat_model_min._record.identification.aggregations = value
        expected = fx_item_cat_model_min._items.enabled
        html = BeautifulSoup(render_item_catalogue(fx_item_cat_model_min), parser="html.parser", features="lxml")

        if expected:
            assert html.select_one("#tab-content-items") is not None
        else:
            assert html.select_one("#tab-content-items") is None

    def test_items(self, fx_item_cat_model_min: ItemCatalogue):
        """
        Can get item summaries with expected values from item.

        Detailed item summary tests are run in common macro tests.
        """
        items = Aggregations(
            [
                Aggregation(
                    identifier=Identifier(identifier="x", href="x", namespace="x"),
                    association_type=AggregationAssociationCode.IS_COMPOSED_OF,
                    initiative_type=AggregationInitiativeCode.COLLECTION,
                ),
                Aggregation(
                    identifier=Identifier(identifier="y", href="x", namespace="y"),
                    association_type=AggregationAssociationCode.IS_COMPOSED_OF,
                    initiative_type=AggregationInitiativeCode.COLLECTION,
                ),
            ]
        )
        fx_item_cat_model_min._record.identification.aggregations = items
        expected = fx_item_cat_model_min._items.items
        html = BeautifulSoup(render_item_catalogue(fx_item_cat_model_min), parser="html.parser", features="lxml")

        for item in expected:
            assert html.select_one(f"a[href='{item.href}']") is not None


class TestDataTab:
    """Test data tab template macros."""

    @pytest.mark.parametrize(
        "value",
        [
            [],
            [
                Distribution(
                    distributor=Contact(organisation=ContactIdentity(name="x"), role={ContactRoleCode.DISTRIBUTOR}),
                    transfer_option=TransferOption(
                        online_resource=OnlineResource(href="x", function=OnlineResourceFunctionCode.DOWNLOAD)
                    ),
                )
            ],
        ],
    )
    def test_enabled(self, fx_item_cat_model_min: ItemCatalogue, value: list[Distribution]):
        """Can get data tab if enabled in item."""
        fx_item_cat_model_min._record.distribution = value
        expected = fx_item_cat_model_min._data.enabled
        html = BeautifulSoup(render_item_catalogue(fx_item_cat_model_min), parser="html.parser", features="lxml")

        if expected:
            assert html.select_one("#tab-content-data") is not None
        else:
            assert html.select_one("#tab-content-data") is None

    def test_data_download(self, fx_item_cat_model_min: ItemCatalogue):
        """Can get individual data elements for download distributions based on values from item."""
        fx_item_cat_model_min._record.distribution = [
            Distribution(
                distributor=Contact(organisation=ContactIdentity(name="x"), role={ContactRoleCode.DISTRIBUTOR}),
                format=Format(format="x", href="https://www.iana.org/assignments/media-types/image/png"),
                transfer_option=TransferOption(
                    size=Size(unit="bytes", magnitude=1024),
                    online_resource=OnlineResource(href="x", function=OnlineResourceFunctionCode.DOWNLOAD),
                ),
            )
        ]
        expected = fx_item_cat_model_min._data.items[0]
        html = BeautifulSoup(render_item_catalogue(fx_item_cat_model_min), parser="html.parser", features="lxml")

        assert html.select_one(f"a[href='{expected.action.href}']") is not None
        # noinspection PyTypeChecker
        assert html.find(name="span", string=expected.format_type.value) is not None
        # noinspection PyTypeChecker
        assert html.find(name="div", string=expected.size) is not None

    @pytest.mark.parametrize("value", [None, "x"])
    def test_data_description(self, fx_item_cat_model_min: ItemCatalogue, value: str | None):
        """Can get optional data descriptions based on values from item."""
        fx_item_cat_model_min._record.distribution = [
            Distribution(
                distributor=Contact(organisation=ContactIdentity(name="x"), role={ContactRoleCode.DISTRIBUTOR}),
                format=Format(format="x", href="https://www.iana.org/assignments/media-types/image/png"),
                transfer_option=TransferOption(
                    size=Size(unit="bytes", magnitude=1024),
                    online_resource=OnlineResource(
                        href="x", description=value, function=OnlineResourceFunctionCode.DOWNLOAD
                    ),
                ),
            )
        ]
        html = BeautifulSoup(render_item_catalogue(fx_item_cat_model_min), parser="html.parser", features="lxml")

        result = html.find(name="aside", string=value)
        assert result is not None

    @pytest.mark.parametrize(
        ("value", "text"),
        [
            (
                [
                    "https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+layer+feature",
                    "https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+service+feature",
                ],
                "ArcGIS Feature Services",
            ),
            (
                [
                    "https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+layer+feature+ogc",
                    "https://metadata-resources.data.bas.ac.uk/media-types/x-service/ogc+api+feature",
                ],
                "(as implemented by ArcGIS Server)",
            ),
            (
                ["https://www.bas.ac.uk/data/our-data/maps/how-to-order-a-map/"],
                "This item is available to purchase as a physical paper map",
            ),
            (
                [
                    "https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+layer+tile+raster",
                    "https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+service+tile+raster",
                ],
                "ArcGIS Raster (Map) Tiles",
            ),
            (
                [
                    "https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+layer+tile+vector",
                    "https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+service+tile+vector",
                ],
                "ArcGIS Vector Tiles",
            ),
        ],
    )
    def test_data_info(self, fx_item_cat_model_min: ItemCatalogue, value: list[str], text: str):
        """
        Can get matching data access template based on values from item.

        Checking these templates is tricky:
        - templates vary significantly and don't contain any single common/predictable value to check against
        - templates do not contain a value we can use as a boundary to search within
        - templates could repeat if multiple distribution options of the same type are defined

        This test is therefore a best efforts attempt, checking for a freetext value. anywhere in the item template.
        Using a single distribution option set, with an otherwise minimal item, to hopefully limit irrelevant content.

        This value will always appear twice in rendered content, as we include a <noscript> version for gracefully
        handling JavaScript disabled browsers. Text should therefore be in the collapsible section, and the <noscript>.

        Note: This test does not check the contents of the rendered template, except for the freetext value. For
        example, it doesn't verify a service endpoint (if used) is populated correctly.
        """
        for href in value:
            fx_item_cat_model_min._record.distribution.append(
                Distribution(
                    distributor=Contact(organisation=ContactIdentity(name="x"), role={ContactRoleCode.DISTRIBUTOR}),
                    format=Format(format="x", href=href),
                    transfer_option=TransferOption(
                        online_resource=OnlineResource(href=href, function=OnlineResourceFunctionCode.DOWNLOAD)
                    ),
                )
            )
        expected = fx_item_cat_model_min._data.items[0]
        html = BeautifulSoup(render_item_catalogue(fx_item_cat_model_min), parser="html.parser", features="lxml")

        assert html.select_one(f"button[data-target='{expected.access_target}']") is not None
        # noinspection PyTypeChecker
        assert html.find(name="span", string=expected.format_type.value) is not None
        assert str(html).count(text) == 2  # one in collapsible, one in <noscript>

        for tag in html.find_all("noscript"):
            tag.decompose()  # drop
        assert str(html).count(text) == 1  # only collapsible

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            (
                Constraint(
                    type=ConstraintTypeCode.ACCESS,
                    restriction_code=ConstraintRestrictionCode.UNRESTRICTED,
                    statement="Open Access",
                ),
                False,
            ),
            (
                Constraint(
                    type=ConstraintTypeCode.ACCESS,
                    restriction_code=ConstraintRestrictionCode.RESTRICTED,
                    statement="Closed Access",
                ),
                True,
            ),
        ],
    )
    def test_restricted_access(
        self,
        fx_item_cat_model_min: ItemCatalogue,
        fx_item_cat_model_open: ItemCatalogue,
        fx_admin_meta_keys: AdministrationKeys,
        value: Constraint,
        expected: bool,
    ):
        """Shows restricted access panel if item is restricted."""
        model = fx_item_cat_model_min
        if value.restriction_code == ConstraintRestrictionCode.UNRESTRICTED:
            model = fx_item_cat_model_open
        model._record.distribution.append(
            Distribution(
                distributor=Contact(organisation=ContactIdentity(name="x"), role={ContactRoleCode.DISTRIBUTOR}),
                format=Format(format="x", href="https://www.iana.org/assignments/media-types/image/png"),
                transfer_option=TransferOption(
                    size=Size(unit="bytes", magnitude=1024),
                    online_resource=OnlineResource(href="x", function=OnlineResourceFunctionCode.DOWNLOAD),
                ),
            )
        )
        model._record.identification.constraints = Constraints([value])
        html = BeautifulSoup(render_item_catalogue(model), parser="html.parser", features="lxml")

        result = html.select_one("#data-restricted-info")
        if expected:
            assert result is not None
        else:
            assert result is None


class TestAuthorsTab:
    """Test authors tab template macros."""

    base_contact = Contact(organisation=ContactIdentity(name="x"), email="x", role={ContactRoleCode.POINT_OF_CONTACT})

    @pytest.mark.parametrize(
        "value",
        [
            Contacts([base_contact]),
            Contacts(
                [
                    base_contact,
                    Contact(organisation=ContactIdentity(name="x"), role={ContactRoleCode.AUTHOR}),
                ]
            ),
        ],
    )
    def test_enabled(self, fx_item_cat_model_min: ItemCatalogue, value: Contacts):
        """
        Can get items tab if enabled in item.

        Point of Contact role always required.
        """
        fx_item_cat_model_min._record.identification.contacts = value
        expected = fx_item_cat_model_min._authors.enabled
        html = BeautifulSoup(render_item_catalogue(fx_item_cat_model_min), parser="html.parser", features="lxml")

        if expected:
            assert html.select_one("#tab-content-authors") is not None
        else:
            assert html.select_one("#tab-content-authors") is None

    def test_authors(self, fx_item_cat_model_min: ItemCatalogue):
        """
        Can get item authors with expected values from item.

        Basic count test. Subsequent tests check for author item elements.
        """
        items = Contacts(
            [
                self.base_contact,
                Contact(organisation=ContactIdentity(name="x"), role={ContactRoleCode.AUTHOR}),
                Contact(organisation=ContactIdentity(name="y"), role={ContactRoleCode.AUTHOR}),
            ]
        )
        fx_item_cat_model_min._record.identification.contacts = items
        expected = fx_item_cat_model_min._authors.items
        html = BeautifulSoup(render_item_catalogue(fx_item_cat_model_min), parser="html.parser", features="lxml")

        for item in expected:
            # noinspection PyTypeChecker
            assert html.find("div", string=item.organisation.name) is not None

    @pytest.mark.parametrize(
        "value",
        [
            Contact(organisation=ContactIdentity(name="x"), role={ContactRoleCode.AUTHOR}),
            Contact(individual=ContactIdentity(name="x"), role={ContactRoleCode.AUTHOR}),
            Contact(
                individual=ContactIdentity(name="x"),
                organisation=ContactIdentity(name="y"),
                role={ContactRoleCode.AUTHOR},
            ),
            Contact(individual=ContactIdentity(name="x"), email="x", role={ContactRoleCode.AUTHOR}),
            Contact(individual=ContactIdentity(name="x", href="x"), role={ContactRoleCode.AUTHOR}),
        ],
    )
    def test_author(self, fx_item_cat_model_min: ItemCatalogue, value: Contact):
        """Can get individual author elements based on values from item."""
        items = Contacts([self.base_contact, value])
        fx_item_cat_model_min._record.identification.contacts = items
        expected = fx_item_cat_model_min._authors.items[0]
        html = BeautifulSoup(render_item_catalogue(fx_item_cat_model_min), parser="html.parser", features="lxml")

        if expected.organisation is not None:
            # noinspection PyTypeChecker
            assert html.find("div", string=expected.organisation.name) is not None
        if expected.individual is not None:
            # noinspection PyTypeChecker
            assert html.find("div", string=expected.individual.name) is not None
        if expected.orcid is not None:
            assert html.find("a", href=expected.orcid) is not None


class TestLicenceTab:
    """Test licence tab template macros."""

    @pytest.mark.parametrize(
        "value",
        [
            Constraints([]),
            Constraints(
                [
                    Constraint(
                        type=ConstraintTypeCode.USAGE,
                        restriction_code=ConstraintRestrictionCode.LICENSE,
                    )
                ]
            ),
            Constraints(
                [
                    Constraint(
                        type=ConstraintTypeCode.USAGE,
                        restriction_code=ConstraintRestrictionCode.LICENSE,
                        href="x",
                    )
                ]
            ),
            Constraints(
                [
                    Constraint(
                        type=ConstraintTypeCode.USAGE,
                        restriction_code=ConstraintRestrictionCode.LICENSE,
                        href=Licence.OGL_UK_3_0.value,
                    )
                ]
            ),
        ],
    )
    def test_enabled(self, fx_item_cat_model_min: ItemCatalogue, value: Constraints):
        """Can get licence tab if enabled in item."""
        fx_item_cat_model_min._record.identification.constraints = value
        expected = fx_item_cat_model_min._licence.enabled
        html = BeautifulSoup(render_item_catalogue(fx_item_cat_model_min), parser="html.parser", features="lxml")

        if expected:
            assert html.select_one("#tab-content-licence") is not None
        else:
            assert html.select_one("#tab-content-licence") is None

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            (
                "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/",
                "Open Government Licence (OGL 3.0)",
            ),
            (
                "https://creativecommons.org/licenses/by/4.0/",
                "Creative Commons Attribution 4.0 International Licence (CC BY 4.0)",
            ),
            (
                "https://metadata-resources.data.bas.ac.uk/licences/all-rights-reserved-v1/",
                "BAS All Rights Reserved Licence (v1)",
            ),
            (
                "https://metadata-resources.data.bas.ac.uk/licences/operations-mapping-v1/",
                "BAS Operations Mapping Internal Use Licence (v1)",
            ),
        ],
    )
    def test_licence(self, fx_item_cat_model_min: ItemCatalogue, value: str, expected: str):
        """Can get matching licence template based on value from item."""
        fx_item_cat_model_min._record.identification.constraints = Constraints(
            [Constraint(type=ConstraintTypeCode.USAGE, restriction_code=ConstraintRestrictionCode.LICENSE, href=value)]
        )
        html = BeautifulSoup(render_item_catalogue(fx_item_cat_model_min), parser="html.parser", features="lxml")

        # noinspection PyTypeChecker
        assert html.find(name="strong", string="Item licence") is not None

        licence = html.select_one(f"a[href='{value}']")
        assert licence is not None
        assert licence.text.strip() == expected

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ([], []),
            ([Contact(organisation=ContactIdentity(name="x"), role={ContactRoleCode.RIGHTS_HOLDER})], ["x"]),
            (
                [
                    Contact(
                        organisation=ContactIdentity(name="x"),
                        online_resource=OnlineResource(href="x", function=OnlineResourceFunctionCode.INFORMATION),
                        role={ContactRoleCode.RIGHTS_HOLDER},
                    ),
                    Contact(individual=ContactIdentity(name="y"), role={ContactRoleCode.RIGHTS_HOLDER}),
                ],
                ["x", "y"],
            ),
        ],
    )
    def test_copyright_holders(self, fx_item_cat_model_min: ItemCatalogue, value: list[Contact], expected: str):
        """Can get optional copyright holders based on value from item."""
        # needed to enable tab
        fx_item_cat_model_min._record.identification.constraints = Constraints(
            [
                Constraint(
                    type=ConstraintTypeCode.USAGE,
                    restriction_code=ConstraintRestrictionCode.LICENSE,
                    href="https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/",
                )
            ]
        )
        fx_item_cat_model_min._record.identification.contacts.extend(value)
        html = BeautifulSoup(render_item_catalogue(fx_item_cat_model_min), parser="html.parser", features="lxml")

        label_text = "Copyright Holder" if len(expected) < 2 else "Copyright Holders"
        # noinspection PyTypeChecker
        label = html.find(name="strong", string=label_text)
        assert label is not None if expected else label is None

        expected_string = ", ".join(expected)
        output = html.select_one("#licence-copyright")
        if not expected:
            assert output is None
            return
        output_normalised = ", ".join([el.strip() for el in output.text.split(",")])
        assert output_normalised == expected_string


class TestExtentTab:
    """Test extent tab template macros."""

    @pytest.mark.parametrize(
        "value",
        [
            Extents([]),
            Extents(
                [
                    Extent(
                        identifier="bounding",
                        geographic=ExtentGeographic(
                            bounding_box=BoundingBox(
                                west_longitude=1.0, east_longitude=1.0, south_latitude=1.0, north_latitude=1.0
                            )
                        ),
                    ),
                ]
            ),
        ],
    )
    def test_enabled(self, fx_item_cat_model_min: ItemCatalogue, value: Extents):
        """Can get data tab if enabled in item."""
        fx_item_cat_model_min._record.identification.extents = value
        expected = fx_item_cat_model_min._extent.enabled
        html = BeautifulSoup(render_item_catalogue(fx_item_cat_model_min), parser="html.parser", features="lxml")

        if expected:
            assert html.select_one("#tab-content-extent") is not None
        else:
            assert html.select_one("#tab-content-extent") is None

    @pytest.mark.parametrize(
        "value",
        [
            Extent(
                identifier="bounding",
                geographic=ExtentGeographic(
                    bounding_box=BoundingBox(
                        west_longitude=1.0, east_longitude=1.0, south_latitude=1.0, north_latitude=1.0
                    )
                ),
            ),
            Extent(
                identifier="bounding",
                geographic=ExtentGeographic(
                    bounding_box=BoundingBox(
                        west_longitude=1.0, east_longitude=1.0, south_latitude=1.0, north_latitude=1.0
                    )
                ),
                temporal=ExtentTemporal(period=TemporalPeriod(start=Date(date=date(2023, 10, 31)))),
            ),
            Extent(
                identifier="bounding",
                geographic=ExtentGeographic(
                    bounding_box=BoundingBox(
                        west_longitude=1.0, east_longitude=1.0, south_latitude=1.0, north_latitude=1.0
                    )
                ),
                temporal=ExtentTemporal(period=TemporalPeriod(end=Date(date=date(2023, 10, 31)))),
            ),
            Extent(
                identifier="bounding",
                geographic=ExtentGeographic(
                    bounding_box=BoundingBox(
                        west_longitude=1.0, east_longitude=1.0, south_latitude=1.0, north_latitude=1.0
                    )
                ),
                temporal=ExtentTemporal(
                    period=TemporalPeriod(start=Date(date=date(2023, 10, 31)), end=Date(date=date(2023, 11, 1)))
                ),
            ),
        ],
    )
    def test_extent(self, fx_item_cat_model_min: ItemCatalogue, value: Extent):
        """Can get individual extent elements based on values from item."""
        fx_item_cat_model_min._record.identification.extents = Extents([value])
        expected = fx_item_cat_model_min._extent
        html = BeautifulSoup(render_item_catalogue(fx_item_cat_model_min), parser="html.parser", features="lxml")
        bbox = expected.bounding_box
        bbox_min = f"South: {bbox[1]}, West: {bbox[0]}"
        bbox_max = f"North: {bbox[3]}, East: {bbox[2]}"

        assert html.select_one(f"iframe[src='{expected.map_iframe}']") is not None
        assert html.select_one("#bbox-min").text.strip() == bbox_min
        assert html.select_one("#bbox-max").text.strip() == bbox_max

        if expected.start:
            assert html.select_one("#period-start").text.strip() == expected.start.value
            assert html.select_one("#period-start")["datetime"] == expected.start.datetime
        else:
            assert html.select_one("#period-start") is None

        if expected.end:
            assert html.select_one("#period-end").text.strip() == expected.end.value
            assert html.select_one("#period-end")["datetime"] == expected.end.datetime
        else:
            assert html.select_one("#period-end") is None

    @staticmethod
    def _get_record_extents(identifier: str) -> RecordRevision:
        """Local get_record method returning related records with an extent."""
        record = _get_record(identifier)
        record.identification.extents = Extents(
            [
                Extent(
                    identifier="bounding",
                    geographic=ExtentGeographic(
                        bounding_box=BoundingBox(
                            west_longitude=1.0, east_longitude=1.0, south_latitude=1.0, north_latitude=1.0
                        )
                    ),
                )
            ]
        )
        return record

    @pytest.mark.cov()
    def test_extents(self, fx_item_physical_map_model_min: ItemCataloguePhysicalMap):
        """
        Can get multiple extents.

        E.g. for physical maps.
        """
        item = fx_item_physical_map_model_min
        item._get_record = self._get_record_extents
        html = BeautifulSoup(
            render_item_catalogue(fx_item_physical_map_model_min), parser="html.parser", features="lxml"
        )

        assert len(html.select("#tab-content-extent iframe")) == len(item._extent._extents)


class TestLineageTab:
    """Test lineage tab template macros."""

    @pytest.mark.parametrize("value", [None, "x"])
    def test_enabled(self, fx_item_cat_model_min: ItemCatalogue, value: str | None):
        """Can get lineage tab if enabled in item."""
        fx_item_cat_model_min._record.data_quality = DataQuality(lineage=Lineage(statement=value))
        expected = fx_item_cat_model_min._lineage.enabled
        html = BeautifulSoup(render_item_catalogue(fx_item_cat_model_min), parser="html.parser", features="lxml")

        if expected:
            assert html.select_one("#tab-content-lineage") is not None
        else:
            assert html.select_one("#tab-content-lineage") is None

    @pytest.mark.parametrize("value", [None, "x"])
    def test_collections(self, fx_item_cat_model_min: ItemCatalogue, value: str | None):
        """Can get optional lineage statement with expected values from item."""
        fx_item_cat_model_min._record.data_quality = DataQuality(lineage=Lineage(statement=value))
        expected = fx_item_cat_model_min._lineage.statement
        html = BeautifulSoup(render_item_catalogue(fx_item_cat_model_min), parser="html.parser", features="lxml")

        if fx_item_cat_model_min._lineage.enabled:
            assert expected in str(html.select_one("#lineage-statement"))


class TestRelatedTab:
    """Test related tab template macros."""

    @pytest.mark.parametrize(
        "value",
        [
            Aggregations([]),
            Aggregations(
                [
                    Aggregation(
                        identifier=Identifier(identifier="x", href="x", namespace="x"),
                        association_type=AggregationAssociationCode.LARGER_WORK_CITATION,
                        initiative_type=AggregationInitiativeCode.COLLECTION,
                    )
                ]
            ),
        ],
    )
    def test_enabled(self, fx_item_cat_model_min: ItemCatalogue, value: Aggregations):
        """Can get related tab if enabled in item."""
        fx_item_cat_model_min._record.identification.aggregations = value
        expected = fx_item_cat_model_min._related.enabled
        html = BeautifulSoup(render_item_catalogue(fx_item_cat_model_min), parser="html.parser", features="lxml")

        if expected:
            assert html.select_one("#tab-content-related") is not None
        else:
            assert html.select_one("#tab-content-related") is None

    @pytest.mark.parametrize(
        "value",
        [
            Aggregations([]),
            Aggregations(
                [
                    Aggregation(
                        identifier=Identifier(identifier="x", href="x", namespace="x"),
                        association_type=AggregationAssociationCode.LARGER_WORK_CITATION,
                        initiative_type=AggregationInitiativeCode.PAPER_MAP,
                    )
                ]
            ),
        ],
    )
    def test_parent_printed_map(self, fx_item_cat_model_min: ItemCatalogue, value: Aggregations):
        """
        Can get optional parent paper map with expected values from item.

        Detailed item summary tests are run in common macro tests.
        """
        fx_item_cat_model_min._record.identification.aggregations = value
        related = fx_item_cat_model_min._related.parent_printed_map
        expected: list | None = [related] if related else None
        html = BeautifulSoup(render_item_catalogue(fx_item_cat_model_min), parser="html.parser", features="lxml")

        items = html.select_one("#related-parent-printed-map")
        if expected:
            for item in expected:
                assert items.select_one(f"a[href='{item._href}']") is not None
        else:
            assert items is None

    @pytest.mark.parametrize(
        "value",
        [
            Aggregations([]),
            Aggregations(
                [
                    Aggregation(
                        identifier=Identifier(identifier="x", href="x", namespace="x"),
                        association_type=AggregationAssociationCode.PHYSICAL_REVERSE_OF,
                        initiative_type=AggregationInitiativeCode.PAPER_MAP,
                    )
                ]
            ),
        ],
    )
    def test_peer_opposite_side(self, fx_item_cat_model_min: ItemCatalogue, value: Aggregations):
        """
        Can get optional opposite side of a paper map with expected values from item.

        Detailed item summary tests are run in common macro tests.
        """
        fx_item_cat_model_min._record.identification.aggregations = value
        related = fx_item_cat_model_min._related.peer_opposite_side
        expected: list | None = [related] if related else None
        html = BeautifulSoup(render_item_catalogue(fx_item_cat_model_min), parser="html.parser", features="lxml")

        items = html.select_one("#related-peer-opposite-side")
        if expected:
            for item in expected:
                assert items.select_one(f"a[href='{item._href}']") is not None
        else:
            assert items is None

    @pytest.mark.parametrize(
        "value",
        [
            Aggregations([]),
            Aggregations(
                [
                    Aggregation(
                        identifier=Identifier(identifier="x", href="x", namespace="x"),
                        association_type=AggregationAssociationCode.CROSS_REFERENCE,
                    ),
                    Aggregation(
                        identifier=Identifier(identifier="y", href="y", namespace="y"),
                        association_type=AggregationAssociationCode.CROSS_REFERENCE,
                    ),
                ]
            ),
        ],
    )
    def test_peer_cross_reference(self, fx_item_cat_model_min: ItemCatalogue, value: Aggregations):
        """
        Can get optional peer cross-references unrelated to other cross-reference contexts with expected values from item.

        Detailed item summary tests are run in common macro tests.
        """
        fx_item_cat_model_min._record.identification.aggregations = value
        expected = fx_item_cat_model_min._related.peer_cross_reference
        html = BeautifulSoup(render_item_catalogue(fx_item_cat_model_min), parser="html.parser", features="lxml")

        related = html.select_one("#related-peer-items")
        if len(expected) > 0:
            for item in expected:
                assert related.select_one(f"a[href='{item._href}']") is not None
        else:
            assert related is None

    @pytest.mark.parametrize(
        "value",
        [
            Aggregations([]),
            Aggregations(
                [
                    Aggregation(
                        identifier=Identifier(identifier="x", href="x", namespace="x"),
                        association_type=AggregationAssociationCode.REVISION_OF,
                    ),
                ]
            ),
        ],
    )
    def test_peer_supersedes(self, fx_item_cat_model_min: ItemCatalogue, value: Aggregations):
        """
        Can get optional peer items item supersedes with expected values from item.

        Detailed item summary tests are run in common macro tests.
        """
        fx_item_cat_model_min._record.identification.aggregations = value
        expected = fx_item_cat_model_min._related.peer_supersedes
        html = BeautifulSoup(render_item_catalogue(fx_item_cat_model_min), parser="html.parser", features="lxml")

        replaced = html.select_one("#related-peer-supersedes")
        if len(expected) > 0:
            for item in expected:
                assert replaced.select_one(f"a[href='{item._href}']") is not None
        else:
            assert replaced is None

    @pytest.mark.parametrize(
        "value",
        [
            Aggregations([]),
            Aggregations(
                [
                    Aggregation(
                        identifier=Identifier(identifier="x", href="x", namespace="x"),
                        association_type=AggregationAssociationCode.LARGER_WORK_CITATION,
                        initiative_type=AggregationInitiativeCode.COLLECTION,
                    ),
                    Aggregation(
                        identifier=Identifier(identifier="y", href="y", namespace="y"),
                        association_type=AggregationAssociationCode.LARGER_WORK_CITATION,
                        initiative_type=AggregationInitiativeCode.COLLECTION,
                    ),
                ]
            ),
        ],
    )
    def test_parent_collections(self, fx_item_cat_model_min: ItemCatalogue, value: Aggregations):
        """
        Can get optional parent collections with expected values from item.

        Detailed item summary tests are run in common macro tests.
        """
        fx_item_cat_model_min._record.identification.aggregations = value
        expected = fx_item_cat_model_min._related.parent_collections
        html = BeautifulSoup(render_item_catalogue(fx_item_cat_model_min), parser="html.parser", features="lxml")

        collections = html.select_one("#related-parent-collections")
        if len(expected) > 0:
            for item in expected:
                assert collections.select_one(f"a[href='{item._href}']") is not None
        else:
            assert collections is None

    @pytest.mark.parametrize(
        "value",
        [
            Aggregations([]),
            Aggregations(
                [
                    Aggregation(
                        identifier=Identifier(identifier="x", href="x", namespace="x"),
                        association_type=AggregationAssociationCode.CROSS_REFERENCE,
                        initiative_type=AggregationInitiativeCode.COLLECTION,
                    ),
                    Aggregation(
                        identifier=Identifier(identifier="y", href="y", namespace="y"),
                        association_type=AggregationAssociationCode.CROSS_REFERENCE,
                        initiative_type=AggregationInitiativeCode.COLLECTION,
                    ),
                ]
            ),
        ],
    )
    def test_peer_collections(self, fx_item_cat_model_min: ItemCatalogue, value: Aggregations):
        """
        Can get optional peer collections with expected values from item.

        Detailed item summary tests are run in common macro tests.
        """
        fx_item_cat_model_min._record.identification.aggregations = value
        expected = fx_item_cat_model_min._related.peer_collections
        html = BeautifulSoup(render_item_catalogue(fx_item_cat_model_min), parser="html.parser", features="lxml")

        collections = html.select_one("#related-peer-collections")
        if len(expected) > 0:
            for item in expected:
                assert collections.select_one(f"a[href='{item._href}']") is not None
        else:
            assert collections is None


class TestInfoTab:
    """Test additional information tab template macros."""

    def test_enabled(self, fx_item_cat_model_min: ItemCatalogue):
        """Can get additional information tab (always enabled)."""
        html = BeautifulSoup(render_item_catalogue(fx_item_cat_model_min), parser="html.parser", features="lxml")

        assert html.select_one("#tab-content-info") is not None

    def test_id(self, fx_item_cat_model_min: ItemCatalogue):
        """Can get item id based on value from item."""
        expected = fx_item_cat_model_min._additional_info.item_id
        html = BeautifulSoup(render_item_catalogue(fx_item_cat_model_min), parser="html.parser", features="lxml")

        assert html.select_one("#info-id").text.strip() == expected

    def test_type(self, fx_item_cat_model_min: ItemCatalogue):
        """Can get item type based on value from item."""
        expected = fx_item_cat_model_min._additional_info
        html = BeautifulSoup(render_item_catalogue(fx_item_cat_model_min), parser="html.parser", features="lxml")

        assert html.select_one("#info-type i")["class"] == expected.item_type_icon.split(" ")
        assert html.select_one("#info-type").text.strip() == expected.item_type

    @pytest.mark.parametrize("value", [Series, Series(name="x", page="y", edition="z")])
    def test_series_name(self, fx_item_cat_model_min: ItemCatalogue, value: Series):
        """Can get optional item descriptive series name based on value from item."""
        fx_item_cat_model_min._record.identification.series = value
        expected = fx_item_cat_model_min._additional_info.series_name
        html = BeautifulSoup(render_item_catalogue(fx_item_cat_model_min), parser="html.parser", features="lxml")

        series_name = html.select_one("#info-series-name")
        if expected:
            assert series_name.text.strip() == expected
        else:
            assert series_name is None

    @pytest.mark.cov()
    def test_series_names(self, mocker: MockerFixture, fx_item_physical_map_model_min: ItemCataloguePhysicalMap):
        """
        Can get optional multiple series names.

        E.g. for physical maps.
        """
        mocker.patch.object(
            fx_item_physical_map_model_min._additional_info.__class__,
            "series_names",
            new_callable=PropertyMock,
            return_value=["x", "y"],
        )
        html = BeautifulSoup(
            render_item_catalogue(fx_item_physical_map_model_min), parser="html.parser", features="lxml"
        )

        names = html.select_one("#info-series-name")
        for value in fx_item_physical_map_model_min._additional_info.series_names:
            assert names.find(name="li", string=value) is not None

    @pytest.mark.parametrize("value", [Series, Series(name="x", page="y", edition="z")])
    def test_sheet_number(self, fx_item_cat_model_min: ItemCatalogue, value: Series):
        """Can get optional item descriptive series sheet number based on value from item."""
        fx_item_cat_model_min._record.identification.series = value
        expected = fx_item_cat_model_min._additional_info.sheet_number
        html = BeautifulSoup(render_item_catalogue(fx_item_cat_model_min), parser="html.parser", features="lxml")

        sheet_number = html.select_one("#info-sheet-number")
        if expected:
            assert sheet_number.text.strip() == expected
        else:
            assert sheet_number is None

    @pytest.mark.cov()
    def test_sheet_numbers(self, mocker: MockerFixture, fx_item_physical_map_model_min: ItemCataloguePhysicalMap):
        """
        Can get optional multiple series sheet numbers.

        E.g. for physical maps.
        """
        mocker.patch.object(
            fx_item_physical_map_model_min._additional_info.__class__,
            "sheet_numbers",
            new_callable=PropertyMock,
            return_value=["x", "y"],
        )
        html = BeautifulSoup(
            render_item_catalogue(fx_item_physical_map_model_min), parser="html.parser", features="lxml"
        )

        numbers = html.select_one("#info-sheet-number")
        for value in fx_item_physical_map_model_min._additional_info.sheet_numbers:
            assert numbers.find(name="li", string=value) is not None

    @pytest.mark.parametrize("value", [None, 1.0])
    def test_scale(self, fx_item_cat_model_min: ItemCatalogue, value: float | None):
        """Can get optional item scale based on value from item."""
        fx_item_cat_model_min._record.identification.scale = value
        expected = fx_item_cat_model_min._additional_info.scale
        html = BeautifulSoup(render_item_catalogue(fx_item_cat_model_min), parser="html.parser", features="lxml")

        scale = html.select_one("#info-scale")
        if expected:
            assert scale.text.strip() == expected
        else:
            assert scale is None

    @pytest.mark.cov()
    def test_scales(self, mocker: MockerFixture, fx_item_physical_map_model_min: ItemCataloguePhysicalMap):
        """
        Can get optional multiple scales.

        E.g. for physical maps.
        """
        mocker.patch.object(
            fx_item_physical_map_model_min._additional_info.__class__,
            "scales",
            new_callable=PropertyMock,
            return_value=["x", "y"],
        )
        html = BeautifulSoup(
            render_item_catalogue(fx_item_physical_map_model_min), parser="html.parser", features="lxml"
        )

        scale = html.select_one("#info-scale")
        for value in fx_item_physical_map_model_min._additional_info.scales:
            assert scale.find(name="li", string=value) is not None

    @pytest.mark.parametrize("value", [None, ReferenceSystemInfo(code=Code(value="x"))])
    def test_projection(self, fx_item_cat_model_min: ItemCatalogue, value: ReferenceSystemInfo):
        """Can get optional item projection based on value from item."""
        fx_item_cat_model_min._record.reference_system_info = value
        expected = fx_item_cat_model_min._additional_info.projection
        html = BeautifulSoup(render_item_catalogue(fx_item_cat_model_min), parser="html.parser", features="lxml")

        projection = html.select_one("#info-projection")
        if expected:
            assert projection.text.strip() == expected.value
            assert projection["href"] == expected.href
        else:
            assert projection is None

    @pytest.mark.parametrize(
        "value",
        [
            None,
            json.dumps({"width": 1, "height": 1}),
            json.dumps({"width": 210, "height": 297}),
            json.dumps({"width": 297, "height": 210}),
        ],
    )
    def test_size(self, fx_item_cat_model_min: ItemCatalogue, value: str | None):
        """Can get optional item physical page size based on value from item."""
        fx_item_cat_model_min._record.identification.supplemental_information = value
        expected = fx_item_cat_model_min._additional_info.page_size
        html = BeautifulSoup(render_item_catalogue(fx_item_cat_model_min), parser="html.parser", features="lxml")

        size = html.select_one("#info-page-size")
        if expected:
            assert size.text.strip() == expected
        else:
            assert size is None
        if expected is not None and "portrait" in expected.lower():
            assert size.select_one("i.fa-rectangle-portrait") is not None
        if expected is not None and "landscape" in expected.lower():
            assert size.select_one("i.fa-rectangle-landscape") is not None

    @pytest.mark.parametrize(
        "value",
        [
            [],
            [
                Identifier(identifier="x/x", href=f"https://{CATALOGUE_NAMESPACE}/x/x", namespace=ALIAS_NAMESPACE),
                Identifier(identifier="y/y", href=f"https://{CATALOGUE_NAMESPACE}/y/y", namespace=ALIAS_NAMESPACE),
            ],
        ],
    )
    def test_aliases(self, fx_item_cat_model_min: ItemCatalogue, value: list[Identifier]):
        """Can get optional item DOIs based on value from item."""
        fx_item_cat_model_min._record.identification.identifiers.extend(value)
        expected = fx_item_cat_model_min._additional_info.aliases
        html = BeautifulSoup(render_item_catalogue(fx_item_cat_model_min), parser="html.parser", features="lxml")

        alias = html.select_one("#info-aliases")
        if expected:
            for item in expected:
                assert alias.select_one(f"a[href='{item.href}']") is not None
        else:
            assert alias is None

    @pytest.mark.parametrize(
        "value",
        [
            [],
            [
                Identifier(identifier="x", href="x", namespace="doi"),
                Identifier(identifier="y", href="y", namespace="doi"),
            ],
        ],
    )
    def test_doi(self, fx_item_cat_model_min: ItemCatalogue, value: list[Identifier]):
        """Can get optional item DOIs based on value from item."""
        fx_item_cat_model_min._record.identification.identifiers.extend(value)
        expected = fx_item_cat_model_min._additional_info.doi
        html = BeautifulSoup(render_item_catalogue(fx_item_cat_model_min), parser="html.parser", features="lxml")

        doi = html.select_one("#info-doi")
        if expected:
            for item in expected:
                assert doi.select_one(f"a[href='{item.href}']") is not None
        else:
            assert doi is None

    @pytest.mark.parametrize(
        "value",
        [
            [],
            [
                Identifier(identifier="x", href="x", namespace="isbn"),
                Identifier(identifier="y", href="y", namespace="isbn"),
            ],
        ],
    )
    def test_isbn(self, fx_item_cat_model_min: ItemCatalogue, value: list[Identifier]):
        """Can get optional item ISBNs based on value from item."""
        fx_item_cat_model_min._record.identification.identifiers.extend(value)
        expected = fx_item_cat_model_min._additional_info.isbn
        html = BeautifulSoup(render_item_catalogue(fx_item_cat_model_min), parser="html.parser", features="lxml")

        isbn = html.select_one("#info-isbn")
        if expected:
            for item in expected:
                # noinspection PyTypeChecker
                assert isbn.find(name="li", string=item) is not None
        else:
            assert isbn is None

    @pytest.mark.parametrize(
        "value",
        [
            [],
            [
                "https://gitlab.data.bas.ac.uk/MAGIC/x/-/issues/123",
                "https://gitlab.data.bas.ac.uk/MAGIC/x/-/issues/234",
            ],
        ],
    )
    def test_issues(self, fx_item_cat_model_min: ItemCatalogue, value: list[str]):
        """Can get optional item GitLab issues based on value from item."""
        admin_meta = get_admin(keys=fx_item_cat_model_min._admin_keys, record=fx_item_cat_model_min._record)
        admin_meta.gitlab_issues = value
        set_admin(keys=fx_item_cat_model_min._admin_keys, record=fx_item_cat_model_min._record, admin_meta=admin_meta)
        expected = fx_item_cat_model_min._additional_info.gitlab_issues
        html = BeautifulSoup(render_item_catalogue(fx_item_cat_model_min), parser="html.parser", features="lxml")

        issues = html.select_one("#info-issues")
        if expected:
            for item in expected:
                # noinspection PyTypeChecker
                assert issues.find(name="li", string=item) is not None
        else:
            assert issues is None

    def test_dates(self, fx_item_cat_model_min: ItemCatalogue):
        """Can get item dates based on values from item."""
        expected = fx_item_cat_model_min._additional_info.dates
        html = BeautifulSoup(render_item_catalogue(fx_item_cat_model_min), parser="html.parser", features="lxml")

        for label, item in expected.items():
            element = html.select_one(f"#info-{label.lower().replace(' ', '-')}")
            assert element.text.strip() == item.value
            assert element["datetime"] == item.datetime

    @pytest.mark.parametrize("value", [Maintenance(), Maintenance(progress=ProgressCode.COMPLETED)])
    def test_status(self, fx_item_cat_model_min: ItemCatalogue, value: Maintenance):
        """Can get optional item status info based on value from item."""
        fx_item_cat_model_min._record.identification.maintenance = value
        expected = fx_item_cat_model_min._additional_info.status
        html = BeautifulSoup(render_item_catalogue(fx_item_cat_model_min), parser="html.parser", features="lxml")

        status = html.select_one("#info-status")
        if expected:
            assert status.text.strip() == expected
        else:
            assert status is None

    @pytest.mark.parametrize(
        "value", [Maintenance(), Maintenance(maintenance_frequency=MaintenanceFrequencyCode.AS_NEEDED)]
    )
    def test_frequency(self, fx_item_cat_model_min: ItemCatalogue, value: Maintenance):
        """Can get optional item update frequency info based on value from item."""
        fx_item_cat_model_min._record.identification.maintenance = value
        expected = fx_item_cat_model_min._additional_info.frequency
        html = BeautifulSoup(render_item_catalogue(fx_item_cat_model_min), parser="html.parser", features="lxml")

        frequency = html.select_one("#info-frequency")
        if expected:
            assert frequency.text.strip() == expected
        else:
            assert frequency is None

    def test_datestamp(self, fx_item_cat_model_min: ItemCatalogue):
        """Can get metadata datestamp based on value from item."""
        expected = fx_item_cat_model_min._additional_info.datestamp
        html = BeautifulSoup(render_item_catalogue(fx_item_cat_model_min), parser="html.parser", features="lxml")

        assert html.select_one("#info-datestamp").text.strip() == expected.value
        assert html.select_one("#info-datestamp")["datetime"] == expected.datetime

    def test_standard(self, fx_item_cat_model_min: ItemCatalogue):
        """Can get metadata standard and version based on value from item."""
        expected = fx_item_cat_model_min._additional_info
        html = BeautifulSoup(render_item_catalogue(fx_item_cat_model_min), parser="html.parser", features="lxml")

        assert html.select_one("#info-standard").text.strip() == expected.standard
        assert html.select_one("#info-standard-version").text.strip() == expected.standard_version

    @pytest.mark.parametrize(
        "value",
        [
            [],
            [
                DomainConsistency(
                    specification=Citation(title="x", href="x", dates=Dates(publication=Date(date=date(2010, 10, 31)))),
                    explanation="x",
                    result=True,
                )
            ],
        ],
    )
    def test_profiles(self, fx_item_cat_model_min: ItemCatalogue, value: list[DomainConsistency]):
        """Can get metadata profiles based on values from item."""
        fx_item_cat_model_min._record.data_quality = DataQuality(domain_consistency=value)
        expected = fx_item_cat_model_min._additional_info.profiles
        html = BeautifulSoup(render_item_catalogue(fx_item_cat_model_min), parser="html.parser", features="lxml")

        profiles = html.select_one("#info-profiles")
        if len(expected) > 0:
            for item in expected:
                assert profiles.select_one(f"a[href='{item.href}']") is not None
        else:
            assert profiles is None

    def test_record_links(self, fx_item_cat_model_min: ItemCatalogue):
        """Can get metadata record links based on values from item."""
        expected = fx_item_cat_model_min._additional_info.record_links
        html = BeautifulSoup(render_item_catalogue(fx_item_cat_model_min), parser="html.parser", features="lxml")

        links = html.select_one("#info-records")
        if len(expected) > 0:
            for item in expected:
                assert links.select_one(f"a[href='{item.href}']") is not None
        else:
            assert links is None

    def test_build_time(self, fx_item_cat_model_min: ItemCatalogue):
        """Can get link to record revision based on values from item."""
        html = BeautifulSoup(render_item_catalogue(fx_item_cat_model_min), parser="html.parser", features="lxml")

        build = html.select_one("#info-build")
        assert build.select_one("time") is not None


class TestContactTab:
    """Test contact tab template macros."""

    def test_enabled(self, fx_item_cat_model_min: ItemCatalogue):
        """Can get contact tab (always enabled)."""
        html = BeautifulSoup(render_item_catalogue(fx_item_cat_model_min), parser="html.parser", features="lxml")

        assert html.select_one("#tab-content-contact") is not None

    def test_subject(self, fx_item_cat_model_min: ItemCatalogue):
        """Can get contact form subject with expected value from item."""
        expected = fx_item_cat_model_min._contact.subject_default
        html = BeautifulSoup(render_item_catalogue(fx_item_cat_model_min), parser="html.parser", features="lxml")

        assert html.select_one("#message-subject")["value"] == expected

    @pytest.mark.parametrize(
        "value",
        [
            Contact(organisation=ContactIdentity(name="x"), email="x", role={ContactRoleCode.POINT_OF_CONTACT}),
            Contact(
                organisation=ContactIdentity(name="x"), phone="x", email="x", role={ContactRoleCode.POINT_OF_CONTACT}
            ),
            Contact(
                organisation=ContactIdentity(name="x"),
                address=Address(delivery_point="x"),
                email="x",
                role={ContactRoleCode.POINT_OF_CONTACT},
            ),
        ],
    )
    def test_alternate(self, fx_item_cat_model_min: ItemCatalogue, value: Contact):
        """
        Can get optional alternate contact information based on, and with, values from item.

        Email is always expected as the ItemCatalogue class requires it.
        """
        fx_item_cat_model_min._record.identification.contacts = Contacts([value])
        expected = fx_item_cat_model_min._contact
        html = BeautifulSoup(render_item_catalogue(fx_item_cat_model_min), parser="html.parser", features="lxml")

        assert html.select_one("#contact-email").text == expected.email

        phone = html.select_one("#contact-phone")
        if expected.phone:
            assert phone.text == expected.phone
        else:
            assert phone is None

        post = html.select_one("#contact-post")
        if expected.address:
            assert post.text == expected.address
        else:
            assert post is None


class TestAdminTab:
    """Test admin tab template macros."""

    def test_enabled(self, fx_item_cat_model_min: ItemCatalogue):
        """Can get admin tab (always enabled in secure contexts)."""
        html = BeautifulSoup(render_item_catalogue(fx_item_cat_model_min), parser="html.parser", features="lxml")

        assert html.select_one("#tab-content-admin") is not None

    def test_id(self, fx_item_cat_model_min: ItemCatalogue):
        """Can get item id based on value from item."""
        expected = fx_item_cat_model_min._admin.item_id
        html = BeautifulSoup(render_item_catalogue(fx_item_cat_model_min), parser="html.parser", features="lxml")

        assert html.select_one("#admin-id").text.strip() == expected

    def test_revision_link(self, fx_item_cat_model_min: ItemCatalogue):
        """Can get link to record revision based on values from item."""
        # realistic values needed over 'x' so substrings can be extracted safely
        fx_item_cat_model_min._record = deepcopy(fx_item_cat_model_min._record)
        fx_item_cat_model_min.file_identifier = "ee21f4a7-7e87-4074-b92f-9fa27a68d26d"
        fx_item_cat_model_min.file_revision = "3401c9880d4bc42aed8dabd7b41acec8817a293a"

        html = BeautifulSoup(render_item_catalogue(fx_item_cat_model_min), parser="html.parser", features="lxml")

        link = html.select_one("#admin-revision")
        assert link.select_one("a") is not None

    @pytest.mark.parametrize(
        "value",
        [
            [],
            [
                "https://gitlab.data.bas.ac.uk/MAGIC/x/-/issues/123",
                "https://gitlab.data.bas.ac.uk/MAGIC/x/-/issues/234",
            ],
        ],
    )
    def test_issues(self, fx_item_cat_model_min: ItemCatalogue, value: list[str]):
        """Can get optional item GitLab issues based on value from item."""
        admin_meta = get_admin(keys=fx_item_cat_model_min._admin_keys, record=fx_item_cat_model_min._record)
        admin_meta.gitlab_issues = value
        set_admin(keys=fx_item_cat_model_min._admin_keys, record=fx_item_cat_model_min._record, admin_meta=admin_meta)
        expected = fx_item_cat_model_min._admin.gitlab_issues
        html = BeautifulSoup(render_item_catalogue(fx_item_cat_model_min), parser="html.parser", features="lxml")

        issues = html.select_one("#admin-issues")
        if expected:
            for item in expected:
                assert item.value in issues.find(name="a", href=item.href).get_text()
        else:
            assert issues is None

    @pytest.mark.parametrize(("restricted", "expected"), [(True, "Yes"), (False, "No")])
    def test_restricted(
        self,
        fx_item_cat_model_min: ItemCatalogue,
        fx_item_cat_model_open: ItemCatalogue,
        restricted: bool,
        expected: str,
    ):
        """Can get item restriction status based on value from item."""
        model = fx_item_cat_model_min if restricted else fx_item_cat_model_open
        html = BeautifulSoup(render_item_catalogue(model), parser="html.parser", features="lxml")

        result = html.select_one("#admin-restricted")
        assert result.text.strip() == expected

    @pytest.mark.parametrize(
        ("value", "expected"), [(AccessLevel.NONE, "NONE"), (AccessLevel.PUBLIC, "Public (Open Access)")]
    )
    def test_access_level(self, fx_item_cat_model_min: ItemCatalogue, value: AccessLevel, expected: str):
        """Can get item access level based on value from item."""
        if value == AccessLevel.PUBLIC:
            admin_meta = get_admin(keys=fx_item_cat_model_min._admin_keys, record=fx_item_cat_model_min._record)
            admin_meta.access_permissions = [OPEN_ACCESS]
            set_admin(
                keys=fx_item_cat_model_min._admin_keys, record=fx_item_cat_model_min._record, admin_meta=admin_meta
            )
        html = BeautifulSoup(render_item_catalogue(fx_item_cat_model_min), parser="html.parser", features="lxml")

        result = html.select_one("#admin-level")
        assert result.text.strip() == str(expected)

    @pytest.mark.parametrize("value", [AccessLevel.NONE, AccessLevel.PUBLIC])
    def test_access_permissions(self, fx_item_cat_model_min: ItemCatalogue, value: list[Permission]):
        """Can get item access permissions based on value from item."""
        if value == AccessLevel.PUBLIC:
            admin_meta = get_admin(keys=fx_item_cat_model_min._admin_keys, record=fx_item_cat_model_min._record)
            admin_meta.access_permissions = [OPEN_ACCESS]
            set_admin(
                keys=fx_item_cat_model_min._admin_keys, record=fx_item_cat_model_min._record, admin_meta=admin_meta
            )
        expected = fx_item_cat_model_min._admin.access
        html = BeautifulSoup(render_item_catalogue(fx_item_cat_model_min), parser="html.parser", features="lxml")

        access_permissions = html.select_one("#admin-access")
        for permission in expected:
            # noinspection PyTypeChecker
            assert access_permissions.find(name="pre", string=permission) is not None
