from typing import Final, cast
from urllib.parse import unquote, urlparse

from lantern.lib.metadata_library.models.record import Distribution
from lantern.models.record import ALIAS_NAMESPACE, CATALOGUE_NAMESPACE
from lantern.models.record.revision import RecordRevision
from lantern.models.verification.enums import VerificationDistributionType, VerificationType
from lantern.models.verification.jobs import VerificationJob
from lantern.models.verification.types import VerificationContext


class VerificationDistribution:
    """
    Verification Distribution.

    Extends base Record Distribution class with site verification properties and methods.
    """

    file_media_types: Final[list[str]] = [
        "https://www.iana.org/assignments/media-types/application/geo+json",
        "https://www.iana.org/assignments/media-types/application/geopackage+sqlite3",
        "https://metadata-resources.data.bas.ac.uk/media-types/application/geopackage+sqlite3+zip",
        "https://www.iana.org/assignments/media-types/image/jpeg",
        "https://www.iana.org/assignments/media-types/application/pdf",
        "https://metadata-resources.data.bas.ac.uk/media-types/application/pdf+geo",
        "https://www.iana.org/assignments/media-types/image/png",
        "https://metadata-resources.data.bas.ac.uk/media-types/application/vnd.shp+zip",
    ]

    arcgis_layer_media_types: Final[list[str]] = [
        "https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+layer+feature",
        "https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+layer+feature+ogc",
        "https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+layer+tile+raster",
        "https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+layer+tile+vector",
    ]

    arcgis_service_media_types: Final[list[str]] = [
        "https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+service+feature",
        "https://metadata-resources.data.bas.ac.uk/media-types/x-service/ogc+api+feature",
        "https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+service+tile+raster",
        "https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+service+tile+vector",
    ]

    published_maps_url: Final[str] = "https://www.bas.ac.uk/data/our-data/maps/how-to-order-a-map/"

    def __init__(self, distribution: Distribution, file_identifier: str) -> None:
        """Initialise from an underlying Record Distribution and associated Record file identifier."""
        self._distribution = distribution
        self._file_identifier = file_identifier

    def __repr__(self) -> str:
        """String representation."""
        short_ref = (
            self._file_identifier[:4] + "..." + self._file_identifier[-4:]
        )  # first/last 4 characters for brevity
        return f"Distribution(resource={short_ref}, type={self._type.name}, href={self._href})"

    @property
    def _type(self) -> VerificationDistributionType:
        """
        Verification distribution type.

        Used to determine how distribution should be verified.
        """
        if "sharepoint.com" in self._distribution.transfer_option.online_resource.href:
            return VerificationDistributionType.SHAREPOINT
        if self._distribution.transfer_option.online_resource.href.startswith("https://nora.nerc.ac.uk/"):
            return VerificationDistributionType.NORA
        if self._distribution.transfer_option.online_resource.href == self.published_maps_url:
            return VerificationDistributionType.PUBLISHED_MAP
        if self._distribution.format and self._distribution.format.href in self.file_media_types:
            return VerificationDistributionType.FILE
        if self._distribution.format and self._distribution.format.href in self.arcgis_layer_media_types:
            return VerificationDistributionType.ARCGIS_LAYER
        if self._distribution.format and self._distribution.format.href in self.arcgis_service_media_types:
            return VerificationDistributionType.ARCGIS_SERVICE

        msg = "Unsupported verification distribution type"
        raise ValueError(msg) from None

    @property
    def _href_raw(self) -> str:
        """Original distribution transfer option href."""
        return self._distribution.transfer_option.online_resource.href

    @property
    def _href(self) -> str:
        """
        Processed distribution href for verification.

        - for ArcGIS layers, the item ID is extracted to build item URL return item data as JSON
        - for ArcGIS services, service information is returned as JSON
        - for SharePoint, the path to the file is extracted from the URL for use with a SharePoint access proxy [1]

        [1] For 'https://example.com/:i:/r/personal/conwat_example_com/Documents/foo%20bar.jpg?x=y' -> '/foo bar.jpg'
        """
        if self._type == VerificationDistributionType.ARCGIS_LAYER:
            item_id = self._href_raw.split("id=")[-1]
            return f"https://www.arcgis.com/sharing/rest/content/items/{item_id}?f=json"
        if self._type == VerificationDistributionType.ARCGIS_SERVICE:
            return f"{self._href_raw}?f=json"
        if self._type == VerificationDistributionType.SHAREPOINT:
            path = urlparse(unquote(self._href_raw)).path
            return path.split("/Documents")[-1]

        return self._href_raw

    @property
    def _bytes(self) -> int | None:
        """Distribution size in bytes where available."""
        if self._distribution.transfer_option.size is None or self._distribution.transfer_option.size.unit != "bytes":
            return None
        return int(self._distribution.transfer_option.size.magnitude)

    def _make_job(self, job_type: VerificationType, href: str, context: VerificationContext) -> VerificationJob:
        return VerificationJob(
            type=job_type,
            url=href,
            context=context,
            data={"file_identifier": self._file_identifier, "distribution_type": self._type},
        )

    def jobs(self, context: VerificationContext) -> list[VerificationJob]:
        """
        Generate verification jobs for distribution.

        Appends additional job context as needed.
        """
        jobs = [
            self._make_job(
                job_type=VerificationType.ITEM_DOWNLOADS,
                href=self._href_raw,
                context=cast(
                    VerificationContext,
                    {
                        "CHECK_FUNC": "check_item_download",
                        "URL": f"{context['BASE_URL']}/items/{self._file_identifier}/index.html",
                        **context,
                    },
                ),
            )
        ]

        if self._type == VerificationDistributionType.FILE:
            jobs.append(
                self._make_job(
                    job_type=VerificationType.DOWNLOADS_OPEN,
                    href=self._href,
                    context=cast(VerificationContext, {"EXPECTED_LENGTH": self._bytes, **context}),
                )
            )
        elif self._type == VerificationDistributionType.NORA:
            context_ = cast(
                VerificationContext,
                {
                    "METHOD": "get",  # NORA reacts differently to HEAD vs GET requests
                    "HEADERS": {"Range": "bytes=0-253"},
                    "EXPECTED_STATUS": 206,
                    "EXPECTED_LENGTH": self._bytes,
                    **context,
                },
            )
            jobs.append(self._make_job(job_type=VerificationType.DOWNLOADS_NORA, href=self._href, context=context_))
        elif self._type == VerificationDistributionType.SHAREPOINT:
            context_ = cast(
                VerificationContext,
                {
                    "METHOD": "post",
                    "URL": context["SHAREPOINT_PROXY_ENDPOINT"],
                    "JSON": {"path": self._href},
                    **context,
                },
            )
            jobs.append(
                self._make_job(job_type=VerificationType.DOWNLOADS_SHAREPOINT, href=self._href_raw, context=context_)
            )
        elif self._type == VerificationDistributionType.ARCGIS_LAYER:
            context_ = cast(VerificationContext, {"CHECK_FUNC": "check_url_arcgis", **context})
            jobs.append(
                self._make_job(job_type=VerificationType.DOWNLOADS_ARCGIS_LAYERS, href=self._href, context=context_)
            )
        elif self._type == VerificationDistributionType.ARCGIS_SERVICE:  # pragma: no branch
            context_ = cast(VerificationContext, {"CHECK_FUNC": "check_url_arcgis", **context})
            jobs.append(
                self._make_job(job_type=VerificationType.DOWNLOADS_ARCGIS_SERVICES, href=self._href, context=context_)
            )

        return jobs


