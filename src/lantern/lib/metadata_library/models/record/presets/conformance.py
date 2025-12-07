from datetime import date

from lantern.lib.metadata_library.models.record.elements.common import Citation, Contacts, Date, Dates
from lantern.lib.metadata_library.models.record.elements.data_quality import DomainConsistency
from lantern.lib.metadata_library.models.record.enums import ContactRoleCode
from lantern.lib.metadata_library.models.record.presets.contacts import make_magic_role

MAGIC_DISCOVERY_V1 = DomainConsistency(
    specification=Citation(
        title="British Antarctic Survey (BAS) Mapping and Geographic Information Centre (MAGIC) Discovery Metadata Profile",
        href="https://metadata-standards.data.bas.ac.uk/profiles/magic-discovery/v1/",
        dates=Dates(publication=Date(date=date(2024, 11, 1))),
        edition="1",
        contacts=Contacts([make_magic_role(roles={ContactRoleCode.PUBLISHER})]),
    ),
    explanation="Resource within scope of British Antarctic Survey (BAS) Mapping and Geographic Information Centre (MAGIC) Discovery Metadata Profile.",
    result=True,
)

MAGIC_DISCOVERY_V2 = DomainConsistency(
    specification=Citation(
        title="British Antarctic Survey (BAS) Mapping and Geographic Information Centre (MAGIC) Discovery Metadata Profile",
        href="https://metadata-standards.data.bas.ac.uk/profiles/magic-discovery/v2/",
        dates=Dates(publication=Date(date=date(2025, 11, 24))),
        edition="2",
        contacts=Contacts([make_magic_role(roles={ContactRoleCode.PUBLISHER})]),
    ),
    explanation="Resource within scope of British Antarctic Survey (BAS) Mapping and Geographic Information Centre (MAGIC) Discovery Metadata Profile.",
    result=True,
)
