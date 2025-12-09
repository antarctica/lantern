import base64
import re
from abc import ABC, abstractmethod
from typing import Any
from urllib.parse import unquote, urlparse

from humanize import naturalsize

from lantern.lib.metadata_library.models.record.elements.distribution import Distribution as RecordDistribution
from lantern.models.item.base.elements import Link
from lantern.models.item.catalogue.enums import DistributionType


class Distribution(ABC):
    """
    Item Catalogue Distribution.

    Represents a distribution type supported by the BAS Data Catalogue. Types include both file downloads and services.
    Some types are composites, combing multiple Record distributions into a single Item distribution.

    Classes use a `matches()` class method to determine if a Record has the required distribution options.
    """

    @classmethod
    @abstractmethod
    def matches(cls, option: RecordDistribution, other_options: list[RecordDistribution]) -> bool:
        """Whether this class matches the distribution option."""
        ...

    @staticmethod
    def _encode_url(url: str) -> str:
        """
        Encode URL for use as a DOM selector.

        Base64 encodes URL and removes any non-alphanumeric characters.
        """
        return re.sub(r"\W", "", base64.b64encode(url.encode("utf-8")).decode("utf-8"))

    @property
    @abstractmethod
    def format_type(self) -> DistributionType:
        """
        Format type including label.

        No longer shown in item template but retained for future use.
        """
        ...

    @property
    @abstractmethod
    def label(self) -> str:
        """Distinguishing identifier."""
        ...

    @property
    @abstractmethod
    def description(self) -> str | None:
        """
        Optional hint or additional context.

        Values are not visible on mobile due to using a hover tooltip.
        For detailed information, use an action that opens an info box or similar.
        """
        ...

    @property
    @abstractmethod
    def size(self) -> str:
        """Size if applicable."""
        ...

    @property
    @abstractmethod
    def action(self) -> Link:
        """
        Link to distribution if applicable.

        Where an `access_trigger` is set, the returned `Link.href` should be set to None.
        """
        ...

    @property
    def action_btn_variant(self) -> str:
        """
        Variant of button to display for action link or trigger.

        See https://style-kit.web.bas.ac.uk/core/buttons/#variants for available variants.
        """
        return "default"

    @property
    def action_btn_variant_restricted(self) -> str:
        """
        Variant of button to display for action link or trigger in a restricted context.

        See https://style-kit.web.bas.ac.uk/core/buttons/#variants for available variants.
        """
        return "warning"

    @property
    @abstractmethod
    def action_btn_icon(self) -> str:
        """
        Font Awesome icon classes to display in action link or trigger.

        See https://fontawesome.com/v5/search?o=r&s=regular for choices (in available version and recommended style).
        """
        ...

    @property
    def action_btn_icon_restricted(self) -> str:
        """
        Font Awesome icon classes to display in action link or trigger in a restricted context.

        See https://fontawesome.com/v5/search?o=r&s=regular for choices (in available version and recommended style).
        """
        return "far fa-lock-alt"

    @property
    @abstractmethod
    def access_target(self) -> str | None:
        """Optional DOM selector of element showing more information on accessing distribution."""
        ...


