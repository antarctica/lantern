import json
import logging
import random
from datetime import UTC, date, datetime
from pathlib import Path

from bas_metadata_library.standards.magic_administration.v1 import AdministrationMetadata, Permission
from bas_metadata_library.standards.magic_administration.v1.utils import AdministrationKeys
from tasks._config import ExtraConfig
from tasks._record_utils import append_role_to_contact, dump_records, init
from tasks.keys_check import decode as jwe_decode

from lantern.lib.metadata_library.models.record.elements.common import Address, Contact, ContactIdentity, OnlineResource
from lantern.lib.metadata_library.models.record.elements.data_quality import DomainConsistency
from lantern.lib.metadata_library.models.record.enums import (
    ConstraintTypeCode,
    ContactRoleCode,
    HierarchyLevelCode,
    OnlineResourceFunctionCode,
)
from lantern.lib.metadata_library.models.record.presets.admin import OPEN_ACCESS as OPEN_ACCESS_PERMISSION
from lantern.lib.metadata_library.models.record.presets.conformance import MAGIC_ADMINISTRATION_V1, MAGIC_DISCOVERY_V2
from lantern.lib.metadata_library.models.record.presets.constraints import CC_BY_ND_V4, OPEN_ACCESS
from lantern.lib.metadata_library.models.record.presets.contacts import ESRI_DISTRIBUTOR, UKRI_RIGHTS_HOLDER
from lantern.lib.metadata_library.models.record.record import Record, RecordInvalidError
from lantern.lib.metadata_library.models.record.utils.admin import set_admin
from lantern.lib.metadata_library.models.record.utils.kv import get_kv, set_kv
from lantern.models.item.catalogue.const import CONTAINER_SUPER_TYPES
from lantern.models.record.record import Record as CatRecord
from lantern.models.record.revision import RecordRevision as CatRecordRevision
from lantern.stores.gitlab import GitLabStore
from lantern.utils import get_jinja_env

NORA_DISTRIBUTOR = Contact(
    organisation=ContactIdentity(name="NERC Open Research Archive", href="https://ror.org/02b5d8509", title="ror"),
    email="nora.nerc@bgs.ac.uk",
    online_resource=OnlineResource(
        href="https://nora.nerc.ac.uk/information.html",
        title="About this repository - NERC Open Research Archive",
        description="General information about the NERC Open Research Archive (NORA) from the NORA website.",
        function=OnlineResourceFunctionCode.INFORMATION,
    ),
    role={ContactRoleCode.DISTRIBUTOR},
)

MICROSOFT_DISTRIBUTOR = Contact(
    organisation=ContactIdentity(name="Microsoft Corporation", href="https://ror.org/00d0nc645", title="ror"),
    address=Address(
        delivery_point="1 Microsoft Way, Bldg 37",
        city="Redmond",
        administrative_area="Washington",
        postal_code="98052",
        country="United States of America",
    ),
    online_resource=OnlineResource(
        href="https://www.microsoft.com",
        title="Microsoft - AI, Cloud, Productivity, Computing, Gaming & Apps",
        description="Corporate website for Microsoft.",
        function=OnlineResourceFunctionCode.INFORMATION,
    ),
    role={ContactRoleCode.DISTRIBUTOR},
)


