from __future__ import annotations

from base64 import urlsafe_b64encode
from typing import get_type_hints
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from lantern.lib.magic_distribution.formats import (
    ArtefactFormat,
    ArtefactFormatLabel,
    ArtefactFormats,
    ArtefactFormatUnknownError,
)
from lantern.lib.magic_distribution.models.artefact import ArtefactFile
from lantern.lib.magic_distribution.sharepoint.models.types import ArtefactMetadata
from lantern.lib.metadata_library.models.record.elements.common import Contact, OnlineResource
from lantern.lib.metadata_library.models.record.elements.distribution import Distribution, Size, TransferOption
from lantern.lib.metadata_library.models.record.enums import OnlineResourceFunctionCode
from lantern.lib.metadata_library.models.record.presets.contacts import MICROSOFT_DISTRIBUTOR


class ArtefactSharePointFile(ArtefactFile):
    """
    File artefact for a remote file stored in SharePoint.

    Intended for, and specific to, file artefacts deposited in the MAGIC Resource Distribution SharePoint site.

    Uses metadata recorded about a file to state its format, size, name, etc. Does not allow access to file content.

    Provides an access URL to access the artefact file and distribution option for use within resource records.

    Metadata
    --------

    Metadata consists of:
    - `drive_item`: system metadata (file size, hash, name, etc.), via an MS Graph `driveItem` resource [1]
    - `list_metadata`: user metadata (artefact/resource ID, controlled format, SHA256, and unrestricted status), via
      an MS Graph `fieldValueSet` [2]

    `drive_item` properties are generic and controlled by the underlying SharePoint/Graph platform. `list_metadata`
    properties are intended to provide additional context where needed. `list_metadata` values are explicitly trusted.

    Artefact format
    ---------------

    As determining the artefact format accurately requires access the file content (e.g. for geo-PDFs) and file content
    is not accessible, a known format must be provided by via `list_metadata`. This stated value MUST be a member of
    the `lantern.lib.magic_distribution.models.artefacts.ArtefactFormatLabel` enum and will be treated as authoritative.

    Access Proxy
    ------------

    The anonymous sharing level within SharePoint can be disabled at a site or tenancy level, preventing access to any
    files without explict sharing. To overcome this for files intended for open access resources an access proxy CAN be
    used. At a high level, this proxy will request a file on the client's behalf, checking access permissions and if
    applicable, returning a pre-signed URL to the file via a redirect.

    The access URL will use an access proxy where the `proxy_base` parameter is set and the `unrestricted` value in
    `list_metadata` is true.

    [1] https://learn.microsoft.com/en-us/graph/api/resources/driveitem
    [2] https://learn.microsoft.com/en-us/graph/api/resources/fieldvalueset
    """

    def __init__(self, drive_item: dict, list_metadata: ArtefactMetadata, proxy_base: str | None = None) -> None:
        self._check_artefact_metadata(list_metadata)
        self._drive_item = drive_item
        self._list_fields = list_metadata
        self._proxy_base = proxy_base
        super().__init__(self.resource_id)

    def __repr__(self) -> str:
        """Class representation."""
        return f"<ArtefactSpFile: {self.artefact_id} (driveItem: {self._drive_item['id']}), {self.format.name}, {self.size_bytes} bytes, sha256: {self.sha256}>"

    @staticmethod
    def _check_artefact_metadata(list_metadata: ArtefactMetadata) -> None:
        """Validate required metadata against typed dict."""
        keys = get_type_hints(ArtefactMetadata).keys()
        if not all(key in list_metadata for key in keys):
            msg = "One or more required artefact metadata keys are missing from SharePoint list metadata."
            raise KeyError(msg)

    @property
    def artefact_id(self) -> str:  # ty: ignore[invalid-property-type-override]
        """
        Artefact identifier.

        As this value is based on a mutable object a typing error is triggered. In practice this value will be static
        based on the supplied file metadata which should not be modified and so can be treated as a read-only value.
        """
        return self._list_fields["artefact_id"]

    @property
    def resource_id(self) -> str:
        """Resource identifier."""
        return self._list_fields["resource_id"]

    @property
    def format(self) -> ArtefactFormat:
        """Artefact format if supported."""
        try:
            label = ArtefactFormatLabel[self._list_fields["artefact_fmt"]]
        except KeyError:
            raise ArtefactFormatUnknownError() from None
        else:
            return ArtefactFormats.get_by_label(label)

    def validate_format(self) -> None:
        """
        Check file is a supported type.

        May, but should not, raise ArtefactFormatUnknownError if list metadata reports an unknown format.
        """
        _ = self.format  # will trigger ArtefactFormatUnknownError if not supported

    @property
    def name(self) -> str:
        """Artefact name."""
        return self._drive_item["name"]

    @property
    def data(self) -> bytes:
        """Artefact content as bytes."""
        raise NotImplementedError() from None

    @property
    def size_bytes(self) -> int:
        """Artefact size in bytes."""
        return self._drive_item["size"]

    @property
    def quickxor(self) -> str:  # ty: ignore[invalid-property-type-override]
        """
        Microsoft QuickXorHash.

        As this value is based on a mutable object a typing error is triggered. In practice this value will be static
        based on the supplied file metadata which should not be modified and so can be treated as a read-only value.
        """
        return self._drive_item["file"]["hashes"]["quickXorHash"]

    @property
    def sha256(self) -> str:  # ty: ignore[invalid-property-type-override]
        """
        SHA 256 hash.

        This value is set at upload, it is not based on the underlying file stored in SharePoint and so cannot be used
        to determine if a file has changed internally (see `quickxor`) but can be used for external comparisons.

        As this value is based on a mutable object a typing error is triggered. In practice this value will be static
        based on the supplied file metadata which should not be modified and so can be treated as a read-only value.
        """
        return self._list_fields["artefact_sha256"]

    @property
    def presigned_url(self) -> str:
        """
        Temporary presigned access URL.

        WARNING: Do not expose in untrusted contexts.

        Values are time-limited and so may require refreshing by re-fetching the artefact.
        """
        return self._drive_item["@microsoft.graph.downloadUrl"]

    @property
    def url(self) -> str:
        """
        Direct access URL, unless an access proxy is configured and the artefact is unrestricted.

        URLs use the `webUrl` property which has variable behaviour based on file format as defined by SharePoint:
        - formats supported for editing open in a relevant app (e.g. Excel online for a CSV file)
        - PDF files specifically open in a (SharePoint) PDF viewer
        - all other files download directly

        Files that support editing use URLs in the form:
        `https://example.com/.../_layouts/15/Doc.aspx?sourcedoc=...&file=file.csv

        File checksum values are appended to the URL for checking the integrity of downloaded files.

        E.g. A direct URL `https://example.com/file.ext` becomes: `https://example.com/file.ext?sha256=x&quickxor=y`.

        Note: Any existing query parameters in the direct URL are preserved when checksum values are appended.

        Where an access proxy is used:
        - a base 64 encoded direct URL is appended to the `proxy_base` parameter as a `url` query parameter
        - the file name (`file.ext`) is appended as a `name` query parameter

        E.g. With a proxy base `https://example.com`, a direct URL `https://example.com/file.ext` becomes:
        `https://example.com?sha256=x&quickxor=y&url=aHR0cHM6Ly9leGFtcGxlLmNvbS9maWxlLnR4dA%3D%3D&name=file.ext`
        """
        proxy = bool(self._list_fields["unrestricted"] and self._proxy_base)
        direct = self._drive_item["webUrl"]

        params = {"sha256": self.sha256, "quickxor": self.quickxor}
        base = self._proxy_base if proxy else direct
        if proxy:
            params.update({"url": urlsafe_b64encode(direct.encode()).decode(), "name": self.name})

        parsed = urlparse(base)
        query = [(key, value) for key, value in parse_qsl(parsed.query, keep_blank_values=True) if key not in params]
        query.extend(params.items())
        return urlunparse(parsed._replace(query=urlencode(query)))

    @property
    def distributor(self) -> Contact:
        """
        Artefact ISO distributor.

        Static value based on service type.
        """
        return MICROSOFT_DISTRIBUTOR

    @property
    def distribution_transfer_opt(self) -> TransferOption:
        """Generate artefact ISO transfer option with optional transfer option title/description."""
        return TransferOption(
            size=Size(unit="bytes", magnitude=self.size_bytes),
            online_resource=OnlineResource(
                href=self.url,
                title=self.format.name,
                description=self.format.description,
                function=OnlineResourceFunctionCode.DOWNLOAD,
            ),
        )

    @property
    def distribution_option(self) -> Distribution:
        """Artefact ISO transfer option for item."""
        return Distribution(
            format=self.distribution_format,
            distributor=self.distributor,
            transfer_option=self.distribution_transfer_opt,
        )
