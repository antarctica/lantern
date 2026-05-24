from dataclasses import dataclass, field
from pathlib import Path
from typing import Final

from lantern.lib.metadata_library.models.record.elements.common import Contact, OnlineResource
from lantern.lib.metadata_library.models.record.elements.distribution import Distribution, Format, Size, TransferOption
from lantern.lib.metadata_library.models.record.enums import OnlineResourceFunctionCode


@dataclass
class ZapFormat:
    """Distribution format as used in Zap ⚡️."""

    slug: str
    name: str
    url: str
    description: str | None = None
    extensions: list[str] = field(default_factory=list)
    media_types: list[str] = field(default_factory=list)


class DistributionMaker:
    """
    Create distribution options consistent with Zap ⚡️.

    Based on Zap ⚡️ formats data file with local additions for CSV, FPL and GPX.
    Based on Zap ⚡️ distribution option construction for consistency between manual and automatically authored records.
    """

    _zap_formats: Final[dict] = {
        "csv": {
            "slug": "csv",
            "name": "Comma Separated Values",
            "extensions": [".csv"],
            "mediaTypes": ["text/csv"],
            "url": "https://www.iana.org/assignments/media-types/text/csv",
        },
        "fpl": {
            "slug": "fpl",
            "name": "Garmin Flight Plan",
            "extensions": [".fpl"],
            "url": "https://metadata-resources.data.bas.ac.uk/media-types/application/fpl+xml",
        },
        "geojson": {
            "slug": "geojson",
            "name": "GeoJSON",
            "extensions": [".geojson", ".json"],
            "mediaTypes": ["application/geo+json"],
            "url": "https://www.iana.org/assignments/media-types/application/geo+json",
        },
        "gpkg": {
            "slug": "gpkg",
            "name": "GeoPackage",
            "extensions": [".gpkg"],
            "mediaTypes": ["application/geopackage+sqlite3"],
            "url": "https://www.iana.org/assignments/media-types/application/geopackage+sqlite3",
        },
        "gpkg_zip": {
            "slug": "gpkg_zip",
            "name": "GeoPackage (Zipped)",
            "description": "Download information as a GeoPackage file compressed as a Zip archive.",
            "extensions": [".gpkg.zip"],
            "url": "https://metadata-resources.data.bas.ac.uk/media-types/application/geopackage+sqlite3+zip",
        },
        "gpx": {
            "slug": "gpx",
            "name": "GPS Exchange Format",
            "extensions": [".gpx"],
            "mediaTypes": ["application/gpx+xml"],
            "url": "https://metadata-resources.data.bas.ac.uk/media-types/application/gpx+xml",
        },
        "jpeg": {
            "slug": "jpeg",
            "name": "JPEG",
            "extensions": [".jpg", ".jpeg"],
            "mediaTypes": ["image/jpeg"],
            "url": "https://www.iana.org/assignments/media-types/image/jpeg",
        },
        "mbtiles": {
            "slug": "mbtiles",
            "name": "MapBox Vector Tiles",
            "mediaTypes": ["application/vnd.mapbox-vector-tile"],
            "extensions": [".mbtiles"],
            "url": "https://www.iana.org/assignments/media-types/application/vnd.mapbox-vector-tile",
        },
        "pdf": {
            "slug": "pdf",
            "name": "PDF",
            "extensions": [".pdf"],
            "mediaTypes": ["application/pdf"],
            "url": "https://www.iana.org/assignments/media-types/application/pdf",
        },
        "pdf_geo": {
            "slug": "pdf_geo",
            "name": "PDF",
            "description": "Download information as a PDF file with embedded georeferencing.",
            "extensions": [],
            "mediaTypes": ["application/pdf+geo"],
            "url": "https://metadata-resources.data.bas.ac.uk/media-types/application/pdf+geo",
        },
        "png": {
            "slug": "png",
            "name": "PNG",
            "extensions": [".png"],
            "mediaTypes": ["image/png"],
            "url": "https://www.iana.org/assignments/media-types/image/png",
        },
        "shp_zip": {
            "slug": "shp_zip",
            "name": "Shapefile (Zipped)",
            "description": "Download information as a Shapefile compressed as a Zip archive.",
            "extensions": [".shp.zip"],
            "url": "https://metadata-resources.data.bas.ac.uk/media-types/application/shapefile+zip",
        },
    }

    def __init__(self) -> None:
        self._formats: list[ZapFormat] = [
            ZapFormat(
                slug=format_["slug"],
                name=format_["name"],
                description=format_.get("description"),
                extensions=format_.get("extensions"),
                media_types=format_.get("mediaTypes"),
                url=format_["url"],
            )
            for format_ in self._zap_formats.values()
        ]

    def format_by_ext(self, file_path: Path) -> ZapFormat:
        """Get file format by file extension if known."""
        ext = file_path.suffix.lower()
        for format_ in self._formats:
            if ext in format_.extensions:
                return format_

        msg = f"unknown media type for extension '{ext}'."
        raise ValueError(msg) from None

    @staticmethod
    def make_dist_option(
        format_: ZapFormat, href: str, distributor: Contact, size_bytes: int | None = None
    ) -> Distribution:
        """Create a distribution option."""
        dist = Distribution(
            format=Format(format=format_.name, href=format_.url),
            transfer_option=TransferOption(
                online_resource=OnlineResource(
                    href=href,
                    title=format_.name,
                    description=format_.description,
                    function=OnlineResourceFunctionCode.DOWNLOAD,
                ),
            ),
            distributor=distributor,
        )
        if size_bytes is not None:
            dist.transfer_option.size = Size(unit="bytes", magnitude=size_bytes)
        return dist

    def from_file(self, file_path: Path, href: str, distributor: Contact) -> Distribution:
        """Create a distribution option for a file."""
        format_ = self.format_by_ext(file_path)
        size_bytes = file_path.stat().st_size
        return self.make_dist_option(format_=format_, href=href, distributor=distributor, size_bytes=size_bytes)