class RecordUpgrade:
    """Wrapper around record as part of an upgrade."""

    def __init__(self, record: Record, original_sha1: str) -> None:
        """Initialise."""
        self.record = record
        self.changes: list[str] = []
        self._original_sha1 = original_sha1
        self._fid = self.record.file_identifier

    @property
    def _container_super_type(self) -> bool:
        """Whether record is a container super type."""
        return self.record.hierarchy_level in CONTAINER_SUPER_TYPES

    @staticmethod
    def _load_draft_v1_admin_meta(keys: AdministrationKeys, value: str) -> dict:
        clear = json.loads(
            jwe_decode(keys=keys, ciphertext=value, issuer="magic.data.bas.ac.uk", audience="data.bas.ac.uk")
        )
        if (
            clear["$schema"]
            != "https://metadata-resources.data.bas.ac.uk/bas-metadata-generator-configuration-schemas/v2/magic-admin-v1.json"
        ):
            msg = "Bad schema."
            raise ValueError(msg) from None
        return clear

    @staticmethod
    def _map_draft_v1_admin_meta_permissions(draft_permission: dict) -> Permission:
        if draft_permission["directory"] == "*" and draft_permission["group"] == "~public":
            return OPEN_ACCESS_PERMISSION
        if (draft_permission["directory"] == "~bas-ldap" and draft_permission["group"] == "apps_magic_ods_read") or (
            draft_permission["directory"] == "~nerc" and draft_permission["group"] == "~bas-staff"
        ):
            return Permission(
                directory=draft_permission["directory"],
                group=draft_permission["group"],
                comment=draft_permission.get("comments"),
            )
        print(draft_permission)
        msg = "Permission not mapped, aborting as a precaution."
        raise NotImplementedError(msg) from None

    def _get_domain_conformance(self, href: str) -> DomainConsistency | None:
        """Get a domain conformance identified by href if it exists."""
        for dc in self.record.data_quality.domain_consistency:
            if dc.specification.href == href:
                return dc
        return None

    def _add_domain_conformance(self, conformance: DomainConsistency) -> None:
        """Add a domain conformance identified by href if needed."""
        for dc in self.record.data_quality.domain_consistency:
            if dc.specification.href == conformance.specification.href:
                return
        self.record.data_quality.domain_consistency.append(conformance)

    def _remove_domain_conformance(self, href: str) -> None:
        """Filter out a domain conformance identified by href if it exists."""
        self.record.data_quality.domain_consistency = [
            dc for dc in self.record.data_quality.domain_consistency if dc.specification.href != href
        ]

    def _upgrade_admin(self, logger: logging.Logger, keys: AdministrationKeys) -> None:
        """Upgrade administration metadata to final v1 profile."""
        draft_key = "administrative_metadata"
        kv = get_kv(record=self.record)
        if draft_key not in kv:
            logger.debug(f"[{self._fid}] admin meta: draft not found - skipping.")
            return

        logger.debug(f"[{self.record.file_identifier}] admin meta: draft found.")
        draft_data = self._load_draft_v1_admin_meta(keys=keys, value=kv["administrative_metadata"])
        admin = AdministrationMetadata(id=self._fid)  # ty:ignore[invalid-argument-type]
        admin.gitlab_issues = draft_data["gitlab_issues"]
        admin.metadata_permissions = [OPEN_ACCESS_PERMISSION]
        admin.resource_permissions = [
            self._map_draft_v1_admin_meta_permissions(p) for p in draft_data["access_permissions"]
        ]
        del kv[draft_key]
        set_kv(kv=kv, record=self.record, replace=True)
        kv_updated = get_kv(record=self.record)
        if draft_key in kv_updated:
            msg = "Failed to remove draft admin metadata."
            raise RuntimeError(msg)

        set_admin(keys=keys, record=self.record, admin_meta=admin)
        self._add_domain_conformance(MAGIC_ADMINISTRATION_V1)
        self.changes.append("Administration metadata upgraded to V1 final content/encoding.")

    def _add_rights_holder(self) -> None:
        """Add copyright holder if needed."""
        if self.record.identification.contacts.filter(roles=ContactRoleCode.RIGHTS_HOLDER):
            return

        scar_name = "Standing Committee on Antarctic Research"
        sponsors = self.record.identification.contacts.filter(roles=ContactRoleCode.SPONSOR)
        if len(sponsors) == 1 and sponsors[0].organisation and sponsors[0].organisation.name == scar_name:
            append_role_to_contact(record=self.record, name=scar_name, role=ContactRoleCode.RIGHTS_HOLDER)
            self.changes.append("Added rights holder role to SCAR contact.")
            return
        self.record.identification.contacts.append(UKRI_RIGHTS_HOLDER)
        self.changes.append("Added UKRI contact as rights holder.")

    def _add_metadata_constraints(self) -> None:
        """Add unrestricted access and/or CC-BY-ND usage if missing."""
        if not self.record.metadata.constraints.filter(types=ConstraintTypeCode.ACCESS):
            self.record.metadata.constraints.append(OPEN_ACCESS)
            self.changes.append("Added open access metadata access constraint.")
        if not self.record.metadata.constraints.filter(types=ConstraintTypeCode.USAGE):
            self.record.metadata.constraints.append(CC_BY_ND_V4)
            self.changes.append("Added CC BY ND licence metadata usage constraint.")

    def _pre_upgrade_discovery(self, logger: logging.Logger) -> None:
        """A limited subset of records were upgraded to V2 too early and need fixing."""
        file_identifiers = [
            "d0d91e22-18c1-4c7f-8dfc-20e94cd2c107",
            "e5d4c722-a8c1-49a9-a4dd-1fd1868e5083",
            "9bb64d68-3f89-4832-bf52-ec28f30b0d83",
            "1680a763-02b0-4718-802c-bf6f89744f4e",
            "03db9faa-da9a-4d39-8381-12b218750089",
            "a4560740-70bb-4a2a-8ba5-ff4cc1774178",
        ]
        if self.record.file_identifier not in file_identifiers:
            logger.debug(f"[{self.record.file_identifier}] fix discovery v2: not applicable - skipping.")
            return
        logger.debug(f"[{self.record.file_identifier}] fix discovery v2: fixing early v2 conformance.")
        self._remove_domain_conformance(href=MAGIC_DISCOVERY_V2.specification.href)  # ty:ignore[invalid-argument-type]

    def _fix_dates(self) -> None:
        """Fix mising publication and released dates required by discovery profile v2."""
        dates = self.record.identification.dates
        date = dates.released or dates.publication or dates.creation
        if not dates.publication:
            dates.publication = date
            self.changes.append("Missing publication date added based on creation date.")
        if not dates.released:
            dates.released = date
            self.changes.append("Missing released date added based on creation date.")

    def _upgrade_discovery(self, logger: logging.Logger) -> None:
        """Upgrade to discovery profile v2."""
        if self._get_domain_conformance(href=MAGIC_DISCOVERY_V2.specification.href):  # ty:ignore[invalid-argument-type]
            logger.debug(f"[{self.record.file_identifier}] discovery v2: already conforms - skipping.")
            return

        self._add_metadata_constraints()
        self._fix_dates()
        self._add_rights_holder()
        for href in [
            "https://metadata-standards.data.bas.ac.uk/profiles/magic-discovery-v1/",
            "https://metadata-standards.data.bas.ac.uk/profiles/magic-discovery/v1/",
        ]:
            self._remove_domain_conformance(href)
        self._add_domain_conformance(MAGIC_DISCOVERY_V2)
        self.changes.append("Discovery metadata upgraded to V2.")

    def _change_product_type(self, logger: logging.Logger) -> None:
        if self.record.hierarchy_level != HierarchyLevelCode.PRODUCT:
            logger.debug(f"[{self.record.file_identifier}] product type: not a product - skipping.")
            return
        product_type_intro = date(2026, 2, 24)
        dates = self.record.identification.dates
        date_ = dates.revision if dates.revision else dates.creation
        if date_.date > product_type_intro:  # ty:ignore[possibly-missing-attribute]
            # record updated since product types were refactored so value is assumed to be accurate
            logger.debug(f"[{self.record.file_identifier}] product type: set after introduction - skipping.")
            return
        self.record.hierarchy_level = HierarchyLevelCode.MAP_PRODUCT
        self.changes.append("Hierarchy level changed to mapProduct.")

    def _fix_shp_description(self, logger: logging.Logger) -> None:
        """Fix wording of description for shapefile distribution options if needed."""
        if not self.record.distribution:
            logger.debug(f"[{self.record.file_identifier}] shp description: no distributions - skipping.")
            return
        found = False
        for do in self.record.distribution:
            if (
                do.transfer_option.online_resource.description
                == "Download information as an Esri Shapefile (compressed as a Zip file)."
            ):
                found = True
                do.transfer_option.online_resource.description = (
                    "Download information as an Esri Shapefile, compressed as a Zip archive."
                )
        if found:
            self.changes.append("Updated shapefile distribution description wording.")

    def _fix_personal_contacts(self, logger: logging.Logger) -> None:
        """Remove known personal emails from contacts if needed."""
        emails = [
            "eleeld@bas.ac.uk",
            "adrian.hughes@bas.ac.uk",
            "lauger@bas.ac.uk",
            "Tom.Hughes@bas.ac.uk",
            "felnne@bas.ac.uk",
        ]  # DO NOT COMMIT
        flag = False
        for contact in self.record.identification.contacts:
            if contact.email in emails:
                flag = True
                contact.email = None
                self.changes.append("Removed personal email from contact.")
        if not flag:
            logger.debug(f"[{self.record.file_identifier}] personal contacts: none found - skipping.")

    def _update_distributors(self, logger: logging.Logger) -> None:
        """Update distributor for externally hosted data if needed."""
        if not self.record.distribution:
            logger.debug(f"[{self.record.file_identifier}] distributors: no distributions - skipping.")
            return

        mapping = {
            "arcgis.com": ESRI_DISTRIBUTOR,
            "nora.nerc.ac.uk": NORA_DISTRIBUTOR,
            "sharepoint.com": MICROSOFT_DISTRIBUTOR,
        }
        flag = False
        for do in self.record.distribution:
            href = do.transfer_option.online_resource.href
            matched_domain = next((d for d in mapping if d in href), None)
            if next((d for d in mapping if d in href), None):  # if any mapping key in href
                do.distributor = mapping[matched_domain]
                self.changes.append(f"Distributor for '{matched_domain}' updated.")
                flag = True

        if not flag:
            logger.debug(
                f"[{self.record.file_identifier}] distributors: no application distribution options - skipping."
            )

    def _order_profiles(self, logger: logging.Logger) -> None:
        """Order profile domain consistency elements by opinionated list to prevent false positives in diffs."""
        href_order = [MAGIC_DISCOVERY_V2.specification.href, MAGIC_ADMINISTRATION_V1.specification.href]
        hrefs = [dc.specification.href for dc in self.record.data_quality.domain_consistency]
        if set(href_order) != set(hrefs):
            logger.debug(f"[{self.record.file_identifier}] profiles order: no or not applicable profiles - skipping.")
            return
        self.record.data_quality.domain_consistency = [MAGIC_DISCOVERY_V2, MAGIC_ADMINISTRATION_V1]

    def _fix_scar(self, logger: logging.Logger) -> None:
        """Fix misspelt SCAR organisation name if needed."""
        contacts = self.record.identification.contacts
        flag = False
        for contact in contacts:
            if contact.organisation and contact.organisation.name == "Standing Committee on Antarctic Research":
                contact.organisation.name = "Scientific Committee on Antarctic Research"
                flag = True
        if flag:
            self.changes.append("Corrected misspelling of SCAR organisation name.")
            return
        logger.debug(f"[{self.record.file_identifier}] SCAR fix: no SCAR contact found - skipping.")

    def _esri_info(self, logger: logging.Logger) -> None:
        """Change transfer option function for any Esri layers (not services)."""
        if not self.record.distribution:
            logger.debug(f"[{self.record.file_identifier}] esri layers: no distributions - skipping.")
            return

        formats = [
            "https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+layer+feature",
            "https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+layer+feature+ogc",
            "https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+layer+tile+raster",
            "https://metadata-resources.data.bas.ac.uk/media-types/x-service/arcgis+layer+tile+vector",
        ]
        flag = False
        for do in self.record.distribution:
            if do.format and do.format.href in formats:
                do.transfer_option.online_resource.function = OnlineResourceFunctionCode.INFORMATION
                self.changes.append(f"Function code for '{do.format.href}' updated.")
                flag = True

        if not flag:
            logger.debug(
                f"[{self.record.file_identifier}] esri layers: no application distribution options - skipping."
            )

    def _revise(self, logger: logging.Logger) -> None:
        """Update date stamp in record if needed."""
        if self.record.sha1 == self._original_sha1:
            logger.debug(f"[{self.record.file_identifier}] revision: record not changed - skipping.")
            return

        now = datetime.now(tz=UTC)
        self.record.metadata.date_stamp = datetime.now(tz=UTC).date()
        if self._container_super_type:
            self.record.identification.dates.revision.date = now  # ty:ignore[invalid-assignment]
        logger.debug(f"[{self.record.file_identifier}] revision: record changed - revised.")

    def upgrade(self, logger: logging.Logger, keys: AdministrationKeys) -> None:
        """Upgrade record."""
        self._pre_upgrade_discovery(logger=logger)
        self._upgrade_discovery(logger=logger)
        self._upgrade_admin(logger=logger, keys=keys)
        self._change_product_type(logger=logger)
        self._fix_shp_description(logger=logger)
        self._fix_personal_contacts(logger=logger)
        self._update_distributors(logger=logger)
        self._order_profiles(logger=logger)
        self._fix_scar(logger=logger)
        self._esri_info(logger=logger)
        self._revise(logger=logger)

    def validate(self) -> None:
        """Validate record against standard, any declared profiles and data catalogue specific requirements."""
        cat_record = CatRecord.loads(self.record.dumps(strip_admin=False))
        cat_record.validate()


