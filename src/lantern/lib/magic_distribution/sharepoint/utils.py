from __future__ import annotations

from typing import TYPE_CHECKING

from requests.auth import AuthBase

from lantern.lib.magic_distribution.sharepoint.models.types import SharePointPermissions
from lantern.lib.metadata_library.models.record.presets.admin import OPEN_ACCESS

if TYPE_CHECKING:
    from bas_metadata_library.standards.magic_administration.v1 import AdministrationMetadata
    from requests import PreparedRequest


class HTTPBearerTokenAuth(AuthBase):
    """
    Attaches bearer token authentication to the given request object.

    Intended for services using OAuth.
    """

    def __init__(self, token: str) -> None:
        self._token = token

    def __call__(self, r: PreparedRequest) -> PreparedRequest:  # noqa: D102
        r.headers["Authorization"] = f"Bearer {self._token}"
        return r


def get_sharepoint_permissions(
    admin_meta: AdministrationMetadata | None, groups_mapping: dict[str, list[str]]
) -> SharePointPermissions:
    """
    Convert resource access permissions from administration metadata into groups understood by SharePoint.

    Returns a tuple of resolved group identifiers and boolean for whether unrestricted access is allowed.

    Note:
    - unrestricted / open-access permissions MUST be exclusive and use a well-known permission
    - the directory of any other permissions MUST match the tenancy of the deposit SharePoint site (i.e. NERC)
    - permissions targeting other directories are ignored
    - permission expiry date times are ignored

    Permission referencing well-known group aliases/presets (e.g. `~bas-staff`) need to be resolved to real groups
    using a provided mapping. Aliases CAN resolve to multiple groups, e.g. `{'~x': ['123', '234']}`).

    A default mapping is not provided as group identifiers are not included out of an abundance of caution, but are not
    considered sensitive.
    """
    if not admin_meta:
        return SharePointPermissions(group_ids=set(), unrestricted=False)
    if admin_meta.resource_permissions == [OPEN_ACCESS]:
        return SharePointPermissions(group_ids=set(), unrestricted=True)

    # filter out permissions for other directories
    groups = {p.group for p in admin_meta.resource_permissions if p.directory == "~nerc"}
    # resolve any group mappings
    groups = {mapped_group for group in groups for mapped_group in groups_mapping.get(group, [group])}

    return SharePointPermissions(group_ids=groups, unrestricted=False)