class ArcGISDistribution(Distribution, ABC):
    """
    Base (abstract) ArcGIS distribution option.

    Represents common properties of ArcGIS distribution types supported by the BAS Data Catalogue.
    """

    def __init__(
        self,
        option: RecordDistribution,
        other_options: list[RecordDistribution],
        service_media_href: str,
        **kwargs: Any,
    ) -> None:
        self._layer = option
        self._service = self._get_service_option(other_options, service_media_href)

    @staticmethod
    def _get_service_option(options: list[RecordDistribution], target_href: str) -> RecordDistribution:
        """Get corresponding service option for layer."""
        try:
            return next(option for option in options if option.format is not None and option.format.href == target_href)
        except StopIteration:
            msg = "Required corresponding service option not found in resource distributions."
            raise ValueError(msg) from None

    @staticmethod
    def _matches(target_hrefs: list[str], option: RecordDistribution, other_options: list[RecordDistribution]) -> bool:
        """Whether this class matches the distribution option."""
        if option.format is None or option.format.href is None:
            return False

        item_hrefs = [
            option.format.href
            for option in [option, *other_options]
            if option.format is not None and option.format.href is not None
        ]
        match = all(href in item_hrefs for href in target_hrefs)
        # avoid matching for each target href by only returning True if the first target matches
        return match and option.format.href == target_hrefs[0]

    @property
    def label(self) -> str:
        """Generic label based on layer type."""
        return self.format_type.value

    @property
    def description(self) -> None:
        """Not applicable as info box provides additional context."""
        return None

    @property
    def size(self) -> str:
        """Not applicable."""
        return ""

    @property
    def item_link(self) -> Link:
        """Link to portal item."""
        href = self._layer.transfer_option.online_resource.href
        return Link(value=href, href=href, external=True)

    @property
    def service_endpoint(self) -> str:
        """Link to service endpoint."""
        return self._service.transfer_option.online_resource.href

    @property
    def action(self) -> Link:
        """Link to distribution without href due to using `access_trigger`."""
        return Link(value="Add to GIS", href=None)

    @property
    def action_btn_variant(self) -> str:
        """Action button variant."""
        return "primary"

    @property
    def action_btn_icon(self) -> str:
        """Action button icon classes."""
        return "far fa-layer-plus"

    @property
    def access_target(self) -> str:
        """DOM selector of element showing more information on accessing layer."""
        return f"#item-data-info-{self._encode_url(self.item_link.href)}"


class FileDistribution(Distribution, ABC):
    """
    Base (abstract) file based distribution option.

    Represents common properties of file based distribution types supported by the BAS Data Catalogue.
    """

    def __init__(self, option: RecordDistribution, restricted: bool, **kwargs: Any) -> None:
        self._option = option
        self._restricted = restricted

    @property
    def label(self) -> str:
        """Distinguishing identifier from transfer option if available, or generic value based on file type."""
        title = self._option.transfer_option.online_resource.title
        return title if title else self.format_type.value

    @property
    def description(self) -> str | None:
        """Optional hint or additional context."""
        return self._option.transfer_option.online_resource.description

    @property
    def size(self) -> str:
        """Size if known."""
        size = self._option.transfer_option.size
        if size is None:
            return ""
        if size.unit == "bytes":
            return naturalsize(size.magnitude)
        return f"{size.magnitude} {size.unit}"

    @property
    def action(self) -> Link:
        """Link to resource artefact."""
        return Link(value="Download", href=self._option.transfer_option.online_resource.href)

    @property
    def action_btn_variant(self) -> str:
        """Variant of button to display for action link based on resource access."""
        return super().action_btn_variant if not self._restricted else super().action_btn_variant_restricted

    @property
    def action_btn_icon(self) -> str:
        """Action button icon classes."""
        return "far fa-download" if not self._restricted else super().action_btn_icon_restricted

    @property
    def access_target(self) -> None:
        """Not applicable for files."""
        return None


class ArcGisFeatureLayer(ArcGISDistribution):
    """
    ArcGIS Feature Layer distribution option.

    Consisting of a Feature Service and Feature Layer option.
    """

    def __init__(self, option: RecordDistribution, other_options: list[RecordDistribution], **kwargs: Any) -> None:
        service_media_href = "https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+service+feature"
        super().__init__(option, other_options, service_media_href, **kwargs)

    @classmethod
    def matches(cls, option: RecordDistribution, other_options: list[RecordDistribution]) -> bool:
        """Whether this class matches the distribution option."""
        target_hrefs = [
            "https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+layer+feature",
            "https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+service+feature",
        ]
        return ArcGisFeatureLayer._matches(target_hrefs=target_hrefs, option=option, other_options=other_options)

    @property
    def format_type(self) -> DistributionType:
        """Format type."""
        return DistributionType.ARCGIS_FEATURE_LAYER


