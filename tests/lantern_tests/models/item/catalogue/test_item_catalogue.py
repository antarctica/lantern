import json
from datetime import UTC, datetime

import pytest

from lantern.config import Config
from lantern.lib.metadata_library.models.record import Record
from lantern.lib.metadata_library.models.record.elements.common import (
    Contact,
    ContactIdentity,
    Contacts,
    Date,
    Identifiers,
)
from lantern.lib.metadata_library.models.record.elements.identification import GraphicOverview, GraphicOverviews
from lantern.lib.metadata_library.models.record.enums import ContactRoleCode
from lantern.models.item.base.const import CATALOGUE_NAMESPACE
from lantern.models.item.base.elements import Link
from lantern.models.item.base.enums import ResourceTypeLabel
from lantern.models.item.catalogue import ItemCatalogue, ItemInvalidError
from lantern.models.item.catalogue.elements import PageSummary
from lantern.models.item.catalogue.tabs import (
    AdditionalInfoTab,
    AuthorsTab,
    ContactTab,
    DataTab,
    ExtentTab,
    ItemsTab,
    LicenceTab,
    LineageTab,
    RelatedTab,
)
from lantern.models.record.revision import RecordRevision
from tests.conftest import _get_record


class TestItemCatalogue:
    """Test catalogue item."""

    def test_init(self, fx_config: Config, fx_record_minimal_item_catalogue: Record):
        """Can create an ItemCatalogue."""
        item = ItemCatalogue(
            config=fx_config,
            record=fx_record_minimal_item_catalogue,
            get_record=_get_record,
        )
        assert isinstance(item, ItemCatalogue)
        assert item._record == fx_record_minimal_item_catalogue

    @pytest.mark.parametrize(
        ("element", "exception_cls"),
        [
            ("file_identifier", ValueError),
            ("self_identifier", ItemInvalidError),
            ("self_identifier_match", ItemInvalidError),
            ("self_identifier_namespace", ItemInvalidError),
            ("point_of_contact", ItemInvalidError),
        ],
    )
    def test_invalid(
        self,
        fx_config: Config,
        fx_record_minimal_item_catalogue: Record,
        element: str,
        exception_cls: type[Exception],
    ):
        """Cannot create a catalogue item from an invalid record."""
        if element == "file_identifier":
            fx_record_minimal_item_catalogue.file_identifier = None
        elif element == "self_identifier":
            fx_record_minimal_item_catalogue.identification.identifiers = Identifiers([])
        elif element == "self_identifier_match":
            fx_record_minimal_item_catalogue.identification.identifiers[0].identifier = "y"
        elif element == "self_identifier_namespace":
            fx_record_minimal_item_catalogue.identification.identifiers[0].namespace = "y"
        elif element == "point_of_contact":
            fx_record_minimal_item_catalogue.identification.contacts = Contacts([])

        with pytest.raises(exception_cls):
            _ = ItemCatalogue(
                config=fx_config,
                record=fx_record_minimal_item_catalogue,
                get_record=_get_record,
            )

    @pytest.mark.parametrize("has_revision", [False, True])
    def test_revision(
        self,
        fx_config: Config,
        fx_item_catalogue_min: ItemCatalogue,
        fx_record_revision_minimal_item_catalogue: RecordRevision,
        has_revision: bool,
    ):
        """Can compute link to record revision where available."""
        expected = None

        # realistic values needed over 'x' so substrings can be extracted safely
        id_ = "ee21f4a7-7e87-4074-b92f-9fa27a68d26d"
        commit = "3401c9880d4bc42aed8dabd7b41acec8817a293a"

        if has_revision:
            fx_record_revision_minimal_item_catalogue.file_identifier = id_
            fx_record_revision_minimal_item_catalogue.file_revision = commit
            fx_item_catalogue_min._record = fx_record_revision_minimal_item_catalogue
            href = f"{fx_config.TEMPLATES_ITEM_VERSIONS_ENDPOINT}/-/blob/{commit}/records/ee/21/{id_}.json"
            expected = Link(value="3401c988", href=href, external=True)

        assert fx_item_catalogue_min._revision == expected

    def test_html_title(self, fx_item_catalogue_min: ItemCatalogue):
        """Can get HTML title."""
        expected = "x | BAS Data Catalogue"
        fx_item_catalogue_min._record.identification.title = "_x_"

        assert fx_item_catalogue_min.page_metadata.html_title == expected

    @pytest.mark.parametrize(
        ("summary", "published", "graphics"),
        [
            (None, False, GraphicOverviews([])),
            ("x", True, GraphicOverviews([GraphicOverview(identifier="x", href="x", mime_type="x")])),
            ("x", True, GraphicOverviews([GraphicOverview(identifier="overview", href="x", mime_type="x")])),
        ],
    )
    def test_html_open_graph(
        self,
        fx_config: Config,
        fx_item_catalogue_min: ItemCatalogue,
        summary: str | None,
        published: bool,
        graphics: GraphicOverviews,
    ):
        """Can get HTML open graph tags."""
        expected = {
            "og:locale": "en_GB",
            "og:site_name": "BAS Data Catalogue",
            "og:type": "article",
            "og:title": fx_item_catalogue_min.title_plain,
            "og:url": f"{fx_config.BASE_URL}/items/{fx_item_catalogue_min.resource_id}",
        }

        if summary is not None:
            fx_item_catalogue_min._record.identification.purpose = summary
            expected["og:description"] = summary

        if published:
            date_ = Date(date=datetime(2014, 6, 30, tzinfo=UTC).date())
            fx_item_catalogue_min._record.identification.dates.publication = date_
            expected["og:article:published_time"] = date_.date.isoformat()

        fx_item_catalogue_min._record.identification.graphic_overviews = graphics
        if fx_item_catalogue_min.overview_graphic is not None:
            expected["og:image"] = fx_item_catalogue_min.overview_graphic.href

        assert fx_item_catalogue_min.page_metadata.html_open_graph == expected

    @pytest.mark.parametrize(
        ("summary", "graphics", "contacts", "contacts_exp"),
        [
            (None, GraphicOverviews([]), Contacts([]), None),
            (
                "x",
                GraphicOverviews([GraphicOverview(identifier="x", href="x", mime_type="x")]),
                Contacts([Contact(organisation=ContactIdentity(name="x"), role=[ContactRoleCode.POINT_OF_CONTACT])]),
                None,
            ),
            (
                None,
                GraphicOverviews([GraphicOverview(identifier="overview", href="x", mime_type="x")]),
                Contacts([Contact(organisation=ContactIdentity(name="x"), role=[ContactRoleCode.AUTHOR])]),
                "x",
            ),
            (
                None,
                GraphicOverviews([]),
                Contacts(
                    [
                        Contact(individual=ContactIdentity(name="x"), role=[ContactRoleCode.AUTHOR]),
                        Contact(individual=ContactIdentity(name="y"), role=[ContactRoleCode.AUTHOR]),
                    ]
                ),
                "x & y",
            ),
            (
                None,
                GraphicOverviews([]),
                Contacts(
                    [
                        Contact(individual=ContactIdentity(name="x"), role=[ContactRoleCode.AUTHOR]),
                        Contact(individual=ContactIdentity(name="y"), role=[ContactRoleCode.AUTHOR]),
                        Contact(individual=ContactIdentity(name="z"), role=[ContactRoleCode.AUTHOR]),
                    ]
                ),
                "x, y & z",
            ),
        ],
    )
    def test_html_schema_org(
        self,
        fx_config: Config,
        fx_item_catalogue_min: ItemCatalogue,
        summary: str | None,
        graphics: GraphicOverviews,
        contacts: Contacts,
        contacts_exp: str | None,
    ):
        """Can get HTML open graph tags."""
        expected = {
            "@context": "http://schema.org/",
            "@type": "Article",
            "name": "BAS Data Catalogue",
            "headline": fx_item_catalogue_min.title_plain,
            "url": f"{fx_config.BASE_URL}/items/{fx_item_catalogue_min.resource_id}",
        }

        if summary is not None:
            fx_item_catalogue_min._record.identification.purpose = summary
            expected["description"] = summary

        fx_item_catalogue_min._record.identification.graphic_overviews = graphics
        if fx_item_catalogue_min.overview_graphic is not None:
            expected["image"] = fx_item_catalogue_min.overview_graphic.href

        fx_item_catalogue_min._record.identification.contacts = contacts
        if contacts_exp is not None:
            expected["creator"] = contacts_exp

        assert fx_item_catalogue_min.page_metadata.html_schema_org == json.dumps(expected, indent=2)

    def test_page_header(self, fx_item_catalogue_min: ItemCatalogue):
        """Can get page header element."""
        fx_item_catalogue_min._record.identification.title = "_x_"
        expected_title = "<em>x</em>"
        expected_type = ResourceTypeLabel[fx_item_catalogue_min._record.hierarchy_level.name].value

        assert fx_item_catalogue_min.page_header.title == expected_title
        assert fx_item_catalogue_min.page_header.subtitle[0] == expected_type

    def test_summary(self, fx_item_catalogue_min: ItemCatalogue):
        """
        Can get summary element.

        Summary element is checked in more detail in catalogue element tests.
        """
        assert isinstance(fx_item_catalogue_min.summary, PageSummary)

    def test_tabs(self, fx_item_catalogue_min: ItemCatalogue):
        """Can get list of tabs."""
        assert isinstance(fx_item_catalogue_min.tabs[0], ItemsTab)
        assert isinstance(fx_item_catalogue_min.tabs[1], DataTab)
        assert isinstance(fx_item_catalogue_min.tabs[2], AuthorsTab)
        assert isinstance(fx_item_catalogue_min.tabs[3], LicenceTab)
        assert isinstance(fx_item_catalogue_min.tabs[4], ExtentTab)
        assert isinstance(fx_item_catalogue_min.tabs[5], LineageTab)
        assert isinstance(fx_item_catalogue_min.tabs[6], RelatedTab)
        assert isinstance(fx_item_catalogue_min.tabs[7], AdditionalInfoTab)
        assert isinstance(fx_item_catalogue_min.tabs[8], ContactTab)

    base_record = {  # noqa: RUF012
        "$schema": "https://metadata-resources.data.bas.ac.uk/bas-metadata-generator-configuration-schemas/v2/iso-19115-2-v4.json",
        "file_identifier": "x",
        "hierarchy_level": "dataset",
        "metadata": {
            "contacts": [{"organisation": {"name": "x"}, "role": ["pointOfContact"]}],
            "date_stamp": datetime(2014, 6, 30, tzinfo=UTC).date().isoformat(),
        },
        "identification": {
            "title": {"value": "x"},
            "dates": {"creation": "2014-06-30"},
            "abstract": "x",
        },
    }

    @pytest.mark.parametrize(
        ("values", "anchor"),
        [
            (
                {
                    **base_record,
                    "identification": {
                        **base_record["identification"],
                        "aggregations": [
                            {
                                "identifier": {"identifier": "x", "href": "x", "namespace": CATALOGUE_NAMESPACE},
                                "association_type": "isComposedOf",
                                "initiative_type": "collection",
                            }
                        ],
                    },
                },
                "items",
            ),
            (
                {
                    **base_record,
                    "distribution": [
                        {
                            "distributor": {"organisation": {"name": "x"}, "role": ["distributor"]},
                            "format": {
                                "format": "x",
                                "href": "https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+layer+feature",
                            },
                            "transfer_option": {
                                "online_resource": {"href": "x", "function": "download"},
                            },
                        },
                        {
                            "distributor": {"organisation": {"name": "x"}, "role": ["distributor"]},
                            "format": {
                                "format": "x",
                                "href": "https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+service+feature",
                            },
                            "transfer_option": {
                                "online_resource": {"href": "x", "function": "download"},
                            },
                        },
                    ],
                },
                "data",
            ),
            (
                {
                    **base_record,
                    "identification": {
                        **base_record["identification"],
                        "contacts": [{"individual": {"name": "x"}, "role": ["author"]}],
                    },
                },
                "authors",
            ),
            (
                {
                    **base_record,
                    "identification": {
                        **base_record["identification"],
                        "constraints": [
                            {"type": "usage", "restriction_code": "license", "statement": "x", "href": "x"}
                        ],
                    },
                },
                "licence",
            ),
            (
                {
                    **base_record,
                    "identification": {
                        **base_record["identification"],
                        "extents": [
                            {
                                "identifier": "bounding",
                                "geographic": {
                                    "bounding_box": {
                                        "west_longitude": 1.0,
                                        "east_longitude": 1.0,
                                        "south_latitude": 1.0,
                                        "north_latitude": 1.0,
                                    }
                                },
                            }
                        ],
                    },
                },
                "extent",
            ),
            (
                {
                    **base_record,
                    "identification": {
                        **base_record["identification"],
                        "lineage": {"statement": "x"},
                    },
                },
                "lineage",
            ),
            (
                {
                    **base_record,
                    "identification": {
                        **base_record["identification"],
                        "aggregations": [
                            {
                                "identifier": {"identifier": "x", "href": "x", "namespace": CATALOGUE_NAMESPACE},
                                "association_type": "largerWorkCitation",
                                "initiative_type": "collection",
                            }
                        ],
                    },
                },
                "related",
            ),
            (
                base_record,
                "info",
            ),
        ],
    )
    def test_default_tab_anchor(self, fx_item_catalogue_min: ItemCatalogue, values: dict, anchor: str):
        """Can get default tab anchor depending on enabled tabs."""
        record = Record.loads(values)
        fx_item_catalogue_min._record = record

        assert fx_item_catalogue_min.default_tab_anchor == anchor

    def test_render(self, fx_item_catalogue_min: ItemCatalogue):
        """
        Can render template for item.

        This is a basic sanity check that the template can be rendered without error.
        It does not check the content of the rendered template in any detail.
        """
        assert fx_item_catalogue_min.render() != ""
