from __future__ import annotations

from typing import NamedTuple, TypedDict


class ResourceMetadata(TypedDict):
    """SharePoint list metadata required for resource folders."""

    resource_id: str
    unrestricted: bool


class ArtefactMetadata(TypedDict):
    """SharePoint list metadata required for file artefacts."""

    resource_id: str
    artefact_id: str
    artefact_fmt: str
    artefact_sha256: str
    unrestricted: bool


class SharePointPermissions(NamedTuple):
    """Return type for `get_sharepoint_permissions`."""

    group_ids: set[str]
    unrestricted: bool
