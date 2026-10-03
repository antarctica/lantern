import hashlib
import uuid
from abc import ABC, abstractmethod
from base64 import b64encode, urlsafe_b64encode
from functools import cached_property
from typing import TYPE_CHECKING, Final, get_type_hints
from urllib.parse import urlencode, urlparse, urlunparse

from quickxorhash import quickxorhash  # ty: ignore[unresolved-import]

from lantern.lib.magic_distribution.formats import (
    ArtefactFormat,
    ArtefactFormatLabel,
    ArtefactFormats,
    ArtefactFormatUnknownError,
)
from lantern.lib.magic_distribution.models.metadata import ArtefactMetadata
from lantern.lib.metadata_library.models.record.elements.distribution import Format

if TYPE_CHECKING:
    from pathlib import Path


class ArtefactBase(ABC):
    """Artefact abstract base class."""

    _artefact_namespace: Final[str] = "https://artefacts.data.bas.ac.uk"

    def __init__(self, resource_id: str) -> None:
        self._resource_id = resource_id

    @property
    @abstractmethod
    def _artefact_hash(self) -> str:
        """Value to use for constructing the artefact ID."""

    @cached_property
    def artefact_id(self) -> str:
        """
        Artefact identifier.

        Derived from resource identifier and a suitable hash of the artefact given by `_artefact_hash`.
        The URL (https://artefacts.data.bas.ac.uk/) is used as a namespace only and will not resolve to the artefact.
        """
        name = f"{self._artefact_namespace}/{self._resource_id}:{self._artefact_hash}"
        return str(uuid.uuid5(uuid.NAMESPACE_URL, name))

    @property
    def resource_id(self) -> str:
        """Resource identifier."""
        return self._resource_id

    @property
    @abstractmethod
    def format(self) -> ArtefactFormat:
        """Artefact format."""

    @property
    def format_label(self) -> ArtefactFormatLabel:
        """Artefact format label."""
        return self.format.label

    @property
    def distribution_format(self) -> Format | None:
        """Artefact format as an ISO distribution format."""
        return Format(format=self.format.name, href=self.format.registration)

    @property
    @abstractmethod
    def name(self) -> str:
        """Artefact name."""

    @property
    @abstractmethod
    def size_bytes(self) -> int | None:
        """Optional artefact size in bytes."""

    @abstractmethod
    def validate_format(self) -> None:
        """
        Check artefact is a supported type.

        May raise `ArtefactFormatUnknownError` or `ArtefactFormatNotSupportedError` if unknown or explicitly unsupported.
        """


class ArtefactFile(ArtefactBase):
    """Artefact representing a file."""

    @property
    def _artefact_hash(self) -> str:
        """Value to use for constructing the artefact ID."""
        return self.sha256

    @property
    @abstractmethod
    def data(self) -> bytes:
        """Artefact content as bytes."""

    @property
    @abstractmethod
    def size_bytes(self) -> int:
        """Artefact size in bytes."""

    @cached_property
    def quickxor(self) -> str:
        """Microsoft QuickXorHash."""
        h = quickxorhash()
        chunk_size = 8192
        data = self.data
        for i in range(0, len(data), chunk_size):
            chunk = bytes(data[i : i + chunk_size])
            h.update(chunk)
        return b64encode(h.digest()).decode()

    @cached_property
    def sha256(self) -> str:
        """SHA 256 hash."""
        h = hashlib.sha256()
        chunk_size = 8192
        data = self.data
        for i in range(0, len(data), chunk_size):
            chunk = bytes(data[i : i + chunk_size])
            h.update(chunk)
        return h.hexdigest()

    @property
    def deposit_metadata(self) -> ArtefactMetadata:
        """
        Artefact metadata required for file deposits.

        The required `unrestricted` property depends on access permissions artefacts don't hold and defaults to False.
        This property should be overridden in a context where access permissions are known and can be accurately set.
        """
        return ArtefactMetadata(
            resource_id=self.resource_id,
            artefact_id=self.artefact_id,
            artefact_fmt=self.format_label.name,
            artefact_sha256=self.sha256,
            unrestricted=False,
        )


