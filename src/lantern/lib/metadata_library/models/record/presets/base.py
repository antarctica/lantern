import logging
from datetime import date
from typing import Any

from bas_metadata_library.standards.magic_administration.v1 import AdministrationMetadata
from bas_metadata_library.standards.magic_administration.v1.utils import AdministrationKeys

from lantern.lib.metadata_library.models.record.elements.common import Constraints, Contacts
from lantern.lib.metadata_library.models.record.elements.data_quality import DomainConsistency
from lantern.lib.metadata_library.models.record.elements.metadata import Metadata
from lantern.lib.metadata_library.models.record.enums import ContactRoleCode
from lantern.lib.metadata_library.models.record.presets.admin import OPEN_ACCESS as OPEN_ACCESS_PERMISSION
from lantern.lib.metadata_library.models.record.presets.citation import make_magic_citation
from lantern.lib.metadata_library.models.record.presets.conformance import MAGIC_ADMINISTRATION_V1, MAGIC_DISCOVERY_V2
from lantern.lib.metadata_library.models.record.presets.constraints import CC_BY_ND_V4, OGL_V3, OPEN_ACCESS
from lantern.lib.metadata_library.models.record.presets.contacts import UKRI_RIGHTS_HOLDER, make_magic_role
from lantern.lib.metadata_library.models.record.presets.identifiers import make_bas_cat
from lantern.lib.metadata_library.models.record.record import Record
from lantern.lib.metadata_library.models.record.utils.admin import get_admin, set_admin


class RecordMagic(Record):
    """
    Create a Record based on MAGIC metadata profiles and other conventional values.

    At a high-level, this method creates a record complaint with:
    - the MAGIC Discovery profile (V2, https://metadata-standards.data.bas.ac.uk/profiles/magic-discovery/v2/)
    - the MAGIC Administration profile (V1, https://metadata-standards.data.bas.ac.uk/profiles/magic-administration/v1/)

    At a lower level, this method extends a minimal ISO record with:
    - a domain consistency element for the MAGIC Discovery profile (appendix 1)
    - default metadata constraints for open access and the CC BY-ND-v4 licence
    - the required MAGIC contact (Discovery profile appendix 2) as the metadata and identification point of contact
    - an identification identifier using the Data Catalogue namespace based on the file identifier
    - an identification contact for UKRI as a rights holder
    - an identification contact for MAGIC as a publisher
    - an identification citation based on the Harvard APA style with MAGIC conventions and record details
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
        admin_keys=AdministrationKeys(...),
        admin_meta=AdministrationMetadata(id="x"),
    )
    ```

    """

    def __init__(self, **kwargs: Any) -> None:
        """
        Process defaults.

        Inject metadata element with optional datestamp.
        """
        # prepare metadata element
        date_stamp: date | None = kwargs.pop("date_stamp", None)
        magic = make_magic_role({ContactRoleCode.POINT_OF_CONTACT})
        kwargs["metadata"] = Metadata(contacts=Contacts([magic]), date_stamp=date_stamp)

        # prepare optional administration element
        self._admin_keys: AdministrationKeys | None = kwargs.pop("admin_keys", None)
        self._admin_meta: AdministrationMetadata | None = kwargs.pop("admin_meta", None)

        # prepare profiles
        self._profiles: list[DomainConsistency] = [MAGIC_DISCOVERY_V2]

        super().__init__(**kwargs)

    def __post_init__(self) -> None:
        """Process defaults and set optional admin metadata."""
        if self.file_identifier is None:
            msg = "Records require a file_identifier."
            raise TypeError(msg)

        self._set_metadata_constraints()
        self._set_contacts()
        self._set_cat_identifier()
        self._set_citation()
        self._set_admin()
        self._set_profiles()

        super().__post_init__()

    def _set_metadata_constraints(self) -> None:
        """
        Set conventional metadata constraints.

        Restricted metadata is not yet supported.
        """
        self.metadata.constraints = Constraints([OPEN_ACCESS, CC_BY_ND_V4])

    def _set_contacts(self) -> None:
        """
        Set conventional contacts.

        MAGIC as a point of contact and publisher; UKRI as a rights holder
        """
        magic = make_magic_role({ContactRoleCode.POINT_OF_CONTACT, ContactRoleCode.PUBLISHER})
        self.identification.contacts.ensure(magic)
        self.identification.contacts.ensure(UKRI_RIGHTS_HOLDER)

    def _set_cat_identifier(self) -> None:
        """Set an identifier within the Data Catalogue namespace based on the file identifier."""
        self_identifier = make_bas_cat(self.file_identifier)  # ty:ignore[invalid-argument-type]
        self.identification.identifiers.ensure(self_identifier)

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

    def _set_admin(self) -> None:
        """Set administration metadata if provided."""
        if isinstance(self._admin_keys, AdministrationKeys) and isinstance(self._admin_meta, AdministrationMetadata):
            set_admin(keys=self._admin_keys, record=self, admin_meta=self._admin_meta)
            self._profiles.append(MAGIC_ADMINISTRATION_V1)

    def _set_profiles(self) -> None:
        """Set domain consistency elements for any applicable profiles."""
        for profile in self._profiles:
            self.data_quality.domain_consistency.ensure(profile)

    @classmethod
    def loads(
        cls,
        value: dict,
        check_supported: bool = False,
        logger: logging.Logger | None = None,
        admin_keys: AdministrationKeys | None = None,
        **kwargs: Any,
    ) -> "RecordMagic":
        """
        Create a Record from a dict loaded from a JSON schema instance.

        Known to violate method override rules due to differing signature.
        """
        record = super().loads(value=value, check_supported=check_supported, logger=logger, **kwargs)
        admin_meta = get_admin(keys=admin_keys, record=record) if admin_keys else None
        return RecordMagic(
            file_identifier=record.file_identifier,
            hierarchy_level=record.hierarchy_level,
            metadata=record.metadata,
            reference_system_info=record.reference_system_info,
            identification=record.identification,
            data_quality=record.data_quality,
            distribution=record.distribution,
            admin_keys=admin_keys,
            admin_meta=admin_meta,
        )


