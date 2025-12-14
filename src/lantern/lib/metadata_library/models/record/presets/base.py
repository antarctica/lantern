from datetime import date
from typing import Any

from lantern.lib.metadata_library.models.record.elements.common import Contact, Contacts
from lantern.lib.metadata_library.models.record.elements.metadata import Metadata
from lantern.lib.metadata_library.models.record.enums import ContactRoleCode
from lantern.lib.metadata_library.models.record.presets.citation import make_magic_citation
from lantern.lib.metadata_library.models.record.presets.conformance import MAGIC_DISCOVERY_V2
from lantern.lib.metadata_library.models.record.presets.contacts import UKRI_RIGHTS_HOLDER, make_magic_role
from lantern.lib.metadata_library.models.record.presets.identifiers import make_bas_cat
from lantern.lib.metadata_library.models.record.record import Record


class RecordMagicDiscoveryV2(Record):
    """
    A Record based on the MAGIC Discovery profile v2.

    Use when creating records for MAGIC resources to pre-configure elements with conventional values - specifically:
    - the conventional MAGIC contact (appendix 2) as the metadata, and an identification, point of contact
    - the conventional MAGIC Discovery profile domain consistency element (appendix 1)
    - a BAS Data Catalogue identifier based on the file identifier

    This class also:
    - sets UKRI as a default copyright holder contact
    - sets a default citation based on MAGIC's conventions and record details

    See https://metadata-standards.data.bas.ac.uk/profiles/magic-discovery/v2/ for more information about this profile.
    """

    def __init__(self, **kwargs: Any) -> None:
        """Process defaults."""
        date_stamp: date | None = kwargs.pop("date_stamp", None)
        kwargs["metadata"] = Metadata(
            contacts=Contacts([make_magic_role({ContactRoleCode.POINT_OF_CONTACT})]), date_stamp=date_stamp
        )
        super().__init__(**kwargs)

    def __post_init__(self) -> None:
        """Process defaults."""
        RecordMagicDiscoveryV2._set_magic_poc(self.identification.contacts)
        RecordMagicDiscoveryV2._set_ukri_rights(self.identification.contacts)

        self_identifier = make_bas_cat(self.file_identifier)  # ty: ignore[invalid-argument-type]
        if self_identifier not in self.identification.identifiers:
            self.identification.identifiers.append(self_identifier)

        self._set_citation()

        profile = MAGIC_DISCOVERY_V2
        if profile not in self.data_quality.domain_consistency:
            self.data_quality.domain_consistency.append(profile)

        super().__post_init__()

    @staticmethod
    def _ensure_contact(target_contact: Contact, existing_contacts: list[Contact]) -> None:
        """Ensure a list of contacts contains a desired contact."""
        # skip exact match
        if target_contact in existing_contacts:
            return

        # skip with overlapping roles
        for contact in existing_contacts:
            if contact.eq_contains_roles(target_contact):
                return

        # append to existing contact with non-overlapping roles
        for i, contact in enumerate(existing_contacts):
            if contact.eq_no_roles(target_contact):
                existing_contacts[i].role = existing_contacts[i].role.union(target_contact.role)
                return

        # append new contact
        existing_contacts.append(target_contact)

    @staticmethod
    def _set_magic_poc(contacts: list[Contact]) -> None:
        """Ensure a list of contacts contains MAGIC as a point of contact."""
        poc = make_magic_role({ContactRoleCode.POINT_OF_CONTACT})
        RecordMagicDiscoveryV2._ensure_contact(poc, contacts)

    @staticmethod
    def _set_ukri_rights(contacts: list[Contact]) -> None:
        """Ensure a list of contacts contains UKRI as a rights holder contact."""
        RecordMagicDiscoveryV2._ensure_contact(UKRI_RIGHTS_HOLDER, contacts)

    def _set_citation(self) -> None:
        """Set citation using record details as per `make_magic_citation` preset."""
        self.identification.other_citation_details = make_magic_citation(
            title=self.identification.title,
            hierarchy_level=self.hierarchy_level,
            edition=self.identification.edition,
            publication_date=self.identification.dates.publication,
            identifiers=self.identification.identifiers,
        )

    # noinspection PyMethodOverriding
    @classmethod
    # noinspection PyMethodOverridingInspection
    def loads(cls, value: dict) -> "RecordMagicDiscoveryV2":  # ty: ignore[invalid-method-override]
        """
        Create a Record from a dict loaded from a JSON schema instance.

        Known to violate method override rules due to differing signature.
        """
        record = super().loads(value)
        return cls(
            file_identifier=record.file_identifier,
            hierarchy_level=record.hierarchy_level,
            metadata=record.metadata,
            identification=record.identification,
            data_quality=record.data_quality,
            distribution=record.distribution,
        )