class ArcGisOgcApiFeatures(ArcGISDistribution):
    """
    ArcGIS OGC API Features distribution option.

    Represents an ArcGIS specific implementation of the OGC API Features standard.

    Consisting of an ArcGIS OGC Feature Service and ArcGIS OGC Feature Layer option.
    """

    def __init__(self, option: RecordDistribution, other_options: list[RecordDistribution], **kwargs: Any) -> None:
        service_media_href = "https://metadata-resources.data.bas.ac.uk/media-types/x-service/ogc+api+feature"
        super().__init__(option, other_options, service_media_href, **kwargs)

    @classmethod
    def matches(cls, option: RecordDistribution, other_options: list[RecordDistribution]) -> bool:
        """Whether this class matches the distribution option."""
        target_hrefs = [
            "https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+layer+feature+ogc",
            "https://metadata-resources.data.bas.ac.uk/media-types/x-service/ogc+api+feature",
        ]
        return ArcGisFeatureLayer._matches(target_hrefs=target_hrefs, option=option, other_options=other_options)

    @property
    def format_type(self) -> DistributionType:
        """Format type."""
        return DistributionType.ARCGIS_OGC_FEATURE_LAYER


class ArcGisVectorTileLayer(ArcGISDistribution):
    """
    ArcGIS Vector Tile Layer distribution option.

    Consisting of a vector tile service and vector tile layer option.
    """

    def __init__(self, option: RecordDistribution, other_options: list[RecordDistribution], **kwargs: Any) -> None:
        service_media_href = (
            "https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+service+tile+vector"
        )
        super().__init__(option, other_options, service_media_href, **kwargs)

    @classmethod
    def matches(cls, option: RecordDistribution, other_options: list[RecordDistribution]) -> bool:
        """Whether this class matches the distribution option."""
        target_hrefs = [
            "https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+layer+tile+vector",
            "https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+service+tile+vector",
        ]
        return ArcGisFeatureLayer._matches(target_hrefs=target_hrefs, option=option, other_options=other_options)

    @property
    def format_type(self) -> DistributionType:
        """Format type."""
        return DistributionType.ARCGIS_VECTOR_TILE_LAYER


class ArcGisRasterTileLayer(ArcGISDistribution):
    """
    ArcGIS Raster Tile Layer distribution option.

    Consisting of a (raster) tile service and (raster) tile layer option.
    """

    def __init__(self, option: RecordDistribution, other_options: list[RecordDistribution], **kwargs: Any) -> None:
        service_media_href = (
            "https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+service+tile+raster"
        )
        super().__init__(option, other_options, service_media_href, **kwargs)

    @classmethod
    def matches(cls, option: RecordDistribution, other_options: list[RecordDistribution]) -> bool:
        """Whether this class matches the distribution option."""
        target_hrefs = [
            "https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+layer+tile+raster",
            "https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+service+tile+raster",
        ]
        return ArcGisFeatureLayer._matches(target_hrefs=target_hrefs, option=option, other_options=other_options)

    @property
    def format_type(self) -> DistributionType:
        """Format type."""
        return DistributionType.ARCGIS_RASTER_TILE_LAYER


class BasPublishedMap(Distribution):
    """
    BAS published map distribution option.

    Provides information to users on how to purchase BAS maps.
    """

    def __init__(self, option: RecordDistribution, **kwargs: Any) -> None:
        self.option = option

    @classmethod
    def matches(cls, option: RecordDistribution, other_options: list[RecordDistribution]) -> bool:
        """Whether this class matches the distribution option."""
        return (
            option.transfer_option.online_resource.href
            == "https://www.bas.ac.uk/data/our-data/maps/how-to-order-a-map/"
        )

    @property
    def format_type(self) -> DistributionType:
        """Format type."""
        return DistributionType.X_BAS_PAPER_MAP

    @property
    def label(self) -> str:
        """Fixed value."""
        return self.format_type.value

    @property
    def description(self) -> None:
        """Not applicable as info box provides additional context."""
        return None

    @property
    def size(self) -> str:
        """Not applicable."""
        return ""

    @property
    def action(self) -> Link:
        """Link to distribution without href due to using `access_trigger`."""
        return Link(value="Purchase Options", href=None)

    @property
    def action_btn_icon(self) -> str:
        """Action button icon classes."""
        return "far fa-shopping-basket"

    @property
    def access_target(self) -> str | None:
        """DOM selector of element showing more information on purchasing item."""
        return "#item-data-info-map-purchase"


