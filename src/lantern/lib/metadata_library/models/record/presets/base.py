from typing import Any

from lantern.lib.metadata_library.models.record import DataQuality, Metadata, Record
from lantern.lib.metadata_library.models.record.elements.common import Contact, Contacts
from lantern.lib.metadata_library.models.record.enums import ContactRoleCode
from lantern.lib.metadata_library.models.record.presets.citation import make_magic_citation
from lantern.lib.metadata_library.models.record.presets.conformance import MAGIC_PROFILE_V1
from lantern.lib.metadata_library.models.record.presets.contacts import make_magic_role
from lantern.lib.metadata_library.models.record.presets.identifiers import make_bas_cat


class RecordMagicDiscoveryV1(Record):
    """
    A Record based on the MAGIC Discovery profile v1.

    Use this base record when creating records that originate from MAGIC to pre-configure elements with conventional
    values. Specifically:
    - the conventional MAGIC contact (appendix 2) as the metadata, and an identification, point of contact
    - the conventional MAGIC Discovery profile domain consistency element (appendix 1)
    - a BAS Data Catalogue identifier based on the file identifier

    This class also provides a convince method for setting a citation based on MAGIC's conventions from record details.

    See https://metadata-standards.data.bas.ac.uk/profiles/magic-discovery-v1 for more information about this profile.
    """

    def __init__(self, **kwargs: Any) -> None:
        """Process defaults for required properties."""
        date_stamp = None
        if "date_stamp" in kwargs:
            date_stamp = kwargs["date_stamp"]
            del kwargs["date_stamp"]

        kwargs["metadata"] = Metadata(
            contacts=Contacts([make_magic_role([ContactRoleCode.POINT_OF_CONTACT])]), date_stamp=date_stamp
        )
        super().__init__(**kwargs)

    def __post_init__(self) -> None:
        """Process defaults."""
        RecordMagicDiscoveryV1._set_magic_poc(self.identification.contacts)

        self_identifier = make_bas_cat(self.file_identifier)
        if self_identifier not in self.identification.identifiers:
            self.identification.identifiers.append(self_identifier)

        profile = MAGIC_PROFILE_V1
        if self.data_quality is None:
            self.data_quality = DataQuality()
        if profile not in self.data_quality.domain_consistency:
            self.data_quality.domain_consistency.append(profile)

        super().__post_init__()

    @staticmethod
    def _set_magic_poc(contacts: list[Contact]) -> None:
        """Ensure a list of contacts contains MAGIC as a point of contact."""
        poc = make_magic_role([ContactRoleCode.POINT_OF_CONTACT])

        # skip exact match
        if poc in contacts:
            return

        # skip with overlapping roles
        for contact in contacts:
            if contact.eq_contains_roles(poc):
                return

        # append to existing contact with non-overlapping roles
        for i, contact in enumerate(contacts):
            if contact.eq_no_roles(poc):
                contacts[i].role.extend(poc.role)
                return

        # append new contact
        contacts.append(poc)

    @classmethod
    def loads(cls, value: dict) -> "RecordMagicDiscoveryV1":
        """Create a Record from a dict loaded from a JSON schema instance."""
        record = super().loads(value)
        return cls(
            file_identifier=record.file_identifier,
            hierarchy_level=record.hierarchy_level,
            metadata=record.metadata,
            identification=record.identification,
            data_quality=record.data_quality,
            distribution=record.distribution,
        )

    def set_citation(self) -> None:
        """Set citation using record details as per `make_magic_citation` preset."""
        self.identification.other_citation_details = make_magic_citation(
            title=self.identification.title,
            hierarchy_level=self.hierarchy_level,
            edition=self.identification.edition,
            publication_date=self.identification.dates.publication,
            identifiers=self.identification.identifiers,
        )
