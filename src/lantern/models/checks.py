from dataclasses import dataclass
from enum import Enum
from http import HTTPMethod, HTTPStatus
from typing import Final

from lantern.lib.metadata_library.models.record.elements.distribution import Distributions
from lantern.models.record.record import Record
from lantern.models.site import SiteContent, SiteRedirect


class CheckType(Enum):
    """
    Check type.

    Broadly aligns with Outputs, Records identifiers or Record distribution types.

    Used to guide how checks are ran (i.e. which check method to use) and to group checks in reporting.
    """

    NONE = "none"
    BAS_WEBSITE_SEARCH = "BAS Public Website Search"
    ITEM_ALIASES = "Item Aliases"
    ITEM_PAGES = "Item Pages"
    RECORD_PAGES_JSON = "Record Pages (JSON)"
    RECORD_PAGES_HTML = "Record Pages (XML HTML)"
    RECORD_PAGES_XML = "Record Pages (XML)"
    SITE_404 = "Site Not Found Handler"
    SITE_API = "Site API"
    SITE_HEALTH = "Site Health"
    SITE_INDEX = "Site Index"
    SITE_PAGES = "Site Pages"
    SITE_RESOURCES = "Site Resources"
    WAF_PAGES = "WAF"

    DOI_REDIRECTS = "DOI Redirects"
    BAS_PUBLISHED_MAP = "Published Map"
    DOWNLOADS_OPEN = "Normal Downloads"
    DOWNLOADS_NORA = "NORA Downloads"
    DOWNLOADS_SHAREPOINT = "SharePoint Downloads"
    DOWNLOADS_BAS_SAN = "BAS SAN Downloads"
    DOWNLOADS_ARCGIS_LAYER = "ArcGIS Layer"
    DOWNLOADS_ARCGIS_SERVICE = "ArcGIS Service"


class CheckState(Enum):
    """Check state/lifecycle."""

    PENDING = "pending"
    SKIPPED = "skipped"
    FAILED = "failed"
    PASS = "passed"  # noqa: S105


@dataclass(kw_only=True)
class Check:
    """
    Site check.

    Used to verify the contents of a site or a resource within a site.

    - type: see CheckType
    - url: fully qualified URL to check
    - http_method: HTTP method to use for check (HEAD is preferred to minimise content but some endpoints lack support)
    - http_status: expected HTTP status (200, 301, etc.)
    - content_length: optional expected content length (not reliable to use generally)
    - redirect_location: optional expected location header value for redirects
    - file_identifier: optional file identifier for Record related checks, used for grouping in reporting

    - state: check lifecycle, updated by check method when processed
    - duration: duration of check processing as measured by `time`
    - result_http_status: HTTP status of check, compared against expected status
    - result_output: output of check, for reporting/troubleshooting
    """

    type: CheckType
    url: str
    http_method: HTTPMethod = HTTPMethod.HEAD
    http_status: HTTPStatus = HTTPStatus.OK
    content_length: int | None = None
    redirect_location: str | None = None
    file_identifier: str | None = None

    state: CheckState = CheckState.PENDING
    duration: float = 0.0
    result_http_status: HTTPStatus | None = None
    result_output: str | None = None

    @classmethod
    def from_site_content(cls, content: SiteContent, check_type: CheckType, base_url: str) -> "Check":
        """Create check from site content."""
        status = HTTPStatus.OK
        if isinstance(content, SiteRedirect):
            status = HTTPStatus.MOVED_PERMANENTLY

        return cls(
            type=check_type,
            url=f"{base_url}/{content.path!s}",
            http_status=status,
            redirect_location=content.redirect,
            file_identifier=content.object_meta.get("file_identifier"),
        )


