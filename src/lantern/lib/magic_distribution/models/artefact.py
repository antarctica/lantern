from __future__ import annotations

import hashlib
import uuid
from abc import ABC, abstractmethod
from base64 import b64encode, urlsafe_b64encode
from functools import cached_property
from typing import TYPE_CHECKING, Final

from quickxorhash import quickxorhash  # ty: ignore[unresolved-import]

from lantern.lib.magic_distribution.formats import (
    ArtefactFormat,
    ArtefactFormatLabel,
    ArtefactFormats,
)
from lantern.lib.magic_distribution.sharepoint.models.types import ArtefactMetadata
from lantern.lib.metadata_library.models.record.elements.distribution import (
    Format,
)

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


class ArtefactService(ArtefactBase, ABC):
    """Artefact representing a service."""

    def __init__(self, resource_id: str, artefact_name: str, artefact_url: str) -> None:
        super().__init__(resource_id)
        self._artefact_name = artefact_name
        self._artefact_url = artefact_url

    @property
    def _artefact_hash(self) -> str:
        """Value to use for constructing the artefact ID."""
        return urlsafe_b64encode(self._artefact_url.encode()).decode()

    @property
    def name(self) -> str:
        """Artefact name."""
        return self._artefact_name