class BasSan(Distribution):
    """
    BAS SAN distribution option.

    Provides information to users on how to access data from the SAN.
    """

    _sigil = "sftp://san.nerc-bas.ac.uk/"

    def __init__(self, option: RecordDistribution, restricted: bool, **kwargs: Any) -> None:
        self._option = option
        self._restricted = restricted

    @classmethod
    def matches(cls, option: RecordDistribution, other_options: list[RecordDistribution]) -> bool:
        """Whether this class matches the distribution option."""
        return option.transfer_option.online_resource.href.startswith(BasSan._sigil)

    @property
    def format_type(self) -> DistributionType:
        """Fixed (fake) Format type."""
        return DistributionType.X_BAS_SAN

    @property
    def label(self) -> str:
        """Distinguishing identifier from transfer option if available, or generic value based on file type."""
        title = self._option.transfer_option.online_resource.title
        return title if title else "BAS SAN"

    @property
    def description(self) -> None:
        """Not applicable as info box provides additional context."""
        return None

    @property
    def size(self) -> str:
        """Not applicable."""
        return ""

    @property
    def posix_path(self) -> str:
        """SAN path formatted for use on Linux machines where SAN volumes are mounted under `/data`."""
        return urlparse(unquote(self._option.transfer_option.online_resource.href)).path

    @property
    def unc_path(self) -> str:
        """SAN path formatted as a UNC path for use on Windows machines where SAN volumes can be accessed via Samba."""
        samba_endpoint = r"\\samba.nerc-bas.ac.uk\data"
        raw = self.posix_path.replace("/data", "")
        return samba_endpoint + raw.replace("/", "\\")

    @property
    def restricted(self) -> bool:
        """Restricted status."""
        return self._restricted

    @property
    def action(self) -> Link:
        """Link to distribution without href due to using `access_trigger`."""
        return Link(value="Access Data", href=None)

    @property
    def action_btn_variant(self) -> str:
        """Variant of button to display for action link."""
        return super().action_btn_variant if not self._restricted else super().action_btn_variant_restricted

    @property
    def action_btn_icon(self) -> str:
        """Action button icon classes."""
        return "far fa-hdd" if not self._restricted else super().action_btn_icon_restricted

    @property
    def access_target(self) -> str | None:
        """DOM selector of element showing more information on accessing item."""
        return "#item-data-info-san-access"


class Csv(FileDistribution):
    """CSV distribution option."""

    @classmethod
    def matches(cls, option: RecordDistribution, other_options: list[RecordDistribution]) -> bool:
        """Whether this class matches the distribution option."""
        return (
            option.format is not None and option.format.href == "https://www.iana.org/assignments/media-types/text/csv"
        )

    @property
    def format_type(self) -> DistributionType:
        """Format type."""
        return DistributionType.CSV


class Fpl(FileDistribution):
    """FPL distribution option."""

    @classmethod
    def matches(cls, option: RecordDistribution, other_options: list[RecordDistribution]) -> bool:
        """Whether this class matches the distribution option."""
        return (
            option.format is not None
            and option.format.href == "https://metadata-resources.data.bas.ac.uk/media-types/application/fpl+xml"
        )

    @property
    def format_type(self) -> DistributionType:
        """Format type."""
        return DistributionType.FPL


class GeoJson(FileDistribution):
    """GeoJSON distribution option."""

    @classmethod
    def matches(cls, option: RecordDistribution, other_options: list[RecordDistribution]) -> bool:
        """Whether this class matches the distribution option."""
        return (
            option.format is not None
            and option.format.href == "https://www.iana.org/assignments/media-types/application/geo+json"
        )

    @property
    def format_type(self) -> DistributionType:
        """Format type."""
        return DistributionType.GEOJSON


class GeoPackage(FileDistribution):
    """
    GeoPackage distribution option.

    With support for optional zip compression.
    """

    def __init__(self, option: RecordDistribution, restricted: bool, **kwargs: Any) -> None:
        super().__init__(option, restricted, **kwargs)
        self._compressed = self._is_compressed(option)

    @classmethod
    def matches(cls, option: RecordDistribution, other_options: list[RecordDistribution]) -> bool:
        """Whether this class matches the distribution option."""
        target_hrefs = [
            "https://www.iana.org/assignments/media-types/application/geopackage+sqlite3",
            "https://metadata-resources.data.bas.ac.uk/media-types/application/geopackage+sqlite3+zip",
        ]
        return option.format is not None and option.format.href in target_hrefs

    @staticmethod
    def _is_compressed(option: RecordDistribution) -> bool:
        """Check if GeoPackage is compressed based on self-reported format."""
        target_href = "https://metadata-resources.data.bas.ac.uk/media-types/application/geopackage+sqlite3+zip"
        # TYPING: This assumes option.format is not None but given `matches()` this will never be the case.
        return option.format.href == target_href  # ty: ignore[possibly-missing-attribute]

    @property
    def format_type(self) -> DistributionType:
        """Format type."""
        if self._compressed:
            return DistributionType.GEOPACKAGE_ZIP
        return DistributionType.GEOPACKAGE