class RecordsReport:
    """Report on changes made to a set of record."""

    def __init__(self, logger: logging.Logger, records: list[RecordUpgrade]) -> None:
        """Initialise."""
        self._logger = logger
        self._records = records

    @property
    def _data(self) -> dict[str, dict]:
        """Changes for record as a dict indexed by record file identifier."""
        return {
            c.record.file_identifier: {
                "id": c.record.file_identifier,
                "type": c.record.hierarchy_level.name,
                "title": c.record.identification.title,
                "edition": c.record.identification.edition,
                "changes": c.changes,
            }
            for c in self._records
        }  # ty:ignore[invalid-return-type]

    @property
    def _context(self) -> dict[str, str | dict]:
        """Data for Jinja template."""
        return {
            "timestamp": datetime.now(tz=UTC).replace(microsecond=0).isoformat(),
            "count": str(len(self._data)),
            "changed_count": str(sum(1 for r in self._records if r.changes)),
            "items": self._data,
        }

    @property
    def _template(self) -> str:
        """Jinja template."""
        return """
# Records upgrade report

Run at: {{ timestamp }}

Records: {{ count }} (of which {{ changed_count }} were changed)

{% for file_identifier, data in items.items() %}
## {{ data.title }} (Ed: {{ data.edition }})

({{ file_identifier }} / {{ data.type }})

{% for change in data.changes %}
- {{ change }}
{% endfor %}
{% endfor %}
        """

    def _render(self) -> str:
        """Render jinja template."""
        jinja = get_jinja_env()
        return jinja.from_string(self._template).render(**self._context)

    def dump_data(self, path: Path) -> None:
        """Dump report data to path."""
        with path.open("w") as f:
            json.dump(self._data, f, indent=2)

    def dump_rendered(self, path: Path) -> None:
        """Dump rendered report to path."""
        with path.open("w") as f:
            f.write(self._render())