class DistributionChecks:
    """Generator for checks from a Record's distribution options."""

    _arcgis_layer_sigils: Final[list[str]] = [
        "https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+layer+feature",
        "https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+layer+feature+ogc",
        "https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+layer+tile+raster",
        "https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+layer+tile+vector",
    ]
    _arcgis_service_sigils: Final[list[str]] = [
        "https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+service+feature",
        "https://metadata-resources.data.bas.ac.uk/media-types/x-service/ogc+api+feature",
        "https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+service+tile+raster",
        "https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+service+tile+vector",
    ]
    _bas_published_maps_sigil: Final[str] = "https://data.bas.ac.uk/guides/map-purchasing/"
    _nora_sigil: Final[str] = "https://nora.nerc.ac.uk/"
    _sharepoint_sigil: Final[str] = "sharepoint.com"
    _bas_san_sigil: Final[str] = "sftp://san.nerc-bas.ac.uk/"

    def __init__(self, distributions: Distributions, file_identifier: str) -> None:
        self._distributions = distributions
        self._file_identifier = file_identifier

    def _parse(self) -> list[tuple[CheckType, str, int | None]]:
        """
        Generate parameters for checks from distribution options.

        Matches distribution options to a CheckType using a combination of format and transfer option logic.
        Includes expected content-length if included in distribution option.

        Format based detection matches on the format href using similar logic to catalogue item distribution classes.
        Transfer option detection typically matches against the hostname to detect the hosting service.

        Used to detect distribution options that require additional handling (files hosted on NORA for example, which
        does not support HEAD requests).

        Returns a list of matched (type,href,content-length) tuples for building Checks.
        """
        type_hrefs = []
        for dist_option in self._distributions:
            format_href = dist_option.format.href if dist_option.format else None
            transfer_href = dist_option.transfer_option.online_resource.href
            content_length = None
            if dist_option.transfer_option.size is not None and dist_option.transfer_option.size.unit == "bytes":
                content_length = int(dist_option.transfer_option.size.magnitude)

            type_ = CheckType.DOWNLOADS_OPEN

            # From most to least specific
            if transfer_href == self._bas_published_maps_sigil:
                type_ = CheckType.BAS_PUBLISHED_MAP
            elif format_href in self._arcgis_layer_sigils:
                type_ = CheckType.DOWNLOADS_ARCGIS_LAYER
            elif format_href in self._arcgis_service_sigils:
                type_ = CheckType.DOWNLOADS_ARCGIS_SERVICE
            elif transfer_href.startswith(self._nora_sigil):
                type_ = CheckType.DOWNLOADS_NORA
            elif transfer_href.startswith(self._bas_san_sigil):
                type_ = CheckType.DOWNLOADS_BAS_SAN
            elif self._sharepoint_sigil in transfer_href:
                type_ = CheckType.DOWNLOADS_SHAREPOINT

            type_hrefs.append((type_, transfer_href, content_length))
        return type_hrefs

    @property
    def checks(self) -> list[Check]:
        """
        Generate checks for distribution options.

        Checks for SharePoint and the BAS SAN are marked as skipped until a suitable implementation is available.
        """
        checks = []
        for type_href in self._parse():
            check = Check(
                type=type_href[0], url=type_href[1], file_identifier=self._file_identifier, content_length=type_href[2]
            )
            if check.type == CheckType.DOWNLOADS_NORA:
                check.http_method = HTTPMethod.GET
                check.http_status = HTTPStatus.PARTIAL_CONTENT
            if check.type in [CheckType.DOWNLOADS_SHAREPOINT, CheckType.DOWNLOADS_BAS_SAN]:
                check.state = CheckState.SKIPPED
            checks.append(check)
        return checks


class RecordChecks:
    """Generator for checks from the contents of a Record."""

    def __init__(self, record: Record) -> None:
        self._record = record

    @property
    def _doi_checks(self) -> list[Check]:
        """
        Generate checks for any DOI identifiers.

        DOIs always use the `data.bas.ac.uk` domain and so are only valid for the live catalogue endpoint.
        """
        checks = []
        for doi in self._record.identification.identifiers.filter(namespace="doi"):
            checks.append(
                Check(
                    type=CheckType.DOI_REDIRECTS,
                    url=f"https://doi.org/{doi.identifier}",
                    redirect_location=f"https://data.bas.ac.uk/items/{self._record.file_identifier}",
                    file_identifier=self._record.file_identifier,
                )
            )
        return checks

    @property
    def _distribution_checks(self) -> list[Check]:
        """Generate checks for any distribution options."""
        return DistributionChecks(
            distributions=self._record.distribution, file_identifier=self._record.file_identifier
        ).checks

    @property
    def checks(self) -> list[Check]:
        """Checks from record contents."""
        return [*self._doi_checks, *self._distribution_checks]