class Gpx(FileDistribution):
    """GPX distribution option."""

    @classmethod
    def matches(cls, option: RecordDistribution, other_options: list[RecordDistribution]) -> bool:
        """Whether this class matches the distribution option."""
        return (
            option.format is not None
            and option.format.href == "https://metadata-resources.data.bas.ac.uk/media-types/application/gpx+xml"
        )

    @property
    def format_type(self) -> DistributionType:
        """Format type."""
        return DistributionType.GPX


class Jpeg(FileDistribution):
    """JPEG distribution option."""

    @classmethod
    def matches(cls, option: RecordDistribution, other_options: list[RecordDistribution]) -> bool:
        """Whether this class matches the distribution option."""
        return (
            option.format is not None
            and option.format.href == "https://www.iana.org/assignments/media-types/image/jpeg"
        )

    @property
    def format_type(self) -> DistributionType:
        """Format type."""
        return DistributionType.JPEG


class MapboxVectorTiles(FileDistribution):
    """Mapbox Vector Tiles distribution option."""

    @classmethod
    def matches(cls, option: RecordDistribution, other_options: list[RecordDistribution]) -> bool:
        """Whether this class matches the distribution option."""
        return (
            option.format is not None
            and option.format.href == "https://www.iana.org/assignments/media-types/application/vnd.mapbox-vector-tile"
        )

    @property
    def format_type(self) -> DistributionType:
        """Format type."""
        return DistributionType.MAPBOX_VECTOR_TILE


class Pdf(FileDistribution):
    """
    PDF distribution option.

    With support for distinguishing optional georeferencing.
    """

    def __init__(self, option: RecordDistribution, restricted: bool, **kwargs: Any) -> None:
        super().__init__(option, restricted, **kwargs)
        self._georeferenced = self._is_georeferenced(option)

    @classmethod
    def matches(cls, option: RecordDistribution, other_options: list[RecordDistribution]) -> bool:
        """Whether this class matches the distribution option."""
        target_hrefs = [
            "https://www.iana.org/assignments/media-types/application/pdf",
            "https://metadata-resources.data.bas.ac.uk/media-types/application/pdf+geo",
        ]
        return option.format is not None and option.format.href in target_hrefs

    @staticmethod
    def _is_georeferenced(option: RecordDistribution) -> bool:
        """Check if PDF is georeferenced based on self-reported format."""
        target_href = "https://metadata-resources.data.bas.ac.uk/media-types/application/pdf+geo"
        # TYPING: This assumes option.format is not None but given `matches()` this will never be the case.
        return option.format.href == target_href  # ty: ignore[possibly-missing-attribute]

    @property
    def format_type(self) -> DistributionType:
        """Format type."""
        if self._georeferenced:
            return DistributionType.PDF_GEO
        return DistributionType.PDF


class Png(FileDistribution):
    """PNG distribution option."""

    @classmethod
    def matches(cls, option: RecordDistribution, other_options: list[RecordDistribution]) -> bool:
        """Whether this class matches the distribution option."""
        return (
            option.format is not None and option.format.href == "https://www.iana.org/assignments/media-types/image/png"
        )

    @property
    def format_type(self) -> DistributionType:
        """Format type."""
        return DistributionType.PNG


class Shapefile(FileDistribution):
    """
    Shapefile distribution option.

    Supports zip compressed shapefiles only.
    """

    @classmethod
    def matches(cls, option: RecordDistribution, other_options: list[RecordDistribution]) -> bool:
        """Whether this class matches the distribution option."""
        return (
            option.format is not None
            and option.format.href == "https://metadata-resources.data.bas.ac.uk/media-types/application/vnd.shp+zip"
        )

    @property
    def format_type(self) -> DistributionType:
        """Format type."""
        return DistributionType.SHAPEFILE_ZIP
