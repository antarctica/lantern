from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from lantern.lib.magic_distribution.arcgis.gis.enums import SharingLevel
from lantern.lib.magic_distribution.arcgis.models.artefact import ArtefactArcGisService
from lantern.lib.magic_distribution.formats import ArtefactFormatLabel, ArtefactFormats, ArtefactFormatUnknownError
from lantern.lib.metadata_library.models.record.elements.common import Contact
from lantern.lib.metadata_library.models.record.elements.distribution import Distribution, Format, TransferOption
from lantern.lib.metadata_library.models.record.enums import OnlineResourceFunctionCode

if TYPE_CHECKING:
    from lantern.lib.magic_distribution.arcgis.gis import Item as ArcGisItem


class TestArtefactArcGisService:
    """Test ArcGIS based service Artefact class."""

    format_label_item = ArtefactFormats.get_by_label(ArtefactFormatLabel.ARCGIS_FEATURE_LAYER).label
    format_label_service = ArtefactFormats.get_by_label(ArtefactFormatLabel.ARCGIS_FEATURE_SERVICE).label

    @pytest.mark.parametrize("service_label", [None, format_label_service])
    def test_init(self, fx_lib_arcgis_item: ArcGisItem, service_label: ArtefactFormatLabel | None):
        """Can create an ArcGIS item (and service) artefact."""
        artefact = ArtefactArcGisService(
            resource_id="x",
            item=fx_lib_arcgis_item,
            format_label=self.format_label_item,
            format_service_label=service_label,
        )

        assert artefact.name == "x"
        assert artefact._artefact_url == "https://www.maps.arcgis.com/home/item.html?id=x"

    @pytest.mark.cov()
    @pytest.mark.parametrize("service_label", [None, format_label_service])
    def test_repr(
        self, fx_lib_arcgis_service_artefact: ArtefactArcGisService, service_label: ArtefactFormatLabel | None
    ):
        """Can get string representation."""
        fx_lib_arcgis_service_artefact._format_service_label = service_label
        expected = (
            "<ArtefactArcGiS: x, ArcGIS Feature Layer, https://www.maps.arcgis.com/home/item.html?id=x>"
            if not service_label
            else "<ArtefactArcGiS: x, ArcGIS Feature Layer (ArcGIS Feature Service), https://www.maps.arcgis.com/home/item.html?id=x>"
        )

        assert repr(fx_lib_arcgis_service_artefact) == expected

    @pytest.mark.parametrize("service_label", [None, format_label_service])
    def test_format(
        self, fx_lib_arcgis_service_artefact: ArtefactArcGisService, service_label: ArtefactFormatLabel | None
    ):
        """Can get artefact format, and by extension format label, for item and service if applicable."""
        fx_lib_arcgis_service_artefact._format_service_label = service_label
        expected_item = ArtefactFormats.get_by_label(self.format_label_item)
        expected_service = ArtefactFormats.get_by_label(self.format_label_service) if service_label else None

        assert fx_lib_arcgis_service_artefact.format == expected_item
        assert fx_lib_arcgis_service_artefact.format_label == self.format_label_item

        assert fx_lib_arcgis_service_artefact.format_service == expected_service
        assert fx_lib_arcgis_service_artefact.format_label_service == service_label

    def test_unsupported_format(self, fx_lib_arcgis_service_artefact: ArtefactArcGisService):
        """Cannot create a valid ArcGIS artefact with an unsupported format."""
        fx_lib_arcgis_service_artefact._format_label = "invalid"
        with pytest.raises(ArtefactFormatUnknownError):
            repr(fx_lib_arcgis_service_artefact)
        with pytest.raises(ArtefactFormatUnknownError):
            fx_lib_arcgis_service_artefact.validate_format()

    @pytest.mark.parametrize("sharing_level", [SharingLevel.EVERYONE, SharingLevel.PRIVATE])
    @pytest.mark.parametrize("service_label", [None, format_label_service])
    def test_distribution(
        self,
        fx_lib_arcgis_service_artefact: ArtefactArcGisService,
        sharing_level: SharingLevel,
        service_label: ArtefactFormatLabel | None,
    ):
        """Can get ISO distribution and component elements based on artefact for item and service if applicable."""
        fx_lib_arcgis_service_artefact._format_service_label = service_label
        fx_lib_arcgis_service_artefact._item.url = "x" if service_label else None
        fx_lib_arcgis_service_artefact._item.sharing_level = sharing_level
        expected_host = "maps.arcgis.com" if sharing_level == SharingLevel.EVERYONE else "bas.maps.arcgis.com"
        expected_title = "ArcGIS Online"

        assert len(fx_lib_arcgis_service_artefact.distribution_options) >= 1

        assert isinstance(fx_lib_arcgis_service_artefact.distribution_option, Distribution)
        assert isinstance(fx_lib_arcgis_service_artefact.distributor, Contact)
        assert isinstance(fx_lib_arcgis_service_artefact.distribution_format, Format)
        assert isinstance(fx_lib_arcgis_service_artefact.distribution_transfer_opt, TransferOption)

        _online_resource = fx_lib_arcgis_service_artefact.distribution_transfer_opt.online_resource
        assert _online_resource.title == expected_title
        assert _online_resource.description == "Access information as an ArcGIS feature layer."
        assert _online_resource.href.startswith(f"https://{expected_host}")
        assert _online_resource.function == OnlineResourceFunctionCode.INFORMATION

        if service_label:
            assert len(fx_lib_arcgis_service_artefact.distribution_options) == 2  # noqa: PLR2004

            assert isinstance(fx_lib_arcgis_service_artefact.distribution_option_service, Distribution)
            assert isinstance(fx_lib_arcgis_service_artefact.distribution_format_service, Format)
            assert isinstance(fx_lib_arcgis_service_artefact.distribution_transfer_opt_service, TransferOption)

            _online_resource_service = fx_lib_arcgis_service_artefact.distribution_transfer_opt_service.online_resource
            assert _online_resource_service.title == expected_title
            assert _online_resource_service.description == "Access information as an ArcGIS feature service."
            assert _online_resource_service.href == "x"
            assert _online_resource_service.function == OnlineResourceFunctionCode.DOWNLOAD
        else:
            assert fx_lib_arcgis_service_artefact.distribution_option_service is None
            assert fx_lib_arcgis_service_artefact.distribution_format_service is None
            assert fx_lib_arcgis_service_artefact.distribution_transfer_opt_service is None

    @pytest.mark.cov()
    def test_distribution_transfer_opt_service_no_description(
        self, fx_lib_arcgis_service_artefact: ArtefactArcGisService
    ):
        """Can get ISO distribution and component elements based on artefact for item and service if applicable."""
        fx_lib_arcgis_service_artefact._item.url = "x"

        assert isinstance(fx_lib_arcgis_service_artefact.distribution_transfer_opt_service, TransferOption)
        assert fx_lib_arcgis_service_artefact.distribution_transfer_opt_service.online_resource.description is None