class VerificationRecord:
    """
    Verification Distribution.

    Extends base Record class with site verification properties and methods.
    """

    def __init__(self, record: RecordRevision) -> None:
        """Initialise from an underlying RecordRevision."""
        self._record = record

    def _record_jobs(self, context: VerificationContext) -> list[VerificationJob]:
        """Generate verification jobs for record formats."""
        formats: list[tuple[str, str, VerificationType]] = [
            ("json", "JsonExporter", VerificationType.RECORD_PAGES_JSON),
            ("xml", "IsoXmlExporter", VerificationType.RECORD_PAGES_XML),
            ("html", "IsoXmlHtmlExporter", VerificationType.RECORD_PAGES_HTML),
        ]
        return [
            VerificationJob(
                type=fmt[2],
                exporter=fmt[1],
                url=f"{context['BASE_URL']}/records/{self._record.file_identifier}.{fmt[0]}",
                context=context,
                data={"file_identifier": self._record.file_identifier},
            )
            for fmt in formats
        ]

    def _item_jobs(self, context: VerificationContext) -> list[VerificationJob]:
        """Generate verification job for related item page."""
        return [
            VerificationJob(
                type=VerificationType.ITEM_PAGES,
                exporter="HtmlExporter",
                url=f"{context['BASE_URL']}/items/{self._record.file_identifier}/index.html",
                context=context,
                data={"file_identifier": self._record.file_identifier},
            )
        ]

    def _redirect_jobs(self, context: VerificationContext) -> list[VerificationJob]:
        """Generate verification jobs for record alias and DOI identifiers."""
        jobs = []

        for alias in self._record.identification.identifiers.filter(namespace=ALIAS_NAMESPACE):
            jobs.append(
                VerificationJob(
                    type=VerificationType.ALIAS_REDIRECTS,
                    exporter="HtmlAliasesExporter",
                    url=f"{context['BASE_URL']}/{alias.identifier}/",
                    context=cast(
                        VerificationContext,
                        {
                            "CHECK_FUNC": "check_url_redirect",
                            "TARGET": f"/items/{self._record.file_identifier}/index.html",
                            **context,
                        },
                    ),
                    data={"file_identifier": self._record.file_identifier, "slug": alias.identifier},
                )
            )

        for doi in self._record.identification.identifiers.filter(namespace="doi"):
            jobs.append(
                VerificationJob(
                    type=VerificationType.DOI_REDIRECTS,
                    url=f"https://doi.org/{doi.identifier}",
                    context=cast(
                        VerificationContext,
                        {
                            "CHECK_FUNC": "check_url_redirect",
                            "TARGET": f"https://{CATALOGUE_NAMESPACE}/items/{self._record.file_identifier}",
                            **context,
                        },
                    ),
                    data={"file_identifier": self._record.file_identifier, "slug": doi.identifier},
                )
            )

        return jobs

    def _distribution_jobs(self, context: VerificationContext) -> list[VerificationJob]:
        """Generate verification jobs for record distribution options."""
        return [
            job
            for dist in self._record.distribution
            for job in VerificationDistribution(distribution=dist, file_identifier=self._record.file_identifier).jobs(
                context
            )
        ]

    def jobs(self, context: VerificationContext) -> list[VerificationJob]:
        """
        Generate verification jobs for record.

        Appends additional job context as needed.
        """
        jobs = []
        jobs.extend(self._record_jobs(context))
        jobs.extend(self._item_jobs(context))
        jobs.extend(self._redirect_jobs(context))
        jobs.extend(self._distribution_jobs(context))
        return jobs
