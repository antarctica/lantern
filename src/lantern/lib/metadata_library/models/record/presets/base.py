import logging
from datetime import date
from typing import Any

from bas_metadata_library.standards.magic_administration.v1 import AdministrationMetadata
from bas_metadata_library.standards.magic_administration.v1.utils import AdministrationKeys

from lantern.lib.metadata_library.models.record.elements.common import Contact, Contacts
from lantern.lib.metadata_library.models.record.elements.data_quality import DomainConsistency
from lantern.lib.metadata_library.models.record.elements.metadata import Metadata
from lantern.lib.metadata_library.models.record.enums import ContactRoleCode
from lantern.lib.metadata_library.models.record.presets.citation import make_magic_citation
from lantern.lib.metadata_library.models.record.presets.conformance import MAGIC_ADMINISTRATION_V1, MAGIC_DISCOVERY_V2
from lantern.lib.metadata_library.models.record.presets.contacts import UKRI_RIGHTS_HOLDER, make_magic_role
from lantern.lib.metadata_library.models.record.presets.identifiers import make_bas_cat
from lantern.lib.metadata_library.models.record.record import Record
from lantern.lib.metadata_library.models.record.utils.admin import set_admin


class RecordMagic(Record):
    """
    Create a Record based on MAGIC metadata profiles and other conventional values.

    At a high-level, this method creates a record complaint with:
    - the MAGIC Discovery profile (V2, https://metadata-standards.data.bas.ac.uk/profiles/magic-discovery/v2/)
    - the MAGIC Administration profile (V1, https://metadata-standards.data.bas.ac.uk/profiles/magic-administration/v1/)

    At a lower level, this method extends a minimal ISO record with:
    - a domain consistency element for the MAGIC Discovery profile (appendix 1)
    - the conventional MAGIC contact (Discovery profile appendix 2) as the metadata and identification point of contact
    - an identification identifier using the Data Catalogue namespace based on the file identifier
    - an identification contact for UKRI as a rights holder
    - an identification citation based on the Harvard APA style, MAGIC conventions and record details
    - if admin metadata is included, a domain consistency element for the MAGIC Administration profile (appendix 1)
    - if admin metadata is included, the metadata encoded within the identification supplemental info element

    Examples:
    1. Minimal, without admin metadata:
    ```
    RecordMagic(
        file_identifier="x",
        hierarchy_level=HierarchyLevelCode.DATASET,
        identification=Identification(title="x", abstract="x", dates=Dates(creation=Date(date=datetime.now(tz=UTC))))
    )
    ```

    2. Minimal, with admin metadata:
    ```
    RecordMagic(
        file_identifier="x",
        hierarchy_level=HierarchyLevelCode.DATASET,
        identification=Identification(title="x", abstract="x", dates=Dates(creation=Date(date=datetime.now(tz=UTC)))),
        admin_keys=AdministrationKeys,
        admin_meta=AdministrationMetadata,
    )
    ```

    """

    magic_poc = make_magic_role({ContactRoleCode.POINT_OF_CONTACT})

    def __init__(self, **kwargs: Any) -> None:
        """
        Process defaults.

        Inject metadata element with optional datestamp.
        """
        # prepare metadata element
        date_stamp: date | None = kwargs.pop("date_stamp", None)
        kwargs["metadata"] = Metadata(contacts=Contacts([self.magic_poc]), date_stamp=date_stamp)

        # prepare optional administration element
        self._admin_keys: AdministrationKeys | None = kwargs.pop("admin_keys", None)
        self._admin_meta: AdministrationMetadata | None = kwargs.pop("admin_meta", None)

        super().__init__(**kwargs)

    def __post_init__(self) -> None:
        """Process defaults and set optional admin metadata."""
        profiles = [MAGIC_DISCOVERY_V2]

        self._set_contacts()
        self._set_cat_identifier()
        self._set_citation()

        # create optional administration element if provided
        if self._admin_keys is not None and self._admin_meta is not None:
            set_admin(keys=self._admin_keys, record=self, admin_meta=self._admin_meta)
            profiles.append(MAGIC_ADMINISTRATION_V1)

        self._set_profiles(profiles)

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

    def _set_contacts(self) -> None:
        """
        Ensure record identification contains conventional contacts.

        MAGIC as a point of contact and UKRI as a rights holder
        """
        self._ensure_contact(self.magic_poc, self.identification.contacts)
        self._ensure_contact(UKRI_RIGHTS_HOLDER, self.identification.contacts)

    def _set_cat_identifier(self) -> None:
        """Ensure an identifier within the Data Catalogue namespace based on the file identifier."""
        self_identifier = make_bas_cat(self.file_identifier)  # ty:ignore[invalid-argument-type]
        if self_identifier not in self.identification.identifiers:
            self.identification.identifiers.append(self_identifier)

    def _set_citation(self) -> None:
        """Set citation using record details as per `make_magic_citation` preset if not already set."""
        if self.identification.other_citation_details:
            return
        self.identification.other_citation_details = make_magic_citation(
            title=self.identification.title,
            hierarchy_level=self.hierarchy_level,
            edition=self.identification.edition,
            publication_date=self.identification.dates.publication,
            identifiers=self.identification.identifiers,
        )

    def _set_profiles(self, profiles: list[DomainConsistency]) -> None:
        """Ensure record identification / data quality contains MAGIC profiles."""
        for profile in profiles:
            if profile not in self.data_quality.domain_consistency:
                self.data_quality.domain_consistency.append(profile)

    @classmethod
    def loads(cls, value: dict, check_supported: bool = False, logger: logging.Logger | None = None) -> "Record":
        """
        Create a Record from a dict loaded from a JSON schema instance.

        Known to violate method override rules due to differing signature.
        """
        record = super().loads(value=value, check_supported=check_supported, logger=logger)
        return cls(
            file_identifier=record.file_identifier,
            hierarchy_level=record.hierarchy_level,
            metadata=record.metadata,
            identification=record.identification,
            data_quality=record.data_quality,
            distribution=record.distribution,
        )
