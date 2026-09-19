from lantern.lib.metadata_library.models.record.elements.common import Address, Contact, ContactIdentity, OnlineResource
from lantern.lib.metadata_library.models.record.enums import ContactRoleCode, OnlineResourceFunctionCode


def make_bas_role(
    roles: set[ContactRoleCode],
    team_name: str | None = None,
    team_email: str | None = None,
    team_url: str | None = None,
    team_url_title: str | None = None,
) -> Contact:
    """BAS organisation with configurable team name and roles."""
    _base_name = "British Antarctic Survey"
    _base_url = "https://www.bas.ac.uk"
    title = f"{team_url_title} - BAS public website" if team_url_title else "British Antarctic Survey public website"
    description = (
        f"General information about the {team_url_title} from the British Antarctic Survey (BAS) public website."
        if team_url_title
        else "General information about the British Antarctic Survey (BAS)."
    )

    return Contact(
        organisation=ContactIdentity(
            name=f"{team_name}, {_base_name}" if team_name else _base_name,
            href="https://ror.org/01rhff309",
            title="ror",
        ),
        phone="+44 (0)1223 221400",
        email=team_email or None,
        address=Address(
            delivery_point="British Antarctic Survey, High Cross, Madingley Road",
            city="Cambridge",
            administrative_area="Cambridgeshire",
            postal_code="CB3 0ET",
            country="United Kingdom",
        ),
        online_resource=OnlineResource(
            href=team_url or _base_url,
            title=title,
            description=description,
            function=OnlineResourceFunctionCode.INFORMATION,
        ),
        role=roles,
    )


def make_magic_role(roles: set[ContactRoleCode]) -> Contact:
    """MAGIC team with configurable roles."""
    contact = make_bas_role(
        roles=roles,
        team_name="Mapping and Geographic Information Centre",
        team_email="magic@bas.ac.uk",
        team_url="https://www.bas.ac.uk/teams/magic",
        team_url_title="Mapping and Geographic Information Centre (MAGIC)",
    )
    # Fix inconsistency with online resource description, the format of which is required by external profiles.
    contact.online_resource.description = contact.online_resource.description.replace(  # ty: ignore[invalid-assignment, unresolved-attribute]
        "Mapping and Geographic Information Centre (MAGIC)", "BAS Mapping and Geographic Information Centre (MAGIC)"
    )
    return contact


ESRI_DISTRIBUTOR = Contact(
    organisation=ContactIdentity(
        name="Environmental Systems Research Institute", href="https://ror.org/0428exr50", title="ror"
    ),
    address=Address(
        delivery_point="380 New York Street",
        city="Redlands",
        administrative_area="California",
        postal_code="92373",
        country="United States of America",
    ),
    online_resource=OnlineResource(
        href="https://www.esri.com",
        title="GIS Mapping Software, Location Intelligence & Spatial Analytics | Esri",
        description="Corporate website for Environmental Systems Research Institute (ESRI).",
        function=OnlineResourceFunctionCode.INFORMATION,
    ),
    role={ContactRoleCode.DISTRIBUTOR},
)

MICROSOFT_DISTRIBUTOR = Contact(
    organisation=ContactIdentity(name="Microsoft", href="https://ror.org/00d0nc645", title="ror"),
    address=Address(
        delivery_point="One Microsoft Way",
        city="Redmond",
        administrative_area="Washington",
        postal_code="98052",
        country="United States of America",
    ),
    online_resource=OnlineResource(
        href="https://www.microsoft.com",
        title="Microsoft - AI, Cloud, Productivity, Computing, Gaming & Apps",
        description="Corporate website for the Microsoft Corporation.",
        function=OnlineResourceFunctionCode.INFORMATION,
    ),
    role={ContactRoleCode.DISTRIBUTOR},
)

MAGIC_DISTRIBUTOR = make_magic_role(roles={ContactRoleCode.DISTRIBUTOR})

UKRI_RIGHTS_HOLDER = Contact(
    organisation=ContactIdentity(name="UK Research and Innovation", href="https://ror.org/001aqnf71", title="ror"),
    address=Address(
        delivery_point="Polaris House",
        city="Swindon",
        postal_code="SN2 1FL",
        country="United Kingdom",
    ),
    online_resource=OnlineResource(
        href="https://www.ukri.org",
        title="UKRI - UK Research and Innovation",
        description="Corporate website for UK Research and Innovation (UKRI).",
        function=OnlineResourceFunctionCode.INFORMATION,
    ),
    role={ContactRoleCode.RIGHTS_HOLDER},
)
