from datetime import date

from assets_tracking_service.lib.bas_data_catalogue.models.record.elements.common import Citation, Contacts, Date, Dates
from assets_tracking_service.lib.bas_data_catalogue.models.record.elements.data_quality import DomainConsistency
from assets_tracking_service.lib.bas_data_catalogue.models.record.enums import ContactRoleCode
from assets_tracking_service.lib.bas_data_catalogue.models.record.presets.contacts import make_magic_role

MAGIC_PROFILE_V1 = DomainConsistency(
    specification=Citation(
        title="British Antarctic Survey (BAS) Mapping and Geographic Information Centre (MAGIC) Discovery Metadata Profile",
        href="https://metadata-standards.data.bas.ac.uk/profiles/magic-discovery-v1/",
        dates=Dates(publication=Date(date=date(2024, 11, 1))),
        edition="1",
        contacts=Contacts([make_magic_role(roles=[ContactRoleCode.PUBLISHER])]),
    ),
    explanation="Resource within scope of British Antarctic Survey (BAS) Mapping and Geographic Information Centre (MAGIC) Discovery Metadata Profile.",
    result=True,
)