class RecordMagicOpen(RecordMagic):
    """
    Create an unrestricted (open) Record based on MAGIC metadata profiles and other conventional values.

    Extends RecordMagic to:
    - set metadata and resource access constraints and administration metadata permissions to open access
    - set a metadata usage constraint for the CC BY ND v4 licence
    - set a resource usage constraint for the OGL v3.0 licence

    Note: Any constraints and admin metadata permissions passed to this class will be overwritten.
    """

    @staticmethod
    def _set_open_access(admin_keys: AdministrationKeys | None, record: Record) -> None:
        """
        Set open access constraints and permissions.

        Overrides any existing constraints and permissions.
        """
        if not isinstance(admin_keys, AdministrationKeys):
            msg = "Open records require administration metadata keys."
            raise TypeError(msg)

        record.metadata.constraints = Constraints([OPEN_ACCESS, CC_BY_ND_V4])
        record.identification.constraints = Constraints([OPEN_ACCESS, OGL_V3])

        admin_meta = get_admin(keys=admin_keys, record=record)
        if not admin_meta:
            admin_meta = AdministrationMetadata(id=record.file_identifier)  # ty:ignore[invalid-argument-type]
            record.data_quality.domain_consistency.append(MAGIC_ADMINISTRATION_V1)

        admin_meta.metadata_permissions = [OPEN_ACCESS_PERMISSION]
        admin_meta.resource_permissions = [OPEN_ACCESS_PERMISSION]
        set_admin(keys=admin_keys, record=record, admin_meta=admin_meta)

    def __post_init__(self) -> None:
        """Set constraints and permissions."""
        super().__post_init__()
        self._set_open_access(admin_keys=self._admin_keys, record=self)

    @classmethod
    def loads(
        cls,
        value: dict,
        check_supported: bool = False,
        logger: logging.Logger | None = None,
        admin_keys: AdministrationKeys | None = None,
        **kwargs: Any,
    ) -> "RecordMagicOpen":
        """Create an unrestricted Record from a dict loaded from a JSON schema instance."""
        record = super().loads(
            value=value, check_supported=check_supported, logger=logger, admin_keys=admin_keys, **kwargs
        )
        return RecordMagicOpen(
            file_identifier=record.file_identifier,
            hierarchy_level=record.hierarchy_level,
            metadata=record.metadata,
            reference_system_info=record.reference_system_info,
            identification=record.identification,
            data_quality=record.data_quality,
            distribution=record.distribution,
            admin_keys=admin_keys,
        )
