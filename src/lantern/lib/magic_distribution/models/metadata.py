from typing import TypedDict


class ResourceMetadata(TypedDict):
    """SharePoint list metadata required for resource folders."""

    resource_id: str
    unrestricted: bool


class ArtefactMetadata(TypedDict):
    """SharePoint list metadata required for artefacts."""

    resource_id: str
    artefact_id: str
    artefact_fmt: str
    unrestricted: bool
