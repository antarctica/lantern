from lantern.models.record.elements.common import Address, Contact, ContactIdentity, OnlineResource
from lantern.models.record.enums import ContactRoleCode, OnlineResourceFunctionCode


def make_magic_role(roles: list[ContactRoleCode]) -> Contact:
    """MAGIC team with configurable roles."""
    return Contact(
        organisation=ContactIdentity(
            name="Mapping and Geographic Information Centre, British Antarctic Survey",
            href="https://ror.org/01rhff309",
            title="ror",
        ),
        phone="+44 (0)1223 221400",
        email="magic@bas.ac.uk",
        address=Address(
            delivery_point="British Antarctic Survey, High Cross, Madingley Road",
            city="Cambridge",
            administrative_area="Cambridgeshire",
            postal_code="CB3 0ET",
            country="United Kingdom",
        ),
        online_resource=OnlineResource(
            href="https://www.bas.ac.uk/teams/magic",
            title="Mapping and Geographic Information Centre (MAGIC) - BAS public website",
            description="General information about the BAS Mapping and Geographic Information Centre (MAGIC) from the British Antarctic Survey (BAS) public website.",
            function=OnlineResourceFunctionCode.INFORMATION,
        ),
        role=roles,
    )


def make_esri_distributor() -> Contact:
    """Esri as distributor."""
    return Contact(
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
        role=[ContactRoleCode.DISTRIBUTOR],
    )