class RecordsIO:
    """Manages a set of records as underlying files."""

    def __init__(self, logger: logging.Logger, store: GitLabStore, base_path: Path) -> None:
        """Initialise."""
        self._logger = logger
        self._store = store
        self._base = base_path
        self.records: list[RecordUpgrade] = []

    @staticmethod
    def _write_hashes(records: list[Record | CatRecordRevision], path: Path) -> None:
        data = {record.file_identifier: record.sha1 for record in records}
        with path.open("w") as f:
            json.dump(data, f, indent=2)

    @property
    def initialised(self) -> bool:
        """Check if local records set exists."""
        return self._base.exists()

    def prep(self) -> None:
        """Dump all records from store."""
        self._base.mkdir(parents=True, exist_ok=True)
        records_path = self._base / "records"
        hashes_path = self._base / "hashes_original.json"

        records = self._store.select()
        dump_records(logger=self._logger, output_path=records_path, records=records)
        self._logger.info(f"{len(records)} records dumped to {self._base.resolve()}.")

        self._write_hashes(records=records, path=hashes_path)  # ty:ignore[invalid-argument-type]
        self._logger.info(f"Original record hashes dumped to {hashes_path.resolve()}.")

    def dump(self) -> None:
        """Dump records to path."""
        records_ = [r.record for r in self.records]
        records_path = self._base / "records"
        dump_records(logger=self._logger, output_path=records_path, records=records_)
        self._logger.info(f"{len(self.records)} records dumped to {self._base.resolve()}.")

        hashes_path = self._base / "hashes_working.json"
        self._write_hashes(records=records_, path=hashes_path)
        self._logger.info(f"Working record hashes dumped to {hashes_path.resolve()}.")

    def load(self, random_subset: int = 0) -> None:
        """Load (some) records from path."""
        originals_path = self._base / "hashes_original.json"
        with originals_path.open("r") as f:
            original_hashes = json.load(f)

        record_paths = list(self._base.glob("records/*.json"))
        self._logger.info(f"{len(record_paths)} records in {self._base.resolve()}.")

        subset_paths = record_paths
        if 0 < random_subset < len(record_paths):
            self._logger.info(f"Selecting {random_subset} random records as a subset.")
            random.seed(764)  # 764/4
            subset_paths = random.sample(record_paths, random_subset)

        self._logger.info(f"Loading {len(record_paths)} records.")
        self.records = []
        for base_path in subset_paths:
            with base_path.open("r") as f:
                record = Record.loads(json.load(f))
                self.records.append(RecordUpgrade(record=record, original_sha1=original_hashes[record.file_identifier]))

    def list(self) -> None:
        """List or summarise loaded records."""
        if len(self.records) < 20:
            self._logger.info("Loaded records:")
            for container in self.records:
                r = container.record
                self._logger.info(
                    f"* {r.file_identifier} [{r.hierarchy_level.name}] '{r.identification.title}' ({r.identification.edition})"
                )
            return
        self._logger.info(f"{len(self.records)} records.")


