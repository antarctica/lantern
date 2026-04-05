import pytest
from bas_metadata_library.standards.magic_administration.v1 import AdministrationMetadata, Permission
from bas_metadata_library.standards.magic_administration.v1.utils import AdministrationKeys

from lantern.lib.arcgis.gis.dataclasses import Item as ArcGisItem
from lantern.lib.arcgis.gis.enums import ItemType as ArcGisItemType
from lantern.lib.arcgis.gis.enums import SharingLevel
from lantern.lib.metadata_library.models.record.elements.common import Constraint, Constraints, Identifier, Identifiers
from lantern.lib.metadata_library.models.record.elements.data_quality import DataQuality, Lineage
from lantern.lib.metadata_library.models.record.elements.identification import GraphicOverview, GraphicOverviews
from lantern.lib.metadata_library.models.record.enums import ConstraintRestrictionCode, ConstraintTypeCode
from lantern.lib.metadata_library.models.record.utils.admin import set_admin
from lantern.models.item.arcgis.item import ArcGisItemLicenceHrefUnsupportedError, ItemArcGis
from lantern.models.item.base.enums import Licence
from lantern.models.record.record import Record


class TestItemArcGIS:
    """Test ArcGIS item representation."""

    def test_init(self, fx_record_model_min: Record, fx_lib_arcgis_item: ArcGisItem):
        """Creates an ItemArcGIS."""
        item = ItemArcGis(fx_record_model_min, arcgis_item=fx_lib_arcgis_item)

        assert item._record == fx_record_model_min
        assert item.item_id == fx_lib_arcgis_item.id

    def test_validate_snippet(self, fx_record_model_min: Record, fx_lib_arcgis_item: ArcGisItem):
        """Cannot use a record where snippet/purpose is too long."""
        fx_record_model_min.identification.purpose = "x" * 251

        with pytest.raises(ValueError, match=r"ArcGIS snippet \(summary/purpose\) is limited to 250 characters."):
            ItemArcGis(fx_record_model_min, arcgis_item=fx_lib_arcgis_item)

    @pytest.mark.cov()
    def test_title(self, fx_item_arc_model_min: ItemArcGis):
        """Can format title without Markdown."""
        fx_item_arc_model_min.record.identification.title = "_x_"
        assert fx_item_arc_model_min.title_plain == "x"

    @pytest.mark.parametrize(("lineage", "citation", "href"), [(None, None, None), ("-y-", "-z-", "-l-")])
    def test_description(
        self, fx_item_arc_model_min: ItemArcGis, lineage: str | None, citation: str | None, href: str | None
    ):
        """Can render description using template."""
        abstract = "-x-"
        # identifier included by default is never correct so always remove
        fx_item_arc_model_min.record.identification.identifiers = Identifiers([])

        fx_item_arc_model_min.record.identification.abstract = abstract
        if citation is not None:
            fx_item_arc_model_min.record.identification.other_citation_details = citation
        if href is not None:
            fx_item_arc_model_min.record.identification.identifiers = Identifiers(
                [Identifier(identifier="x", href=href, namespace="data.bas.ac.uk")]
            )
        if lineage is not None:
            fx_item_arc_model_min.record.data_quality = DataQuality(lineage=Lineage(statement=lineage))

        result = fx_item_arc_model_min._description

        assert abstract in result
        if lineage is not None:
            assert lineage in result
        else:
            assert "<h5>Lineage</h5>" not in result
        if citation is not None:
            assert citation in result
        else:
            assert "<h5>Citation</h5>" not in result
        if href is not None:
            assert href in result
        else:
            assert "<h5>Further Information</h5>" not in result

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            (
                "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/",
                "Open Government Licence (OGL 3.0)",
            ),
            (None, None),
        ],
    )
    def test_terms_of_use(self, fx_item_arc_model_min: ItemArcGis, value: str | None, expected: str | None):
        """Can render terms of use from a template."""
        if value is not None:
            fx_item_arc_model_min.record.identification.constraints = Constraints(
                [
                    Constraint(
                        type=ConstraintTypeCode.USAGE, restriction_code=ConstraintRestrictionCode.LICENSE, href=value
                    )
                ]
            )

        result = fx_item_arc_model_min._terms_of_use
        if expected is not None:
            assert expected in result
        else:
            assert result is None

    def test_terms_of_use_unknown(self, fx_item_arc_model_min: ItemArcGis):
        """Can't render terms of use from an unsupported licence."""
        fx_item_arc_model_min.record.identification.constraints = Constraints(
            [
                Constraint(
                    type=ConstraintTypeCode.USAGE,
                    restriction_code=ConstraintRestrictionCode.LICENSE,
                    href=Licence.X_ALL_RIGHTS_RESERVED_1.value,
                )
            ]
        )

        with pytest.raises(ArcGisItemLicenceHrefUnsupportedError):
            _ = fx_item_arc_model_min._terms_of_use

    @pytest.mark.cov()
    def test_item_id(self, fx_item_arc_model_min: ItemArcGis, fx_lib_arcgis_item: ArcGisItem):
        """Can get the ArcGIS Item ID."""
        assert fx_item_arc_model_min.item_id == fx_lib_arcgis_item.id

    @pytest.mark.cov()
    def test_item_type(self, fx_item_arc_model_min: ItemArcGis, fx_lib_arcgis_item: ArcGisItem):
        """Can get the ArcGIS Item type/resource."""
        assert fx_item_arc_model_min.item_type == fx_lib_arcgis_item.properties.item_type

    @pytest.mark.parametrize(
        ("permissions", "expected"),
        [
            ([], SharingLevel.PRIVATE),
            ([Permission(directory="*", group="*")], SharingLevel.EVERYONE),
            ([Permission(directory="~nerc", group="~bas-staff")], SharingLevel.ORG),
            ([Permission(directory="x", group="x"), Permission(directory="y", group="y")], SharingLevel.PRIVATE),
        ],
    )
    def test_sharing_level(
        self,
        fx_item_arc_model_min: ItemArcGis,
        fx_admin_meta_keys: AdministrationKeys,
        permissions: list[Permission],
        expected: SharingLevel,
    ):
        """Can get the ArcGIS sharing level for access level."""
        admin = AdministrationMetadata(
            id=fx_item_arc_model_min.record.file_identifier, resource_permissions=permissions
        )
        set_admin(keys=fx_admin_meta_keys, record=fx_item_arc_model_min.record, admin_meta=admin)
        item = ItemArcGis(
            record=fx_item_arc_model_min.record,
            admin_meta_keys=fx_admin_meta_keys,
            arcgis_item=fx_item_arc_model_min.item,
        )

        assert item.sharing_level == expected

    def test_metadata(self, fx_item_arc_model_min: ItemArcGis):
        """Can get ArcGIS item metadata."""
        expected = (
            f"<metadata><mdFileID>{fx_item_arc_model_min.record.file_identifier}</mdFileID><dataIdInfo/></metadata>"
        )
        assert expected == fx_item_arc_model_min._metadata

    @pytest.mark.parametrize(
        "value", [GraphicOverviews([GraphicOverview(identifier="overview-agol", href="x", mime_type="x")]), None]
    )
    def test_thumbnail_href(self, fx_item_arc_model_min: ItemArcGis, value: GraphicOverviews | None):
        """Can get URL to optional item thumbnail."""
        expected = None
        if value is not None:
            fx_item_arc_model_min.record.identification.graphic_overviews = value
            expected = value[0].href

        if value is not None:
            assert fx_item_arc_model_min.thumbnail_href == expected
        else:
            assert fx_item_arc_model_min.thumbnail_href is None

    @pytest.mark.parametrize(
        ("purpose", "identifiers", "constraints", "lineage"),
        [
            (
                "x",
                Identifiers([Identifier(identifier="x", href="x", namespace="data.bas.ac.uk")]),
                Constraints(
                    [
                        Constraint(
                            type=ConstraintTypeCode.USAGE,
                            restriction_code=ConstraintRestrictionCode.LICENSE,
                            href="https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/",
                        )
                    ]
                ),
                "x",
            ),
            (None, None, None, None),
        ],
    )
    def test_item_properties(
        self,
        fx_item_arc_model_min: ItemArcGis,
        purpose: str | None,
        identifiers: Identifiers | None,
        constraints: Constraints | None,
        lineage: str | None,
    ):
        """Can get combined ArcGIS item properties."""
        expected = "x"
        fx_item_arc_model_min.record.identification.title = expected
        fx_item_arc_model_min.record.identification.abstract = expected
        if purpose is not None:
            fx_item_arc_model_min.record.identification.purpose = purpose
        if identifiers is not None:
            fx_item_arc_model_min.record.identification.identifiers = identifiers
        if constraints is not None:
            fx_item_arc_model_min.record.identification.constraints = constraints
        if lineage is not None:
            fx_item_arc_model_min.record.data_quality = DataQuality(lineage=Lineage(statement=lineage))

        result = fx_item_arc_model_min.item_properties
        assert result.title == expected  # matches `arcgis_item_name` until MAGIC/esri#122 resolved
        assert result.item_type == ArcGisItemType.FEATURE_SERVICE
        assert expected in result.description
        assert result.access_information == "BAS"
        if (
            constraints is not None
            and constraints[0].href == "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/"
        ):
            assert "Open Government Licence (OGL 3.0)" in result.license_info
        assert fx_item_arc_model_min.record.file_identifier in result.metadata

    def test_item(self, fx_item_arc_model_min: ItemArcGis):
        """Can get overall ArcGIS item."""
        result = fx_item_arc_model_min.item
        assert isinstance(result, ArcGisItem)