class ArtefactServicePlaceholder(ArtefactBase):
    """
    Artefact representing a service.

    Placeholder implementation to show an alternative to file artefacts.
    """

    def __init__(
        self, resource_id: str, artefact_name: str, artefact_url: str, artefact_format: ArtefactFormat
    ) -> None:
        super().__init__(resource_id)
        self._artefact_name = artefact_name
        self._artefact_url = artefact_url
        self._artefact_format = artefact_format

    @property
    def _artefact_hash(self) -> str:
        """Value to use for constructing the artefact ID."""
        return urlsafe_b64encode(self._artefact_url.encode()).decode()

    @property
    def name(self) -> str:
        """Artefact name."""
        return self._artefact_name

    @property
    def format(self) -> ArtefactFormat:
        """Artefact format."""
        return self._artefact_format

    @property
    def size_bytes(self) -> None:
        """Artefact size in bytes."""
        return None

    def validate_format(self) -> None:
        """Check service is a supported type."""
        raise NotImplementedError() from None


class ArtefactLocalFile(ArtefactFile):
    """
    File artefact for a local file.

    Intended for file artefacts before they've been deposited for use with scripts, CLIs, etc.

    Uses the contents and properties of a file directly to determine its format, size, name, etc. and to allow upload
    to a data access system.

    Note: This class assumes the entire file contents can be read into memory, which is a known limitation. Care should
    be when handling large files.
    """

    def __init__(self, resource_id: str, artefact_path: Path) -> None:
        super().__init__(resource_id)
        self._artefact = artefact_path

    def __repr__(self) -> str:
        """Class representation."""
        return f"<ArtefactLocal: {self.name}, {self.format.name}, {self.size_bytes} bytes, sha256: {self.sha256}>"

    @property
    def format(self) -> ArtefactFormat:
        """
        Artefact format.

        Raises ArtefactFormatUnknownError, ArtefactFormatNotSupportedError if not supported.
        """
        return ArtefactFormats.get_file_format(self._artefact, name=self.name)

    def validate_format(self) -> None:
        """
        Check file is a supported type.

        May raise `ArtefactFormatUnknownError` or `ArtefactFormatNotSupportedError` if unknown or explicitly unsupported.
        """
        ArtefactFormats.check_file_supported(self._artefact, name=self.name)

    @property
    def name(self) -> str:
        """Artefact name."""
        return self._artefact.name

    @property
    def data(self) -> bytes:
        """Artefact content as bytes."""
        return self._artefact.read_bytes()

    @property
    def size_bytes(self) -> int:
        """Artefact size in bytes."""
        return self._artefact.stat().st_size


class ArtefactSharePointFile(ArtefactFile):
    """
    File artefact for a remote file stored in SharePoint.

    Intended for, and specific to, file artefacts deposited in the MAGIC Resource Distribution SharePoint site.

    Uses metadata recorded about a file to state its format, size, name, etc. Does not allow access to file content.

    Provides an access URL to access the artefact file for use in distribution options within resource records.

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
    def artefact_id(self) -> str:
        """Artefact identifier."""
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
            return ArtefactFormats.get_label(label)

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
    def data(self) -> memoryview:
        """Artefact content as bytes."""
        raise NotImplementedError() from None

    @property
    def size_bytes(self) -> int:
        """Artefact size in bytes."""
        return self._drive_item["size"]

    @property
    def quickxor(self) -> str:
        """Microsoft QuickXorHash."""
        return self._drive_item["file"]["hashes"]["quickXorHash"]

    @property
    def sha256(self) -> str:
        """
        SHA 256 hash.

        This value is set at upload, it is not based on the underlying file stored in SharePoint and so cannot be used
        to determine if a file has changed internally (see `quickxor`) but can be used for external comparisons.
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

        File checksum values are appended to the direct URL for checking the integrity of downloaded files.

        E.g. A direct URL `https://example.com/file.ext` becomes: `https://example.com/file.ext?sha256=x&quickxor=y`.

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
        return urlunparse(urlparse(base)._replace(query=urlencode(params)))