class NotInitialisedError(Exception):
    """Raised when local records set does yet not exist."""

    pass


# noinspection SpellCheckingInspection
class Upgradamatron:
    """Upgrade a set of records."""

    def __init__(self, logger: logging.Logger, config: ExtraConfig, store: GitLabStore, path: Path) -> None:
        """Initialise."""
        self._logger = logger
        self._config = config
        self._store = store
        self._base = path

        self._io = RecordsIO(logger=self._logger, store=self._store, base_path=self._base)

    def init(self, random_subset: int = 0) -> None:
        """Initialise local records set."""
        if not self._io.initialised:
            self._io.prep()
            self._logger.info("Init local git repo and commit all records to track changes. Then rerun this task.")
            raise NotInitialisedError() from None
        self._io.load(random_subset=random_subset)

    def list(self) -> None:
        """List or summarise loaded records."""
        self._io.list()

    def run(self) -> None:
        """Upgrade and validate records."""
        for container in self._io.records:
            container.upgrade(logger=self._logger, keys=self._config.ADMIN_METADATA_KEYS_RW)
            self._logger.debug(f"[{container.record.file_identifier}] validating")
            try:
                container.validate()
            except RecordInvalidError:
                self._logger.exception(f"[{container.record.file_identifier}] record invalid")

    def dump(self) -> None:
        """Dump records and reports to tracking repo path."""
        self._io.dump()
        report_data_path = self._base / "report_data.json"
        report_rendered_path = self._base / "report_rendered.md"
        reporter = RecordsReport(logger=self._logger, records=self._io.records)
        reporter.dump_data(path=report_data_path)
        reporter.dump_rendered(path=report_rendered_path)
        self._logger.info(f"Report data dumped to {report_data_path.resolve()}.")
        self._logger.info(f"Report rendered dumped to {report_rendered_path.resolve()}.")


def main() -> None:
    """Entrypoint."""
    path = Path("upgrade")
    subset = 0
    logger, config, store, _s3 = init()
    logger.info("Records upgrade script: 2026-02 (0.4.x -> 0.5.0)")

    upgrade = Upgradamatron(logger=logger, config=config, store=store, path=path)
    try:
        upgrade.init(random_subset=subset)
    except NotInitialisedError:
        return
    upgrade.list()
    upgrade.run()
    upgrade.dump()

    logger.info("Upgrade complete.")


if __name__ == "__main__":
    main()
