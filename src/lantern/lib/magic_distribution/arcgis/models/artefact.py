from __future__ import annotations

from typing import TYPE_CHECKING

from lantern.lib.magic_distribution.arcgis.gis.enums import SharingLevel
from lantern.lib.magic_distribution.formats import ArtefactFormat, ArtefactFormatLabel, ArtefactFormats
from lantern.lib.magic_distribution.models.artefact import ArtefactService
from lantern.lib.metadata_library.models.record.elements.common import Contact, OnlineResource
from lantern.lib.metadata_library.models.record.elements.distribution import (
    Distribution,
    Distributions,
    Format,
    TransferOption,
)
from lantern.lib.metadata_library.models.record.enums import OnlineResourceFunctionCode
from lantern.lib.metadata_library.models.record.presets.contacts import ESRI_DISTRIBUTOR

if TYPE_CHECKING:
    from lantern.lib.magic_distribution.arcgis.gis.dataclasses import Item as ArcGisItem


class ArtefactArcGisService(ArtefactService):
    """
    Artefact representing an ArcGIS item.

    Represents both ArcGIS Portal items (web maps, etc.), and their underlying ArcGIS Server services
    (Feature Services, etc.) if applicable.
    """

    def __init__(
        self,
        resource_id: str,
        item: ArcGisItem,
        format_label: ArtefactFormatLabel,
        format_service_label: ArtefactFormatLabel | None = None,
    ) -> None:
        name = item.properties.title
        endpoint = f"https://www.maps.arcgis.com/home/item.html?id={item.id}"
        super().__init__(resource_id=resource_id, artefact_name=name, artefact_url=endpoint)
        self._item = item
        self._format_label = format_label
        self._format_service_label = format_service_label

    def __repr__(self) -> str:
        """Class representation."""
        _service_format = f" ({self.format_service.name})" if self.format_service else ""
        return f"<ArtefactArcGiS: {self.name}, {self.format.name}{_service_format}, {self._artefact_url}>"

    @property
    def format(self) -> ArtefactFormat:
        """
        Artefact format for item.

        From stated format label.

        This should be determined upstream, from the Portal item type and item type keywords properties.
        """
        return ArtefactFormats.get_by_label(self._format_label)

    @property
    def format_service(self) -> ArtefactFormat | None:
        """
        Artefact format, for underlying service if applicable.

        From stated (optional) format_service label.

        This should be determined upstream, from URL path fragments and (annoyingly) the capabilities data property.
        """
        _label = self._format_service_label
        return ArtefactFormats.get_by_label(_label) if _label else None

    @property
    def format_label(self) -> ArtefactFormatLabel:
        """
        Artefact format label for item.

        For the ArcGIS Portal item.
        """
        return super().format_label

    @property
    def format_label_service(self) -> ArtefactFormatLabel | None:
        """
        Artefact format label, for underlying service if applicable.

        For the underlying ArcGIS Server service, if applicable.
        """
        return self.format_service.label if self.format_service else None

    @property
    def distribution_format(self) -> Format | None:
        """
        Artefact format for item as an ISO distribution format.

        For the ArcGIS Portal item.
        """
        return super().distribution_format

    @property
    def distribution_format_service(self) -> Format | None:
        """
        Artefact format, for underlying service, as an ISO distribution format, if applicable.

        For the underlying ArcGIS Server service.
        """
        if not self.format_service:
            return None
        return Format(format=self.format_service.name, href=self.format_service.registration)

    @property
    def distributor(self) -> Contact:
        """
        Artefact ISO distributor.

        Static value for both items and optional services.
        """
        return ESRI_DISTRIBUTOR

    @property
    def distribution_transfer_opt(self) -> TransferOption:
        """Artefact ISO transfer option for item."""
        href_host = "maps.arcgis.com" if self._item.sharing_level == SharingLevel.EVERYONE else "bas.maps.arcgis.com"
        href = f"https://{href_host}/home/item.html?id={self._item.id}"

        description_mapping = {
            ArtefactFormatLabel.ARCGIS_FEATURE_LAYER: "Access information as an ArcGIS feature layer.",
            ArtefactFormatLabel.ARCGIS_OGC_FEATURES_LAYER: "Access information as an ArcGIS OGC feature layer.",
            ArtefactFormatLabel.ARCGIS_RASTER_TILE_LAYER: "Access information as an ArcGIS raster tile layer.",
            ArtefactFormatLabel.ARCGIS_VECTOR_TILE_LAYER: "Access information as an ArcGIS vector tile layer.",
            ArtefactFormatLabel.ARCGIS_WEB_SCENE: "Access information as an ArcGIS web scene.",
            ArtefactFormatLabel.ARCGIS_WEB_MAP: "Access information as an ArcGIS web map",
        }
        description = description_mapping[self.format_label]

        return TransferOption(
            online_resource=OnlineResource(
                href=href,
                title="ArcGIS Online",
                description=description,
                function=OnlineResourceFunctionCode.INFORMATION,
            )
        )

    @property
    def distribution_transfer_opt_service(self) -> TransferOption | None:
        """Artefact ISO transfer option for underlying service if applicable."""
        if not self._item.url:
            return None

        description_mapping = {
            ArtefactFormatLabel.ARCGIS_FEATURE_SERVICE: "Access information as an ArcGIS feature service.",
            ArtefactFormatLabel.ARCGIS_OGC_FEATURES_SERVICE: "Access information as an OGC API feature service.",
            ArtefactFormatLabel.ARCGIS_RASTER_TILE_SERVICE: "Access information as an ArcGIS raster tile service.",
            ArtefactFormatLabel.ARCGIS_VECTOR_TILE_SERVICE: "Access information as an ArcGIS vector tile service.",
        }
        description = None
        if self.format_label_service:
            description = description_mapping[self.format_label_service]

        return TransferOption(
            online_resource=OnlineResource(
                href=self._item.url,
                title="ArcGIS Online",
                description=description,
                function=OnlineResourceFunctionCode.DOWNLOAD,
            )
        )

    @property
    def distribution_option(self) -> Distribution:
        """Artefact ISO distribution option for item."""
        return Distribution(
            format=self.distribution_format,
            distributor=self.distributor,
            transfer_option=self.distribution_transfer_opt,
        )

    @property
    def distribution_option_service(self) -> Distribution | None:
        """Artefact ISO transfer option for underlying service if applicable."""
        if not self.distribution_transfer_opt_service:
            return None
        return Distribution(
            format=self.distribution_format_service,
            distributor=self.distributor,
            transfer_option=self.distribution_transfer_opt_service,
        )

    @property
    def distribution_options(self) -> Distributions:
        """Combination of artefact ISO distribution options for item and underlying service if applicable."""
        _service_opt = self.distribution_option_service
        if not _service_opt:
            return Distributions([self.distribution_option])
        return Distributions([self.distribution_option, _service_opt])

    def validate_format(self) -> None:
        """
        Check file is a supported type.

        May raise `ArtefactFormatUnknownError` if unknown.
        """
        ArtefactFormats.get_by_label(self._format_label)
